"""Controller para el cálculo de la matriz inversa y estructuración de pasos didácticos.

Este controller actúa como puente entre el backend matemático (MatrixInverseSolver)
y la vista en NiceGUI.

IMPORTANTE: process_inverse devuelve un dict de Python (NO un string JSON).
Los pasos contienen referencias a objetos Matrix que la vista renderiza bajo demanda;
serializar ~2600 matrices de 50×100 en memoria como JSON sería inviable en rendimiento
y consumo de memoria.
"""
from __future__ import annotations

import json
import logging
import re
import time
from fractions import Fraction

from src.backend.constants import (
    INVERSE_LATEX_MAX_DIMENSION,
    INVERSE_MAX_DIMENSION,
)
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.formatters import matrix_to_latex
from src.backend.solvers.matrix_ops.inverse import MatrixInverseSolver
from src.backend.utils.formatters import format_fraction_str
from src.backend.utils.validators import MatrixValidator
from src.frontend.controllers.linear_systems._shared import parse_payload

logger = logging.getLogger(__name__)

from src.frontend.controllers._step_classifier import classify_step


class InverseOpsController:
    """Procesa solicitudes de inversión de matrices cuadradas."""

    @classmethod
    def process_inverse(cls, payload_json: str) -> dict:
        """Parsea el payload, valida y calcula la inversa paso a paso.

        Args:
            payload_json: String JSON con forma {"n": int, "data": list[list[str]]}.

        Returns:
            dict con el resultado estructurado para la vista (status, steps, groups,
            verifications, stats, etc.).
        """
        raw_data, err_json = parse_payload(payload_json)
        if err_json is not None:
            try:
                err_dict = json.loads(err_json)
                msg = err_dict.get("message", "Payload inválido.")
            except Exception:
                msg = "Payload JSON inválido."
            return cls._empty_result("ERROR", msg)

        # 1. Validar dimensión n
        n = raw_data.get("n")
        if not isinstance(n, int) or isinstance(n, bool) or n < 1 or n > INVERSE_MAX_DIMENSION:
            return cls._empty_result(
                "ERROR",
                f"La dimensión n debe ser un entero entre 1 y {INVERSE_MAX_DIMENSION}.",
                n=n if (isinstance(n, int) and not isinstance(n, bool)) else 0,
            )

        # 2. Validar estructura de data
        data = raw_data.get("data")
        if not isinstance(data, list) or len(data) != n:
            return cls._empty_result(
                "ERROR",
                f"Se esperaban {n} filas en la matriz.",
                n=n,
            )

        # 3. Parsear cada celda a Fraction exacto
        parsed_matrix: list[list[Fraction]] = []
        for i in range(n):
            row = data[i]
            if not isinstance(row, list) or len(row) != n:
                return cls._empty_result(
                    "ERROR",
                    f"La fila {i + 1} debe contener {n} columnas.",
                    n=n,
                )
            parsed_row: list[Fraction] = []
            for j in range(n):
                cell = row[j]
                cell_str = str(cell).strip() if cell is not None else ""
                if cell_str == "":
                    cell_str = "0"
                ok, val, err_msg = MatrixValidator.parse_number_exact(cell_str)
                if not ok:
                    return cls._empty_result(
                        "ERROR",
                        f"Error en A[{i + 1},{j + 1}]: {err_msg}",
                        n=n,
                        error_cell=[i, j],
                    )
                parsed_row.append(val)
            parsed_matrix.append(parsed_row)

        matrix_a = Matrix(n, n, parsed_matrix)

        # 4. Resolver
        t0 = time.perf_counter()
        try:
            solver = MatrixInverseSolver()
            res = solver.solve(matrix_a, build_step_latex=False)
        except ValueError as e:
            return cls._empty_result(
                "ERROR",
                str(e),
                n=n,
                elapsed_s=time.perf_counter() - t0,
                matrix_a=matrix_a,
            )
        except Exception as e:
            logger.exception("Error inesperado en MatrixInverseSolver")
            return cls._empty_result(
                "ERROR",
                f"Error al calcular la inversa: {e}",
                n=n,
                elapsed_s=time.perf_counter() - t0,
                matrix_a=matrix_a,
            )
        elapsed_s = time.perf_counter() - t0

        status = res.get("status", "ERROR")
        if status == "ERROR":
            return cls._empty_result(
                "ERROR",
                res.get("message", "Error al resolver."),
                n=n,
                elapsed_s=elapsed_s,
                matrix_a=matrix_a,
            )

        # 5. Formatear pasos, grupos y estadísticas
        raw_steps = res.get("steps", [])
        steps, groups, stats = cls._process_steps(raw_steps, n, status)

        det = res.get("determinant")
        det_str = format_fraction_str(det) if det is not None else None
        inverse = res.get("inverse")
        inverse_latex = (
            matrix_to_latex(inverse)
            if (inverse is not None and n <= INVERSE_LATEX_MAX_DIMENSION)
            else None
        )
        matrix_a_latex = (
            matrix_to_latex(matrix_a)
            if n <= INVERSE_LATEX_MAX_DIMENSION
            else None
        )

        # 6. Comprobaciones formales
        verifications = []
        if status == "SUCCESS":
            v_right = res.get("verification_step")
            if v_right:
                verifications.append({
                    "key": "right",
                    "title": "A · A⁻¹ = I",
                    "coincide": bool(v_right.get("coincide")),
                    "detail_latex": (
                        v_right.get("detail_latex")
                        if n <= INVERSE_LATEX_MAX_DIMENSION
                        else None
                    ),
                })
            v_left = res.get("verification_reverse_step")
            if v_left:
                verifications.append({
                    "key": "left",
                    "title": "A⁻¹ · A = I",
                    "coincide": bool(v_left.get("coincide")),
                    "detail_latex": (
                        v_left.get("detail_latex")
                        if n <= INVERSE_LATEX_MAX_DIMENSION
                        else None
                    ),
                })
            v_trans = res.get("transpose_property_step")
            if v_trans:
                verifications.append({
                    "key": "transpose",
                    "title": "(Aᵀ)⁻¹ = (A⁻¹)ᵀ",
                    "coincide": bool(v_trans.get("coincide")),
                    "detail_latex": (
                        v_trans.get("detail_latex")
                        if n <= INVERSE_LATEX_MAX_DIMENSION
                        else None
                    ),
                })

        return {
            "status": status,
            "message": res.get("message", ""),
            "n": n,
            "elapsed_s": round(elapsed_s, 4),
            "determinant": det,
            "determinant_str": det_str,
            "matrix_a": matrix_a,
            "matrix_a_latex": matrix_a_latex,
            "inverse": inverse,
            "inverse_latex": inverse_latex,
            "steps": steps,
            "groups": groups,
            "stats": stats,
            "verifications": verifications,
            "error_cell": None,
        }

    @classmethod
    def _empty_result(
        cls,
        status: str,
        message: str,
        *,
        n: int = 0,
        elapsed_s: float = 0.0,
        determinant: Fraction | None = None,
        matrix_a: Matrix | None = None,
        error_cell: list[int] | None = None,
    ) -> dict:
        """Construye un resultado vacío homogéneo para errores y fallos."""
        return {
            "status": status,
            "message": message,
            "n": n,
            "elapsed_s": round(elapsed_s, 4),
            "determinant": determinant,
            "determinant_str": (
                format_fraction_str(determinant) if determinant is not None else None
            ),
            "matrix_a": matrix_a,
            "matrix_a_latex": (
                matrix_to_latex(matrix_a)
                if (matrix_a is not None and n <= INVERSE_LATEX_MAX_DIMENSION)
                else None
            ),
            "inverse": None,
            "inverse_latex": None,
            "steps": [],
            "groups": [],
            "stats": {
                "total": 0,
                "pivotes": 0,
                "intercambios": 0,
                "eliminaciones": 0,
                "normalizaciones": 0,
            },
            "verifications": [],
            "error_cell": error_cell,
        }

    @classmethod
    def _process_steps(
        cls, raw_steps: list[dict], n: int, status: str
    ) -> tuple[list[dict], list[dict], dict]:
        """Clasifica los pasos de Gauss-Jordan, asigna explicaciones y los agrupa por fases."""
        steps: list[dict] = []
        raw_groups: list[dict] = []
        current_col_group: dict | None = None
        current_norm_group: dict | None = None
        current_other_group: dict | None = None

        for idx, step in enumerate(raw_steps):
            desc = step.get("description", "")
            mat = step.get("matrix")

            parsed = classify_step(desc)
            kind = parsed["kind"]
            pivot: tuple[int, int] | None = None
            rows_changed: list[int] = []
            swap_rows: tuple[int, int] | None = None
            explanation = desc

            if kind == "inicial":
                explanation = (
                    "Construimos la matriz aumentada [A | I]: A a la izquierda y la "
                    "identidad I a la derecha. Meta: aplicar operaciones elementales "
                    "de fila hasta obtener [I | A⁻¹]."
                )
                current_col_group = None
                current_norm_group = None
                current_other_group = None
                group = {
                    "kind": "inicial",
                    "title": "Matriz inicial [A | I]",
                    "step_indices": [idx],
                }
                raw_groups.append(group)
                group_idx = len(raw_groups) - 1

            elif kind == "intercambio":
                a = parsed["row1"] + 1
                b = parsed["row2"] + 1
                swap_rows = (a - 1, b - 1)
                rows_changed = [a - 1, b - 1]
                explanation = (
                    f"Intercambiamos la fila {a} con la fila {b} para que el pivote "
                    f"sea el elemento de mayor valor absoluto de la columna (pivoteo parcial). "
                    f"Intercambiar filas no altera el resultado."
                )
                current_norm_group = None
                current_other_group = None
                current_col_group = {
                    "kind": "columna",
                    "title": "",
                    "step_indices": [idx],
                    "has_swap": True,
                    "pivot_row": None,
                    "pivot_col": None,
                    "pivot_val": None,
                }
                raw_groups.append(current_col_group)
                group_idx = len(raw_groups) - 1

            elif kind == "pivote":
                r = parsed["row1"] + 1
                c = parsed["col"] + 1
                pivot = (r - 1, c - 1)
                rows_changed = []
                p_val = (
                    format_fraction_str(mat.get(r - 1, c - 1))
                    if mat is not None
                    else ""
                )
                explanation = (
                    f"Pivote: fila {r}, columna {c} (valor {p_val}). "
                    f"Usaremos esta fila para anular el resto de la columna {c}."
                )
                current_norm_group = None
                current_other_group = None

                if (
                    current_col_group is not None
                    and current_col_group.get("pivot_row") is None
                ):
                    current_col_group["pivot_row"] = r - 1
                    current_col_group["pivot_col"] = c - 1
                    current_col_group["pivot_val"] = p_val
                    current_col_group["step_indices"].append(idx)
                    group_idx = raw_groups.index(current_col_group)
                else:
                    current_col_group = {
                        "kind": "columna",
                        "title": "",
                        "step_indices": [idx],
                        "has_swap": False,
                        "pivot_row": r - 1,
                        "pivot_col": c - 1,
                        "pivot_val": p_val,
                    }
                    raw_groups.append(current_col_group)
                    group_idx = len(raw_groups) - 1

            elif kind == "eliminacion":
                t = parsed["row1"] + 1
                f = parsed["val_str"]
                p = parsed["row2"] + 1
                rows_changed = [t - 1]
                pivot_col = (
                    current_col_group["pivot_col"]
                    if (
                        current_col_group is not None
                        and current_col_group.get("pivot_col") is not None
                    )
                    else (p - 1)
                )
                pivot = (p - 1, pivot_col)
                explanation = (
                    f"Hacemos 0 la entrada de la fila {t} en la columna {pivot_col + 1}: "
                    f"Fila {t} = Fila {t} − ({f}) · Fila {p}. La operación afecta la "
                    f"fila completa, es decir, los dos bloques a la vez."
                )
                current_norm_group = None
                current_other_group = None
                if current_col_group is not None:
                    current_col_group["step_indices"].append(idx)
                    group_idx = raw_groups.index(current_col_group)
                else:
                    if current_other_group is None:
                        current_other_group = {
                            "kind": "otros",
                            "title": "Otras operaciones",
                            "step_indices": [idx],
                        }
                        raw_groups.append(current_other_group)
                        group_idx = len(raw_groups) - 1
                    else:
                        current_other_group["step_indices"].append(idx)
                        group_idx = raw_groups.index(current_other_group)

            elif kind == "normalizacion":
                r = parsed["row1"] + 1
                v = parsed["val_str"]
                rows_changed = [r - 1]
                pivot = (r - 1, r - 1) if (r - 1 < n) else None
                explanation = (
                    f"Dividimos la fila {r} entre {v} para que su pivote valga 1 "
                    f"y la diagonal del bloque izquierdo quede igual a la identidad."
                )
                current_col_group = None
                current_other_group = None
                if current_norm_group is None:
                    current_norm_group = {
                        "kind": "normalizacion",
                        "title": "Normalización: cada pivote pasa a 1",
                        "step_indices": [idx],
                    }
                    raw_groups.append(current_norm_group)
                    group_idx = len(raw_groups) - 1
                else:
                    current_norm_group["step_indices"].append(idx)
                    group_idx = raw_groups.index(current_norm_group)

            else:
                kind = "otro"
                explanation = desc
                if current_col_group is not None:
                    current_col_group["step_indices"].append(idx)
                    group_idx = raw_groups.index(current_col_group)
                elif current_norm_group is not None:
                    current_norm_group["step_indices"].append(idx)
                    group_idx = raw_groups.index(current_norm_group)
                else:
                    if current_other_group is None:
                        current_other_group = {
                            "kind": "otros",
                            "title": "Otras operaciones",
                            "step_indices": [idx],
                        }
                        raw_groups.append(current_other_group)
                        group_idx = len(raw_groups) - 1
                    else:
                        current_other_group["step_indices"].append(idx)
                        group_idx = raw_groups.index(current_other_group)

            # Si el paso es el ÚLTIMO de la lista y status == SUCCESS
            if idx == len(raw_steps) - 1 and status == "SUCCESS":
                explanation = (
                    "Resultado: el bloque izquierdo ya es I, por lo tanto el bloque "
                    "derecho es A⁻¹. " + explanation
                )

            steps.append({
                "index": idx,
                "description": desc,
                "kind": kind,
                "group_index": group_idx,
                "pivot": pivot,
                "rows_changed": rows_changed,
                "swap_rows": swap_rows,
                "explanation": explanation,
                "matrix": mat,
            })

        # Formatear grupos finales
        groups: list[dict] = []
        for g in raw_groups:
            k = len(g["step_indices"])
            summary = "1 operación" if k == 1 else f"{k} operaciones"
            kind = g.get("kind", "otro")
            if kind == "columna":
                c = g.get("pivot_col")
                r = g.get("pivot_row")
                val = g.get("pivot_val")
                has_swap = g.get("has_swap", False)
                if c is not None and r is not None and val is not None:
                    title = f"Columna {c + 1} · pivote {val} en fila {r + 1}"
                    if has_swap:
                        title += " · con intercambio"
                elif c is not None:
                    title = f"Columna {c + 1}"
                else:
                    title = "Columna"
            else:
                title = g.get("title", "")

            groups.append({
                "title": title,
                "summary": summary,
                "kind": kind,
                "step_indices": g["step_indices"],
            })

        stats = {
            "total": len(steps),
            "pivotes": sum(1 for s in steps if s["kind"] == "pivote"),
            "intercambios": sum(1 for s in steps if s["kind"] == "intercambio"),
            "eliminaciones": sum(1 for s in steps if s["kind"] == "eliminacion"),
            "normalizaciones": sum(1 for s in steps if s["kind"] == "normalizacion"),
        }

        return steps, groups, stats

    @classmethod
    def build_focus_for_step(cls, steps: list[dict], idx: int) -> dict:
        """Construye rows_before, rows_after y cols para un paso dado usando excerpt_rows."""
        from src.ai.context import excerpt_rows
        from src.frontend.controllers._step_classifier import classify_step

        if not steps:
            return {"rows_before": {}, "rows_after": {}, "cols": None}

        if 0 <= idx < len(steps):
            i = idx
        elif 1 <= idx <= len(steps):
            i = idx - 1
        else:
            i = max(0, min(idx, len(steps) - 1))

        step = steps[i]
        mat = step.get("matrix")
        if mat is None:
            return {"rows_before": {}, "rows_after": {}, "cols": None}

        rows = [[mat.get(r, c) for c in range(mat.cols)] for r in range(mat.rows)]

        prev_step = steps[i - 1] if i > 0 else step
        prev_mat = prev_step.get("matrix", mat)
        prev_rows = [[prev_mat.get(r, c) for c in range(prev_mat.cols)] for r in range(prev_mat.rows)] if prev_mat else rows

        desc = step.get("description", "")
        parsed = classify_step(desc)
        kind = parsed.get("kind", step.get("kind", "otro"))

        center_col = 0
        if step.get("pivot"):
            center_col = step["pivot"][1]
        elif parsed.get("col") is not None:
            center_col = parsed["col"]
        else:
            for k in range(i, -1, -1):
                if steps[k].get("pivot"):
                    center_col = steps[k]["pivot"][1]
                    break

        rows_before = {}
        rows_after = {}
        cols_range = None

        if kind == "intercambio":
            r1 = parsed.get("row1")
            r2 = parsed.get("row2")
            if r1 is None or r2 is None:
                swap = step.get("swap_rows")
                if swap:
                    r1, r2 = swap
            if r1 is not None and r2 is not None:
                rows_before, cols_range = excerpt_rows(prev_rows, [r1, r2], center_col)
                rows_after, _ = excerpt_rows(rows, [r1, r2], center_col)
        elif kind == "eliminacion":
            t = parsed.get("row1")
            p = parsed.get("row2")
            target_rows = []
            if t is not None:
                target_rows.append(t)
            elif step.get("rows_changed"):
                target_rows.extend(step["rows_changed"])
            if p is not None and p not in target_rows:
                target_rows.append(p)
            
            rows_before, cols_range = excerpt_rows(prev_rows, target_rows if target_rows else [0], center_col)
            rows_after, _ = excerpt_rows(rows, [t] if t is not None else target_rows, center_col)
        elif kind in ("normalizacion", "pivote"):
            r = parsed.get("row1")
            if r is None and step.get("rows_changed"):
                r = step["rows_changed"][0]
            if r is None and step.get("pivot"):
                r = step["pivot"][0]
            r_idx = r if r is not None else 0
            rows_before, cols_range = excerpt_rows(prev_rows, [r_idx], center_col)
            rows_after, _ = excerpt_rows(rows, [r_idx], center_col)
        else:
            target_rows = list(step.get("rows_changed", []))
            if not target_rows and step.get("pivot"):
                target_rows = [step["pivot"][0]]
            if not target_rows:
                target_rows = [0]
            rows_before, cols_range = excerpt_rows(prev_rows, target_rows, center_col)
            rows_after, _ = excerpt_rows(rows, target_rows, center_col)

        return {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "cols": cols_range,
        }
