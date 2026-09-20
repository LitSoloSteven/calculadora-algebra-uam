import json

from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.utils.formatters import matrix_to_latex
from src.backend.utils.validators import MatrixValidator
from src.frontend.controllers.linear_systems._shared import (
    parse_payload,
    validate_and_build_augmented,
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
        result = solver.solve()

        # --- Formateo de la respuesta ---
        intermediate_steps_latex = []
        for step in result.get("steps", []):
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
            "intermediate_steps_latex": intermediate_steps_latex,
            "back_substitution_steps": result.get("back_substitution_steps", []),
            "verification_steps_latex": verification_steps_latex
        }

        return json.dumps(response_payload)