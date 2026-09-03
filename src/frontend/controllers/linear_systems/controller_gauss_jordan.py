import json
from fractions import Fraction
from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver
from src.backend.utils.validators import MatrixValidator
from src.backend.utils.formatters import matrix_to_latex
from src.backend.models.matrix import Matrix

class GaussJordanController:
    @staticmethod
    def process_system(json_payload: str) -> str:
        data = json.loads(json_payload)
        
        try:
            A_fractions = [[Fraction(cell) for cell in row] for row in data["matrix_A"]]
            b_fractions = [Fraction(val) for val in data["vector_b"]]
        except ValueError as e:
            return json.dumps({"status": "error", "message": f"Error en los datos: {e}"})

        augmented_data = []
        for i in range(len(A_fractions)):
            augmented_data.append(A_fractions[i] + [b_fractions[i]])
            
        matriz_aumentada = Matrix(len(A_fractions), len(A_fractions[0]) + 1, augmented_data)
        
        solver = GaussJordanSolver(matriz_aumentada)
        resultado = solver.solve()

        clasificacion = resultado["message"]
        solucion = resultado["solution"]
        
        pasos_latex = []
        for paso in resultado["steps"]:
            pasos_latex.append({
                "descripcion": paso["description"], 
                "matriz": matrix_to_latex(paso["matrix"])
            })

        reporte_comprobacion = []
        if clasificacion == "Sistema Consistente Determinado: Presenta Solución Única.":
            _, reporte_comprobacion = MatrixValidator.verify_solution(
                A_fractions, solucion, b_fractions, as_latex=True
            )

        response = {
            "status": "success",
            "classification": clasificacion,
            "solution": [str(x) for x in solucion] if solucion else [],
            "intermediate_steps_latex": pasos_latex,
            "verification_steps_latex": reporte_comprobacion,
            "back_substitution_steps": resultado.get("back_substitution_steps", [])
        }
        
        return json.dumps(response, ensure_ascii=False)