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

from src.frontend.controllers._agrupar_pasos import agrupar_pasos_eliminacion
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
                ok, val, err_msg = MatrixValidator.parsear_numero_exacto(cell_str)
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
            res = solver.resolver(matrix_a, build_step_latex=False)
        except ValueError as e:
            return cls._empty_result(
                "ERROR",
                str(e),
                n=n,
                elapsed_s=time.perf_counter() - t0,
                matrix_a=matrix_a,
            )
        except Exception:
            logger.exception("Error inesperado en MatrixInverseSolver")
            return cls._empty_result(
                "ERROR",
                "Ocurrió un error inesperado al calcular la inversa. Inténtalo de nuevo.",
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
        return agrupar_pasos_eliminacion(raw_steps, n, status, contexto="inversa")

    @classmethod
    def build_focus_for_step(cls, steps: list[dict], idx: int) -> dict:
        """Construye rows_before, rows_after y cols para un paso dado usando extraer_filas."""
        from src.ai.context import extraer_filas
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
                rows_before, cols_range = extraer_filas(prev_rows, [r1, r2], center_col)
                rows_after, _ = extraer_filas(rows, [r1, r2], center_col)
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
            
            rows_before, cols_range = extraer_filas(prev_rows, target_rows if target_rows else [0], center_col)
            rows_after, _ = extraer_filas(rows, [t] if t is not None else target_rows, center_col)
        elif kind in ("normalizacion", "pivote"):
            r = parsed.get("row1")
            if r is None and step.get("rows_changed"):
                r = step["rows_changed"][0]
            if r is None and step.get("pivot"):
                r = step["pivot"][0]
            r_idx = r if r is not None else 0
            rows_before, cols_range = extraer_filas(prev_rows, [r_idx], center_col)
            rows_after, _ = extraer_filas(rows, [r_idx], center_col)
        else:
            target_rows = list(step.get("rows_changed", []))
            if not target_rows and step.get("pivot"):
                target_rows = [step["pivot"][0]]
            if not target_rows:
                target_rows = [0]
            rows_before, cols_range = extraer_filas(prev_rows, target_rows, center_col)
            rows_after, _ = extraer_filas(rows, target_rows, center_col)

        return {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "cols": cols_range,
        }

    # Alias canónico en castellano
    procesar_inversa = process_inverse

