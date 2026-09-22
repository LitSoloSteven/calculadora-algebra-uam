import json

from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver
from src.backend.utils.formatters import matrix_to_latex
from src.backend.utils.validators import MatrixValidator
from src.frontend.controllers.linear_systems._shared import (
    parse_payload,
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
        solver = GaussJordanSolver(matrix, variable_names=variables)
        result = solver.solve()

        classification = result.get("message", "")
        solution = result.get("solution")

        steps_latex = []
        for step in result.get("steps", []):
            steps_latex.append({
                "descripcion": step["description"],
                "matriz": matrix_to_latex(step["matrix"])
            })

        verification_steps_latex = []
        if result.get("status") == "UNIQUE_SOLUTION":
            _, verification_steps_latex = MatrixValidator.verify_solution(
                A_fractions, solution, b_fractions, as_latex=True
            )

        response = {
            "status": result.get("status"),
            "classification": classification,
            "message": classification,
            "solution": [str(x) for x in solution] if solution else [],
            "intermediate_steps_latex": steps_latex,
            "verification_steps_latex": verification_steps_latex,
            "back_substitution_steps": result.get("back_substitution_steps", [])
        }

        return json.dumps(response, ensure_ascii=False)