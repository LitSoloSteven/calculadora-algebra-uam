import secrets
import threading
import time
from dataclasses import dataclass

from nicegui import ui

from src.frontend.constantes import MAX_ENTRADAS_HANDOFF, TTL_HANDOFF_SEGUNDOS
from src.frontend.navigation import tool_by_id
from src.frontend.textos import MSJ_HANDOFF_DATOS_INVALIDOS
from src.backend.utils.validators import MatrixValidator


TTL_SECONDS = TTL_HANDOFF_SEGUNDOS
_MAX_ENTRIES = MAX_ENTRADAS_HANDOFF
_STORE: dict[str, tuple[float, dict]] = {}
_LOCK = threading.Lock()


def _now() -> float:
    return time.monotonic()


def _store_put(kind: str, source: str, data, **extra) -> str:
    token = secrets.token_urlsafe(16)
    payload = {"v": 1, "kind": kind, "source": source, "data": data, **extra}
    with _LOCK:
        now = _now()
        expired = [k for k, (ts, _) in _STORE.items() if now - ts > TTL_SECONDS]
        for k in expired:
            del _STORE[k]
        if len(_STORE) >= _MAX_ENTRIES:
            oldest = min(_STORE.keys(), key=lambda k: _STORE[k][0])
            del _STORE[oldest]
        _STORE[token] = (now, payload)
    return token


def put_matrix(source_id: str, data: list[list[str]]) -> str:
    return _store_put("matrix_A", source_id, data)


def handoff_url(route: str, token: str) -> str:
    return f"{route}?handoff={token}"


def validate_matrix_payload(payload, *, max_n: int) -> tuple[list[list[str]] | None, str | None]:
    if not isinstance(payload, dict):
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    if payload.get("v") != 1 or payload.get("kind") != "matrix_A" or not isinstance(payload.get("source"), str):
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    
    n = len(data)
    for row in data:
        if not isinstance(row, list) or len(row) != n:
            return None, MSJ_HANDOFF_DATOS_INVALIDOS
            
    if n > max_n:
        return None, f"La matriz es de {n}×{n} y esta herramienta admite hasta {max_n}×{max_n}. Empezamos con la herramienta vacía."
        
    for row in data:
        for cell in row:
            if not isinstance(cell, str) or not (1 <= len(cell) <= 64):
                return None, MSJ_HANDOFF_DATOS_INVALIDOS
            ok, _, _ = MatrixValidator.parse_number_exact(cell)
            if not ok:
                return None, MSJ_HANDOFF_DATOS_INVALIDOS
                
    return data, None


@dataclass(frozen=True)
class HandoffResult:
    status: str
    data: list[list[str]] | dict | None
    source_name: str
    message: str


def consume_matrix(token: str, *, max_n: int) -> HandoffResult | None:
    if not token:
        return None
        
    with _LOCK:
        entry = _STORE.pop(token, None)
        
    if entry is None:
        return HandoffResult(
            status='missing',
            data=None,
            source_name='',
            message="No encontramos los datos que ibas a traer. Ya los usaste o el enlace es antiguo. Puedes capturar la matriz aquí."
        )
        
    ts, payload = entry
    if _now() - ts > TTL_SECONDS:
        return HandoffResult(
            status='expired',
            data=None,
            source_name='',
            message="Los datos tardaron demasiado en llegar y expiraron. Vuelve a la herramienta de origen y repite la acción."
        )
        
    try:
        source_name = tool_by_id(payload["source"]).name
    except KeyError:
        source_name = "otra herramienta"
        
    data, error_msg = validate_matrix_payload(payload, max_n=max_n)
    if error_msg is not None:
        return HandoffResult(
            status='invalid',
            data=None,
            source_name=source_name,
            message=error_msg
        )
        
    return HandoffResult(
        status='ok',
        data=data,
        source_name=source_name,
        message=""
    )


def render_handoff_notice(result: HandoffResult, success_message: str) -> None:
    if result.status == 'ok':
        with ui.row().classes('handoff-note').props('role=status'):
            ui.icon('check_circle').classes('text-accent')
            ui.label(success_message)
    else:
        with ui.row().classes('items-center gap-2 px-4 py-2 badge-warning w-fit').props('role=status'):
            ui.icon('warning_amber')
            ui.label(result.message)


def clean_handoff_url() -> None:
    ui.timer(0.2, lambda: ui.run_javascript("(()=>{const u=new URL(location.href);u.searchParams.delete('handoff');history.replaceState(null,'',u.pathname+u.search+u.hash);})()"), once=True)


def put_system(source_id: str, A: list[list[str]], b: list[str]) -> str:
    return _store_put("system", source_id, {"matrix_A": A, "vector_b": b})


def put_vectors(source_id: str, scene: str, data: list[list[str]]) -> str:
    return _store_put("vectors", source_id, data, scene=scene)


def _validate_cell(cell: str) -> bool:
    if not isinstance(cell, str) or not (1 <= len(cell) <= 64):
        return False
    ok, _, _ = MatrixValidator.parse_number_exact(cell)
    return ok


def validate_system_payload(payload, *, max_m: int, allowed_n: set[int]) -> tuple[dict | None, str | None]:
    if not isinstance(payload, dict) or payload.get("v") != 1 or payload.get("kind") != "system":
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    data = payload.get("data")
    if not isinstance(data, dict):
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    
    A = data.get("matrix_A")
    b = data.get("vector_b")
    if not isinstance(A, list) or not isinstance(b, list):
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    
    m = len(A)
    if m == 0 or m > max_m or len(b) != m:
        return None, f"El sistema debe tener entre 1 y {max_m} ecuaciones. Empezamos con la herramienta vacía."
    
    n = len(A[0])
    if n not in allowed_n:
        return None, f"El sistema tiene {n} variables. Esta herramienta solo grafica sistemas con {', o '.join(map(str, sorted(allowed_n)))} variables. Empezamos con la herramienta vacía."
    
    for i, row in enumerate(A):
        if not isinstance(row, list) or len(row) != n:
            return None, MSJ_HANDOFF_DATOS_INVALIDOS
        for cell in row:
            if not _validate_cell(cell):
                return None, MSJ_HANDOFF_DATOS_INVALIDOS
        if not _validate_cell(b[i]):
            return None, MSJ_HANDOFF_DATOS_INVALIDOS
            
    return data, None


def validate_vectors_payload(payload, *, allowed_n: set[int]) -> tuple[dict | None, str | None]:
    if not isinstance(payload, dict) or payload.get("v") != 1 or payload.get("kind") != "vectors":
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    data = payload.get("data")
    scene = payload.get("scene", "vectores")
    if not isinstance(data, list) or not data:
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    
    n = len(data[0])
    if n not in allowed_n:
        return None, f"Los vectores tienen dimensión {n}. Esta herramienta solo grafica en {', o '.join(map(str, sorted(allowed_n)))}D. Empezamos con la herramienta vacía."
    
    for vec in data:
        if not isinstance(vec, list) or len(vec) != n:
            return None, MSJ_HANDOFF_DATOS_INVALIDOS
        for cell in vec:
            if not _validate_cell(cell):
                return None, MSJ_HANDOFF_DATOS_INVALIDOS
                
    return {"scene": scene, "data": data}, None


def consume_system(token: str, *, max_m: int, allowed_n: set[int]) -> HandoffResult | None:
    if not token:
        return None
        
    with _LOCK:
        entry = _STORE.pop(token, None)
        
    if entry is None:
        return HandoffResult(status='missing', data=None, source_name='', message="No encontramos los datos que ibas a traer. Ya los usaste o el enlace es antiguo. Puedes capturarlos aquí.")
        
    ts, payload = entry
    if _now() - ts > TTL_SECONDS:
        return HandoffResult(status='expired', data=None, source_name='', message="Los datos tardaron demasiado en llegar y expiraron. Vuelve a la herramienta de origen y repite la acción.")
        
    try:
        source_name = tool_by_id(payload["source"]).name
    except KeyError:
        source_name = "otra herramienta"
        
    data, error_msg = validate_system_payload(payload, max_m=max_m, allowed_n=allowed_n)
    if error_msg is not None:
        return HandoffResult(status='invalid', data=None, source_name=source_name, message=error_msg)
        
    return HandoffResult(status='ok', data=data, source_name=source_name, message="")


def consume_vectors(token: str, *, allowed_n: set[int]) -> HandoffResult | None:
    if not token:
        return None
        
    with _LOCK:
        entry = _STORE.pop(token, None)
        
    if entry is None:
        return HandoffResult(status='missing', data=None, source_name='', message="No encontramos los datos que ibas a traer. Ya los usaste o el enlace es antiguo. Puedes capturarlos aquí.")
        
    ts, payload = entry
    if _now() - ts > TTL_SECONDS:
        return HandoffResult(status='expired', data=None, source_name='', message="Los datos tardaron demasiado en llegar y expiraron. Vuelve a la herramienta de origen y repite la acción.")
        
    try:
        source_name = tool_by_id(payload["source"]).name
    except KeyError:
        source_name = "otra herramienta"
        
    data, error_msg = validate_vectors_payload(payload, allowed_n=allowed_n)
    if error_msg is not None:
        return HandoffResult(status='invalid', data=None, source_name=source_name, message=error_msg)
        
    return HandoffResult(status='ok', data=data, source_name=source_name, message="")
