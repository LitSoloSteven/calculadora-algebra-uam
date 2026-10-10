import json

from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.matrix_ops.formatters import matrix_to_latex
from src.backend.utils.validators import MatrixValidator
from src.frontend.controllers.linear_systems._shared import (
    parse_payload,
    validate_and_build_augmented,
    build_steps_meta,
)


class MatrixController:
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
        solver = GaussSolver(matrix, variable_names=variables)
        result = solver.resolver()

        # --- Formateo de la respuesta ---
        raw_steps = result.get("steps", [])
        steps_meta = build_steps_meta(raw_steps)
        intermediate_steps_latex = []
        for step in raw_steps:
            intermediate_steps_latex.append({
                "descripcion": step["description"],
                "matriz": matrix_to_latex(step["matrix"])
            })

        verification_steps_latex = []
        solution = result.get("solution")
        if solution and result.get("status") == "UNIQUE_SOLUTION":
            _, verification_steps_latex = MatrixValidator.verify_solution(
                A=A_fractions,
                x=solution,
                b=b_fractions,
                as_latex=True
            )

        response_payload = {
            "status": result.get("status"),
            "classification": result.get("message"),
            "message": result.get("message"),
            "solution": solution,
            "solution_param": result.get("solution_param"),
            "analisis_sistema": result.get("analisis_sistema"),
            "intermediate_steps_latex": intermediate_steps_latex,
            "steps_meta": steps_meta,
            "back_substitution_steps": result.get("back_substitution_steps", []),
            "verification_steps_latex": verification_steps_latex
        }

        return json.dumps(response_payload, ensure_ascii=False, default=str)

    # Alias canónico en castellano
    procesar_sistema = process_system