import json

from src.backend.resolutores.sistemas_lineales.gauss_jordan import ResolutorGaussJordan as GaussJordanSolver
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex as matrix_to_latex
from src.backend.utils.validators import MatrixValidator
from src.frontend.controllers._agrupar_pasos import agrupar_pasos_eliminacion
from src.frontend.controllers.linear_systems._shared import (
    build_steps_meta,
    parse_payload,
    serialize_matrix,
    validate_and_build_augmented,
)


class GaussJordanController:
    @staticmethod
    def process_system(json_payload: str) -> str:
        data, err = parse_payload(json_payload)
        if err:
            return err

        matrix, A_fractions, b_fractions, _m, _n, err = validate_and_build_augmented(data)
        if err:
            return err

        variables = data.get("variables")

        # --- Ejecución del solver ---
        solver = GaussJordanSolver(matrix, nombres_variables=variables)
        result = solver.resolver()

        classification = result.get("message", "")
        solution = result.get("solution")

        raw_steps = result.get("steps", [])
        steps_meta = build_steps_meta(raw_steps)

        steps_latex = []
        for step in raw_steps:
            steps_latex.append({
                "descripcion": step["description"],
                "matriz": matrix_to_latex(step["matrix"])
            })

        verification_steps_latex = []
        if result.get("status") == "UNIQUE_SOLUTION":
            _, verification_steps_latex = MatrixValidator.verify_solution(
                A_fractions, solution, b_fractions, as_latex=True
            )

        pasos, groups, stats = agrupar_pasos_eliminacion(
            raw_steps, _n, result.get("status"), contexto="sistema", metodo="gauss-jordan"
        )
        steps_view = [
            {
                "index": s["index"],
                "kind": s["kind"],
                "description": s["description"],
                "explanation": s["explanation"],
                "group_index": s["group_index"],
                "pivot": list(s["pivot"]) if s["pivot"] is not None else None,
                "rows_changed": list(s["rows_changed"]),
                "swap_rows": list(s["swap_rows"]) if s["swap_rows"] is not None else None,
                "matrix": serialize_matrix(s["matrix"]),
            }
            for s in pasos
        ]

        vars_list = variables if variables is not None else [f"x{i+1}" for i in range(_n)]

        response = {
            "status": result.get("status"),
            "classification": classification,
            "message": classification,
            "solution": [str(x) for x in solution] if solution else [],
            "solution_param": result.get("solution_param"),
            "analisis_sistema": result.get("analisis_sistema"),
            "intermediate_steps_latex": steps_latex,
            "steps_meta": steps_meta,
            "verification_steps_latex": verification_steps_latex,
            "back_substitution_steps": result.get("back_substitution_steps", []),
            "variables": vars_list,
            "n_vars": _n,
            "steps_view": steps_view,
            "groups": groups,
            "stats": stats,
        }

        def _serializador(obj):
            if hasattr(obj, "numerator") and hasattr(obj, "denominator"):
                return str(obj)
            return str(obj)

        return json.dumps(response, default=_serializador, ensure_ascii=False)

    # Alias canónico en castellano
    procesar_sistema = process_system