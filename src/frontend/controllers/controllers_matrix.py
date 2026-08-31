import json
from fractions import Fraction

from src.backend.solvers.linear_systems import GaussSolver
from src.backend.utils.validators import MatrixValidator
from src.backend.utils.formatters import matrix_to_latex
from src.backend.models.matrix import Matrix

class MatrixController:
    @staticmethod
    def process_system(json_payload: str) -> str:
        """
        Recibe un JSON del frontend (NiceGUI), procesa el sistema de ecuaciones
        y devuelve un JSON con resultados y pasos formateados en LaTeX.
        """
        data = json.loads(json_payload)
        
        try:
            # 1. Parseo estricto a Fraction para cumplir los requerimientos sin librerías externas
            A_fractions = [[Fraction(cell) for cell in row] for row in data["matrix_A"]]
            b_fractions = [Fraction(val) for val in data["vector_b"]]
        except ValueError as e:
            return json.dumps({
                "status": "error",
                "message": f"Error en los datos de entrada: Asegúrate de ingresar números válidos o fracciones. ({e})"
            })

        # 2. Construir matriz aumentada y ejecutar el Solver
        augmented_data = []
        for i in range(len(A_fractions)):
            augmented_data.append(A_fractions[i] + [b_fractions[i]])
            
        matriz_aumentada = Matrix(len(A_fractions), len(A_fractions[0]) + 1, augmented_data)
        
        solver = GaussSolver(matriz_aumentada)
        resultado = solver.solve() # Retorna un diccionario

        # Extraer los datos del diccionario
        clasificacion = resultado["message"]
        solucion = resultado["solution"]
        matrices_intermedias = [paso["matrix"] for paso in resultado["steps"]]

        # 3. Preparar los pasos intermedios en LaTeX para la UI
        pasos_latex = []
        for paso in resultado["steps"]:
            pasos_latex.append({
                "descripcion": paso["description"], 
                "matriz": matrix_to_latex(paso["matrix"])
            })

        # 4. Validar y generar el reporte de comprobación Ax = b (si hay solución única)
        reporte_comprobacion = []
        if clasificacion == "Sistema Consistente Determinado: Presenta Solución Única.":
            # Usamos as_latex=True como configuramos en el validador
            _, reporte_comprobacion = MatrixValidator.verify_solution(
                A_fractions, solucion, b_fractions, as_latex=True
            )

        # 5. Construir y retornar la respuesta JSON
        response = {
            "status": "success",
            "classification": clasificacion,
            "solution": [str(x) for x in solucion] if solucion else [],
            "intermediate_steps_latex": pasos_latex,
            "verification_steps_latex": reporte_comprobacion
        }
        
        return json.dumps(response, ensure_ascii=False)