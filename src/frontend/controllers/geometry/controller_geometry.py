"""Controller para el Visualizador Geométrico (F8a).

Métodos estáticos que devuelven dict JSON-serializable (patrón InverseOpsController).
Python puro: no importa nicegui ni plotly.

Claves devueltas (documentadas por método):
- process_lines_planes: status, equations, solution_status, set, pending_param,
  flags, range, error_cell, message, n
- process_vectors: status, u, v, static, frames, default_frame, range, n, error_cell, message
- process_combination: status, b, vectors, chain, representation, b_outside_span,
  range, n, error_cell, message, solution_status
"""
from __future__ import annotations

import json
import logging
import math
from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.vector_ops.linear_combination import LinearCombinationSolver
from src.backend.utils.validators import MatrixValidator
from src.frontend.controllers.linear_systems._shared import (
    parse_payload,
    validate_and_build_augmented,
)
from src.frontend.controllers.geometry._solution_set import (
    from_gauss_result,
)
from src.frontend.controllers.vector_ops.controller_vector_ops import build_vector_from_dict
from src.backend.solvers.vector_ops.formatters import format_linear_expression, vector_to_latex
from src.backend.utils.formatters import number_to_latex

logger = logging.getLogger(__name__)

# ---------- helpers ----------

def error_cell_selector(error_cell: dict, *, scene: str, grid_n: int) -> str | None:
    if not error_cell:
        return None
    kind = error_cell.get("kind")
    if kind == "A":
        row = error_cell.get("row", 0)
        col = error_cell.get("col", 0)
        return f'input[data-row="{row}"][data-col="{col}"]'
    elif kind == "b":
        row = error_cell.get("row", 0)
        return f'input[data-row="{row}"][data-col="{grid_n}"]'
    elif kind == "vec":
        name = error_cell.get("name", "")
        index = error_cell.get("index", 0)
        panel_id = "geo_vec" if scene == 'vectores' else "geo_comb"
        return f'input[data-vec-id="{panel_id}_{name}"][data-vec-idx="{index}"]'
    return None

def clip_line_to_box(p: list[float], d: list[float], half: float) -> tuple[float, float] | None:
    t0 = -float('inf')
    t1 = float('inf')
    for p_i, d_i in zip(p, d):
        if abs(d_i) < 1e-12:
            if p_i < -half or p_i > half:
                return None
        else:
            t_min = (-half - p_i) / d_i
            t_max = (half - p_i) / d_i
            if t_min > t_max:
                t_min, t_max = t_max, t_min
            t0 = max(t0, t_min)
            t1 = min(t1, t_max)
    if t0 > t1 or t0 == -float('inf') or t1 == float('inf'):
        return None
    return t0, t1

def _safe_float(v: Fraction) -> float | None:
    """Convert Fraction to float, returning None on overflow."""
    try:
        return float(v)
    except (OverflowError, ValueError):
        return None


def _frac_str(v: Fraction) -> str:
    return str(v)


def _locate_cell_error(matrix_A_raw, vector_b_raw) -> dict | None:
    """Scan raw cells and return the first error_cell dict, or None."""
    for i, row in enumerate(matrix_A_raw):
        for j, cell in enumerate(row):
            raw = str(cell).strip() if cell is not None and str(cell).strip() else '0'
            ok, _, _ = MatrixValidator.parse_number_exact(raw)
            if not ok:
                return {"kind": "A", "row": i, "col": j}
    for i, cell in enumerate(vector_b_raw):
        raw = str(cell).strip() if cell is not None and str(cell).strip() else '0'
        ok, _, _ = MatrixValidator.parse_number_exact(raw)
        if not ok:
            return {"kind": "b", "row": i}
    return None


def _locate_vec_error(vectors_raw: list[list[str]], names: list[str]) -> dict | None:
    """Scan raw vector cells and return the first error_cell dict, or None."""
    for vi, vec in enumerate(vectors_raw):
        for ci, cell in enumerate(vec):
            raw = str(cell).strip() if cell is not None and str(cell).strip() else '0'
            ok, _, _ = MatrixValidator.parse_number_exact(raw)
            if not ok:
                return {"kind": "vec", "name": names[vi], "index": ci}
    return None


def auto_range(values: list[float], *, minimum: float = 5.0, margin: float = 0.35) -> list[float]:
    """Compute a symmetric axis range [-half, half] with 1-2-5 rounding.

    - Non-finite values are ignored.
    - If no finite values, returns [-minimum, minimum].
    - The half-width is at least `minimum`.
    - Rounds up to the next 1-2-5 scale.
    - Tope: 1e6 to prevent absurd ranges.

    Returns [lo, hi] as a list of two floats.
    """
    finite = [v for v in values if v is not None and math.isfinite(v)]
    if not finite:
        return [-minimum, minimum]

    max_abs = max(abs(v) for v in finite)
    raw_half = max(max_abs * (1.0 + margin), minimum)

    # Clamp
    raw_half = min(raw_half, 1e6)

    # 1-2-5 rounding
    if raw_half <= 0:
        return [-minimum, minimum]

    exp = math.floor(math.log10(raw_half))
    base = 10 ** exp
    norm = raw_half / base

    if norm <= 1.0:
        nice = 1.0
    elif norm <= 2.0:
        nice = 2.0
    elif norm <= 5.0:
        nice = 5.0
    else:
        nice = 10.0

    half = nice * base
    return [-half, half]


def _classify_equation(coeffs: list[Fraction], b: Fraction, n: int) -> str:
    """Classify a single equation: 'line', 'plane', 'trivial', 'contradiction'."""
    all_zero = all(c == 0 for c in coeffs)
    if all_zero:
        if b == 0:
            return "trivial"
        else:
            return "contradiction"
    if n == 2:
        return "line"
    elif n == 3:
        return "plane"
    return "line"  # fallback


def _are_proportional(a: list[Fraction], b_row: list[Fraction]) -> bool:
    """Check if two coefficient vectors are proportional (Fraction exact)."""
    # Find a non-zero entry to establish ratio
    ratio = None
    for ai, bi in zip(a, b_row):
        if ai == 0 and bi == 0:
            continue
        if ai == 0 or bi == 0:
            return False
        r = Fraction(bi, ai)
        if ratio is None:
            ratio = r
        elif r != ratio:
            return False
    return ratio is not None


class GeometryController:
    """Controller del Visualizador Geométrico (F8a).

    Todos los métodos son estáticos y devuelven dict JSON-serializable.
    """

    @staticmethod
    def process_lines_planes(payload_json: str) -> dict:
        """Process a system Ax = b for geometric visualization.

        Payload: {"matrix_A": [[str]], "vector_b": [str]}

        Returns dict with keys:
            status, equations, solution_status, set, pending_param,
            flags, range, error_cell, message, n
        """
        pending_param = False
        sp = None
        flags_list = []

        data, err = parse_payload(payload_json)
        if err is not None:
            err_dict = json.loads(err)
            return {
                "status": "ERROR",
                "message": err_dict.get("message", "Payload inválido."),
                "error_cell": None,
            }

        matrix_result = validate_and_build_augmented(data)
        aug_matrix, A_fracs, b_fracs, m, n, err_json = matrix_result

        if err_json is not None:
            err_dict = json.loads(err_json)
            # Try to locate the exact cell
            error_cell = _locate_cell_error(
                data.get("matrix_A", []),
                data.get("vector_b", []),
            )
            return {
                "status": "ERROR",
                "message": err_dict.get("message", ""),
                "error_cell": error_cell,
            }

        # Check dimension
        if n not in (2, 3):
            return {
                "status": "ERROR",
                "code": "bad_dimension",
                "message": f"Este visualizador solo grafica sistemas con 2 o 3 variables (el tuyo tiene {n}). Puedes resolverlo en Sistemas de ecuaciones.",
                "error_cell": None,
                "n": n,
            }

        # Classify each equation
        equations = []
        var_names = ["x", "y", "z"][:n]
        for i in range(m):
            coeffs = A_fracs[i]
            bi = b_fracs[i]
            kind = _classify_equation(coeffs, bi, n)

            c_exact = [_frac_str(c) for c in coeffs]
            b_ex = _frac_str(bi)
            lhs = format_linear_expression(coeffs, var_names)
            rhs = number_to_latex(bi)

            coeffs_floats = [_safe_float(c) for c in coeffs]
            b_float = _safe_float(bi)
            if any(cf is None for cf in coeffs_floats) or b_float is None:
                return {
                    "status": "ERROR",
                    "code": "not_finite",
                    "message": "Algún valor es demasiado grande para graficarlo. Usa números más pequeños.",
                    "error_cell": None,
                    "n": n,
                }

            eq_data = {
                "index": i,
                "kind": kind,
                "coeffs": coeffs_floats,
                "coeffs_exact": c_exact,
                "b": b_float,
                "b_exact": b_ex,
                "latex": f"{lhs} = {rhs}",
            }
            equations.append(eq_data)

        # Solve with Gauss
        solver = GaussSolver(aug_matrix)
        result = solver.solve()
        solution_status = result["status"]

        # Classify solution set
        sol_set = from_gauss_result(result)
        # Compute range FIRST
        range_values = []
        for i in range(m):
            coeffs = A_fracs[i]
            bi = b_fracs[i]
            for j in range(n):
                if coeffs[j] != 0:
                    intercept = _safe_float(bi / coeffs[j])
                    if intercept is not None:
                        range_values.append(intercept)

        if sol_set is not None and sol_set.point is not None:
            for p in sol_set.point:
                pf = _safe_float(p)
                if pf is not None:
                    range_values.append(pf)

        range_values = [v for v in range_values if v is not None]

        axis_range = auto_range(range_values)
        h = axis_range[1]

        # Extra validation and enrichment for INFINITE_SOLUTIONS
        if solution_status == "INFINITE_SOLUTIONS":
            from src.frontend.controllers.geometry._solution_set import get_solution_param, from_solution_param
            sp = get_solution_param(result)
            if sp:
                valid = True
                particular = sp["particular"]
                directions = sp["directions"]
                for i in range(m):
                    row = A_fracs[i]
                    p_val = sum(r * p for r, p in zip(row, particular))
                    if p_val != b_fracs[i]:
                        valid = False
                        break
                    for d in directions:
                        d_val = sum(r * v for r, v in zip(row, d))
                        if d_val != 0:
                            valid = False
                            break
                    if not valid:
                        break
                if valid:
                    sol_set = from_solution_param(sp)
                    pending_param = False
                else:
                    logger.error("Fallo validación defensiva en INFINITE_SOLUTIONS")
                    sol_set = None
                    pending_param = True
                    sp = None
            else:
                pending_param = True
                sol_set = None

        set_data = None
        if sol_set is not None:
            point_float = None
            point_exact = None
            point_latex = None
            if sol_set.point is not None:
                point_float = [_safe_float(p) for p in sol_set.point]
                point_exact = [_frac_str(p) for p in sol_set.point]
                point_mat = Matrix(n, 1, [[x] for x in sol_set.point])
                point_latex = vector_to_latex(point_mat)

            is_whole_space = (sol_set.dimension == n)
            # Para whole_space en R² (kind sale PLANE por classify), la vista debe mirar whole_space antes que kind
            kind_label = "whole_space" if is_whole_space else sol_set.kind.value

            set_data = {
                "kind": sol_set.kind.value,
                "kind_label": kind_label,
                "dimension": sol_set.dimension,
                "whole_space": is_whole_space,
                "point": point_float,
                "point_exact": point_exact,
                "point_latex": point_latex,
            }
            if sp:
                # Add directions
                set_data["directions"] = [[_safe_float(v) for v in d] for d in sp["directions"]]
                set_data["directions_exact"] = [[_frac_str(v) for v in d] for d in sp["directions"]]
                set_data["param_names"] = sp["param_names"]
                set_data["free_vars"] = [["x", "y", "z"][c] for c in sp["free_cols"]]

                # param_latex
                parts = []
                p_mat = Matrix(n, 1, [[x] for x in sp["particular"]])
                p_latex = vector_to_latex(p_mat)
                parts.append(p_latex)
                for i, d in enumerate(sp["directions"]):
                    d_mat = Matrix(n, 1, [[x] for x in d])
                    d_latex = vector_to_latex(d_mat)
                    parts.append(f"{sp['param_names'][i]}{d_latex}")

                set_data["param_latex"] = r"\mathbf{x} = " + " + ".join(parts)

                # description
                if n == 2 and sol_set.dimension == 1:
                    d_str = ", ".join(set_data["directions_exact"][0])
                    p_str = ", ".join(point_exact) if point_exact else ""
                    set_data["description"] = f"Las soluciones forman una recta que pasa por ({p_str}) con dirección ({d_str})."
                elif n == 3 and sol_set.dimension == 1:
                    d_str = ", ".join(set_data["directions_exact"][0])
                    p_str = ", ".join(point_exact) if point_exact else ""
                    set_data["description"] = f"Las soluciones forman una recta que pasa por ({p_str}) con dirección ({d_str})."
                elif n == 3 and sol_set.dimension == 2:
                    d1_str = ", ".join(set_data["directions_exact"][0])
                    d2_str = ", ".join(set_data["directions_exact"][1])
                    p_str = ", ".join(point_exact) if point_exact else ""
                    set_data["description"] = f"Las soluciones forman un plano que pasa por ({p_str}) generado por ({d1_str}) y ({d2_str})."

                # Clip geometry
                if not set_data["whole_space"]:
                    if sol_set.dimension == 1:
                        d_f = set_data["directions"][0]
                        p_f = set_data["point"]
                        if all(v is not None for v in p_f) and all(v is not None for v in d_f):
                            t_bounds = clip_line_to_box(p_f, d_f, h)
                            if t_bounds:
                                t0, t1 = t_bounds
                                set_data["segment"] = [
                                    [p_f[i] + t0 * d_f[i] for i in range(n)],
                                    [p_f[i] + t1 * d_f[i] for i in range(n)]
                                ]
                                set_data["segment_visible"] = True
                            else:
                                set_data["segment_visible"] = False
                                logger.warning("Recta solución fuera de la caja visual.")
                    elif sol_set.dimension == 2 and n == 3:
                        d1 = sp["directions"][0]
                        d2 = sp["directions"][1]
                        p = sp["particular"]
                        nx = d1[1]*d2[2] - d1[2]*d2[1]
                        ny = d1[2]*d2[0] - d1[0]*d2[2]
                        nz = d1[0]*d2[1] - d1[1]*d2[0]
                        offset = nx*p[0] + ny*p[1] + nz*p[2]
                        set_data["normal_exact"] = [_frac_str(nx), _frac_str(ny), _frac_str(nz)]
                        set_data["offset_exact"] = _frac_str(offset)

                        nx_f, ny_f, nz_f = _safe_float(nx), _safe_float(ny), _safe_float(nz)
                        off_f = _safe_float(offset)
                        if all(v is not None for v in (nx_f, ny_f, nz_f, off_f)):
                            set_data["normal"] = [nx_f, ny_f, nz_f]
                            set_data["offset"] = off_f

        # Parallel flag
        if n == 2 and solution_status == "NO_SOLUTION" and m >= 2:
            for i in range(m):
                for j in range(i + 1, m):
                    if _are_proportional(A_fracs[i], A_fracs[j]):
                        ratio = None
                        for ai, aj in zip(A_fracs[i], A_fracs[j]):
                            if ai != 0:
                                ratio = Fraction(aj, ai)
                                break
                        if ratio is not None and b_fracs[j] != ratio * b_fracs[i]:
                            flags_list.append("parallel")
                            break
                if "parallel" in flags_list:
                    break

        out_of_range = any(abs(v) > h for v in range_values)

        return {
            "status": "OK",
            "n": n,
            "m": m,
            "equations": equations,
            "solution_status": solution_status,
            "set": set_data,
            "pending_param": pending_param,
            "flags": flags_list,
            "range": axis_range,
            "out_of_range": out_of_range,
            "error_cell": None,
            "message": "",
        }

    @staticmethod
    def process_vectors(payload_json: str) -> dict:
        """Process two vectors u, v for vector visualization.

        Payload: {"vectors": [{"data": [str], "orientation": "column"}, ...]}
        Exactly 2 vectors with n in {2, 3}.

        Returns dict with keys:
            status, u, v, static, frames, default_frame, range, n, error_cell, message
        """
        data, err = parse_payload(payload_json)
        if err is not None:
            err_dict = json.loads(err)
            return {"status": "ERROR", "message": err_dict.get("message", ""), "error_cell": None}

        vectors_raw = data.get("vectors", [])
        if not isinstance(vectors_raw, list) or len(vectors_raw) != 2:
            return {"status": "ERROR", "message": "Se necesitan exactamente 2 vectores.", "error_cell": None}

        # Parse vectors
        parsed_vecs = []
        names = ["u", "v"]
        for vi, vec_data in enumerate(vectors_raw):
            raw = vec_data if isinstance(vec_data, list) else vec_data.get("data", [])
            if not isinstance(raw, list):
                return {"status": "ERROR", "message": "Datos de vector inválidos.", "error_cell": None}

            components = []
            for ci, cell in enumerate(raw):
                cell_str = str(cell).strip() if cell is not None else "0"
                if not cell_str:
                    cell_str = "0"
                ok, val, msg = MatrixValidator.parse_number_exact(cell_str)
                if not ok:
                    return {
                        "status": "ERROR",
                        "message": f"Error en {names[vi]}[{ci + 1}]: {msg}",
                        "error_cell": {"kind": "vec", "name": names[vi], "index": ci},
                    }
                components.append(val)
            parsed_vecs.append(components)

        n = len(parsed_vecs[0])
        if n != len(parsed_vecs[1]):
            return {"status": "ERROR", "message": "Los vectores deben tener la misma dimensión.", "error_cell": None}

        if n not in (2, 3):
            return {
                "status": "ERROR",
                "code": "bad_dimension",
                "message": f"Solo se grafican vectores de dimensión 2 o 3 (los tuyos tienen {n}).",
                "error_cell": None,
            }

        u_frac = parsed_vecs[0]
        v_frac = parsed_vecs[1]

        # Static data
        u_float = [_safe_float(c) for c in u_frac]
        v_float = [_safe_float(c) for c in v_frac]
        u_plus_v_float = [_safe_float(a + b) for a, b in zip(u_frac, v_frac)]

        static = {
            "u": u_float,
            "v": v_float,
            "u_plus_v": u_plus_v_float,
        }

        # Check overflow
        all_values = u_float + v_float + u_plus_v_float
        if any(v is None for v in all_values):
            return {
                "status": "ERROR",
                "code": "not_finite",
                "message": "Las coordenadas generan valores no finitos.",
                "error_cell": None,
            }

        # Precomputed frames: k = j/4 for j = -12..12 (25 frames)
        frames = []
        all_range_values = list(all_values)

        for j in range(-12, 13):
            k_frac = Fraction(j, 4)
            k_float = float(k_frac)
            ku = [_safe_float(k_frac * c) for c in u_frac]
            ku_plus_v = [_safe_float(k_frac * a + b) for a, b in zip(u_frac, v_frac)]

            frame = {
                "k": k_float,
                "k_exact": _frac_str(k_frac),
                "ku": ku,
                "ku_plus_v": ku_plus_v,
            }
            frames.append(frame)

            # Add to range values
            if ku is not None:
                all_range_values.extend([x for x in ku if x is not None])
            if ku_plus_v is not None:
                all_range_values.extend([x for x in ku_plus_v if x is not None])

        # Default frame index: k = 1 => j = 4 => index = 4 + 12 = 16
        default_frame = 16

        axis_range = auto_range(all_range_values)
        out_of_range = any(abs(v) > axis_range[1] for v in all_range_values if v is not None)

        return {
            "status": "OK",
            "n": n,
            "u": {"float": u_float, "exact": [_frac_str(c) for c in u_frac]},
            "v": {"float": v_float, "exact": [_frac_str(c) for c in v_frac]},
            "static": static,
            "frames": frames,
            "default_frame": default_frame,
            "range": axis_range,
            "out_of_range": out_of_range,
            "error_cell": None,
            "message": "",
        }

    @staticmethod
    def process_combination(payload_json: str) -> dict:
        """Process b and 1-4 column vectors for linear combination visualization.

        Payload: {"b": {"data": [str], "orientation": "column"},
                  "vectors": [{"data": [str], "orientation": "column"}, ...]}

        Returns dict with keys:
            status, b, vectors, chain, representation, b_outside_span,
            range, n, error_cell, message, solution_status
        """
        data, err = parse_payload(payload_json)
        if err is not None:
            err_dict = json.loads(err)
            return {"status": "ERROR", "message": err_dict.get("message", ""), "error_cell": None}

        b_raw = data.get("b", {})
        vectors_raw = data.get("vectors", [])

        if not isinstance(vectors_raw, list) or len(vectors_raw) < 1 or len(vectors_raw) > 4:
            return {"status": "ERROR", "message": "Se necesitan entre 1 y 4 vectores columna.", "error_cell": None}

        # Parse b
        try:
            b_mat = build_vector_from_dict(b_raw)
        except ValueError as e:
            # Try to locate the error cell
            b_data = b_raw.get("data", [])
            for ci, cell in enumerate(b_data):
                ok, _, _ = MatrixValidator.parse_number_exact(str(cell).strip() or "0")
                if not ok:
                    return {
                        "status": "ERROR",
                        "message": str(e),
                        "error_cell": {"kind": "vec", "name": "b", "index": ci},
                    }
            return {"status": "ERROR", "message": str(e), "error_cell": None}

        n = b_mat.rows
        if n not in (2, 3):
            return {
                "status": "ERROR",
                "code": "bad_dimension",
                "message": f"Solo se grafican vectores de dimensión 2 o 3 (b tiene {n}).",
                "error_cell": None,
            }

        # Parse column vectors
        col_mats = []
        vec_names = [f"v_{i+1}" for i in range(len(vectors_raw))]
        for vi, v_raw in enumerate(vectors_raw):
            try:
                v_mat = build_vector_from_dict(v_raw)
            except ValueError as e:
                v_data = v_raw.get("data", [])
                for ci, cell in enumerate(v_data):
                    ok, _, _ = MatrixValidator.parse_number_exact(str(cell).strip() or "0")
                    if not ok:
                        return {
                            "status": "ERROR",
                            "message": str(e),
                            "error_cell": {"kind": "vec", "name": vec_names[vi], "index": ci},
                        }
                return {"status": "ERROR", "message": str(e), "error_cell": None}

            if v_mat.rows != n:
                return {
                    "status": "ERROR",
                    "message": f"El vector {vec_names[vi]} tiene dimensión {v_mat.rows}, pero b tiene {n}.",
                    "error_cell": None,
                }
            col_mats.append(v_mat)

        # Solve with LinearCombinationSolver
        try:
            solver = LinearCombinationSolver()
            result = solver.solve(b_mat, col_mats)
        except Exception as e:
            logger.exception("Error en LinearCombinationSolver")
            return {"status": "ERROR", "message": f"Error al resolver: {e}", "error_cell": None}

        sol_status = result.get("status", "ERROR")

        # Extract b as floats
        b_float = [_safe_float(Fraction(b_mat.get(i, 0))) for i in range(n)]
        b_exact = [_frac_str(Fraction(b_mat.get(i, 0))) for i in range(n)]

        # Extract vectors as floats
        vecs_float = []
        vecs_exact = []
        for v_mat in col_mats:
            vf = [_safe_float(Fraction(v_mat.get(i, 0))) for i in range(n)]
            ve = [_frac_str(Fraction(v_mat.get(i, 0))) for i in range(n)]
            vecs_float.append(vf)
            vecs_exact.append(ve)

        if any(x is None for x in b_float) or any(any(x is None for x in vf) for vf in vecs_float):
            return {
                "status": "ERROR",
                "code": "not_finite",
                "message": "Algún valor es demasiado grande para graficarlo. Usa números más pequeños.",
                "error_cell": None,
                "n": n,
            }

        # Compute range values
        range_values = []
        for v in b_float:
            if v is not None:
                range_values.append(v)
        for vf in vecs_float:
            for v in vf:
                if v is not None:
                    range_values.append(v)

        chain = None
        representation = None
        b_outside_span = False

        if sol_status == "UNIQUE":
            # Build chain of cumulative partial sums
            coeffs_exact = result.get("coeficientes") or []
            if not coeffs_exact:
                coeffs_str = result.get("coeficientes_str", [])
                coeffs_exact = []
                for cs in coeffs_str:
                    ok, val, _ = MatrixValidator.parse_number_exact(cs)
                    coeffs_exact.append(val if ok else Fraction(0))

            chain = []
            cumulative = [Fraction(0)] * n
            for vi, c in enumerate(coeffs_exact):
                c_frac = Fraction(c) if not isinstance(c, Fraction) else c
                for dim in range(n):
                    cumulative[dim] += c_frac * Fraction(col_mats[vi].get(dim, 0))
                chain_point = {
                    "float": [_safe_float(x) for x in cumulative],
                    "exact": [_frac_str(x) for x in cumulative],
                    "label": f"c_{vi+1}·v_{vi+1}" if vi == 0 else f"+ c_{vi+1}·v_{vi+1}",
                }
                chain.append(chain_point)
                for x in chain_point["float"]:
                    if x is not None:
                        range_values.append(x)

        elif sol_status == "INFINITE":
            representation = "non_unique"

        elif sol_status == "NO_SOLUTION":
            b_outside_span = True

        axis_range = auto_range(range_values)
        out_of_range = any(abs(v) > axis_range[1] for v in range_values if v is not None)

        return {
            "status": "OK",
            "n": n,
            "b": {"float": b_float, "exact": b_exact},
            "vectors": [{"float": vf, "exact": ve} for vf, ve in zip(vecs_float, vecs_exact)],
            "chain": chain,
            "representation": representation,
            "b_outside_span": b_outside_span,
            "solution_status": sol_status,
            "range": axis_range,
            "out_of_range": out_of_range,
            "error_cell": None,
            "message": result.get("message", ""),
        }
