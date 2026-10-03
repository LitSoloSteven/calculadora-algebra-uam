import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Protocol, Sequence, Tuple

MAX_CONTEXT_CHARS = 4000
FULL_MATRIX_MAX = 8
WINDOW = 6
NUMBER_MAX_LEN = 14

@dataclass(frozen=True)
class StepRef:
    index: int
    total: int
    kind: str
    op: str
    rows_before: Dict[str, List[str]]
    rows_after: Dict[str, List[str]]
    cols: Tuple[int, int] | None = None
    detail: Dict[str, Any] | None = None

@dataclass
class AIContext:
    tool: str
    view: str
    label: str
    input: Dict[str, Any]
    result: Dict[str, Any] | None = None
    focus: StepRef | None = None
    window_note: str | None = None
    stale: bool = False
    empty: bool = False

class AIContextProvider(Protocol):
    def get_ai_context(self) -> AIContext | None: ...

def clip_text(s: str, max_len: int) -> str:
    s = str(s)
    if len(s) <= max_len:
        return s
    return s[:max_len - 1] + "…"

def sanitize_user_string(s: str, limit: int) -> str:
    s = str(s)
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
    s = re.sub(r'(?i)\[/?CONTEXTO\]', '', s)
    return clip_text(s, limit)

def compact_number(s: str, max_len: int = NUMBER_MAX_LEN) -> str:
    s = str(s).strip()
    if len(s) <= max_len:
        return s

    if "/" in s:
        try:
            num, den = s.split("/")
            val = float(num) / float(den)
            aprox = f"≈{val:.1f}"
            if len(aprox) <= max_len:
                return aprox
        except Exception:
            pass

    return clip_text(s, max_len)

def describe_matrix(rows: Sequence[Sequence[Any]], *, full_max=FULL_MATRIX_MAX, window=WINDOW) -> dict:
    n_rows = len(rows)
    n_cols = len(rows[0]) if n_rows > 0 else 0
    
    if n_rows <= full_max and n_cols <= full_max:
        data = [[compact_number(c) for c in r] for r in rows]
        nonzero = sum(1 for r in rows for c in r if str(c).strip() not in ('0', '', '0.0'))
        return {"rows": n_rows, "cols": n_cols, "data": data}
        
    w_rows = min(n_rows, window)
    w_cols = min(n_cols, window)
    
    data = []
    nonzero = 0
    invalid = 0
    for i in range(n_rows):
        row_data = []
        for j in range(n_cols):
            val = str(rows[i][j]).strip()
            if val not in ('0', '', '0.0'):
                try:
                    if "/" in val:
                        float(val.split("/")[0])
                    else:
                        float(val)
                    nonzero += 1
                except Exception:
                    invalid += 1
            if i < w_rows and j < w_cols:
                row_data.append(compact_number(val))
        if i < w_rows:
            data.append(row_data)
            
    res = {"rows": n_rows, "cols": n_cols, "window": [w_rows, w_cols], "data": data, "nonzero": nonzero}
    if invalid > 0:
        res["invalid"] = invalid
    return res

def excerpt_rows(rows, row_indices, center_col, max_cols=12) -> Tuple[Dict[str, List[str]], Tuple[int, int] | None]:
    n_cols = len(rows[0]) if rows else 0
    start_col = 0
    end_col = n_cols
    cols_range = None
    
    if n_cols > max_cols:
        start_col = max(0, center_col - max_cols // 2)
        end_col = min(n_cols, start_col + max_cols)
        if end_col - start_col < max_cols:
            start_col = max(0, end_col - max_cols)
        cols_range = (start_col + 1, end_col)
        
    result = {}
    for r_idx in row_indices:
        if 0 <= r_idx < len(rows):
            row_data = rows[r_idx]
            result[str(r_idx + 1)] = [compact_number(c) for c in row_data[start_col:end_col]]
            
    return result, cols_range

def serialize_context(ctx: AIContext, *, max_chars=MAX_CONTEXT_CHARS) -> str:
    import copy
    working_ctx = copy.deepcopy(ctx)
    
    def build_dict(c: AIContext, truncated: bool) -> dict:
        d = {
            "v": 1,
            "tool": c.tool,
            "view": c.view,
            "input": c.input,
        }
        if c.result is not None:
            d["result"] = c.result
        if c.focus is not None:
            d["focus"] = {
                "index": c.focus.index,
                "total": c.focus.total,
                "kind": c.focus.kind,
                "op": c.focus.op,
                "rows_before": c.focus.rows_before,
                "rows_after": c.focus.rows_after,
            }
            if c.focus.cols:
                d["focus"]["cols"] = list(c.focus.cols)
            if c.focus.detail:
                d["focus"]["detail"] = c.focus.detail
                
        meta = {}
        if c.window_note:
            meta["window"] = c.window_note
        if c.stale:
            meta["stale"] = True
        if truncated:
            meta["truncated"] = True
            
        if meta:
            d["meta"] = meta
        return d
        
    def get_str(c: AIContext, is_truncated: bool = False) -> str:
        d = build_dict(c, is_truncated)
        res = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
        return f"[CONTEXTO]\n{res}\n[/CONTEXTO]"
        
    res_str = get_str(working_ctx)
    if len(res_str) <= max_chars:
        return res_str
        
    is_truncated = True
    
    # 1. Quitar detail del foco
    if working_ctx.focus and working_ctx.focus.detail:
        import dataclasses
        working_ctx.focus = dataclasses.replace(working_ctx.focus, detail=None)
            
    res_str = get_str(working_ctx, is_truncated)
    if len(res_str) <= max_chars: return res_str
    
    # 2. Quitar extras opcionales
    if working_ctx.result:
        for k in ["inverse", "steps", "segment_steps", "pasos"]:
            working_ctx.result.pop(k, None)
            
    res_str = get_str(working_ctx, is_truncated)
    if len(res_str) <= max_chars: return res_str
    
    # 2. Reducir ventanas de entrada
    def reduce_matrix(m_dict, target_w):
        if not isinstance(m_dict, dict) or "data" not in m_dict: return
        if "window" not in m_dict:
            m_dict["window"] = [len(m_dict["data"]), len(m_dict["data"][0])] if m_dict["data"] else [0,0]
        
        w_r, w_c = m_dict["window"]
        new_w_r, new_w_c = min(w_r, target_w), min(w_c, target_w)
        if new_w_r == 0:
            m_dict.pop("data", None)
            m_dict["window"] = [0, 0]
            return
            
        m_dict["data"] = [row[:new_w_c] for row in m_dict["data"][:new_w_r]]
        m_dict["window"] = [new_w_r, new_w_c]
        
    for step_w in [4, 3, 0]:
        if "data" in working_ctx.input: # Para matrices puras (inversa)
            reduce_matrix(working_ctx.input, step_w)
        else: # Para diccionarios de matrices (sistemas, matrix_ops, vector_ops)
            for k, v in working_ctx.input.items():
                if isinstance(v, dict) and "rows" in v and "cols" in v and "data" in v:
                    reduce_matrix(v, step_w)
                elif isinstance(v, dict) and "data" in v and "orientation" in v:
                    # Vectores
                    if len(v["data"]) > step_w:
                        v["data"] = v["data"][:step_w]
                        if "window" not in v:
                            v["window"] = [step_w, 1] if v["orientation"] == "column" else [1, step_w]
        
        res_str = get_str(working_ctx, is_truncated)
        if len(res_str) <= max_chars: return res_str

    # 3. Reducir result a status+línea
    if working_ctx.result:
        status = working_ctx.result.get("status", "")
        line = working_ctx.result.get("message") or working_ctx.result.get("clasificacion") or ""
        working_ctx.result = {"status": status}
        if line:
            working_ctx.result["message"] = line
        
        res_str = get_str(working_ctx, is_truncated)
        if len(res_str) <= max_chars: return res_str
        
    # 4. Recortar filas del foco
    if working_ctx.focus:
        for d in [working_ctx.focus.rows_before, working_ctx.focus.rows_after]:
            if len(d) > 1:
                first_key = next(iter(d.keys()))
                keys_to_remove = list(d.keys())[1:]
                for k in keys_to_remove:
                    d.pop(k)
                    
        res_str = get_str(working_ctx, is_truncated)
        if len(res_str) <= max_chars: return res_str
        
        for d in [working_ctx.focus.rows_before, working_ctx.focus.rows_after]:
            for k in d:
                d[k] = d[k][:4]
        
        working_ctx.focus.cols = None
                
    return get_str(working_ctx, is_truncated)
