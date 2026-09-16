import json
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.utils.formatters import matrix_to_latex
from src.backend.utils.validators import MatrixValidator

class MatrixController:
    @staticmethod
    def process_system(json_payload: str) -> str:
        try:
            data = json.loads(json_payload)
            matrix_A_raw = data.get("matrix_A", [])
            vector_b_raw = data.get("vector_b", [])

            m = len(matrix_A_raw)
            if m == 0:
                return json.dumps({"status": "error", "message": "La matriz está vacía."})
            n = len(matrix_A_raw[0])

            # Construir la matriz aumentada [A | b] usando MatrixValidator
            augmented_data = []
            for i in range(m):
                fila = []
                for j in range(n):
                    val_str = matrix_A_raw[i][j].strip() if matrix_A_raw[i][j] else '0'
                    success, val, err = MatrixValidator.parse_number(val_str)
                    if not success:
                        return json.dumps({"status": "error", "message": f"Error en A[{i+1},{j+1}]: {err}"})
                    fila.append(val)
                
                b_val_str = vector_b_raw[i].strip() if i < len(vector_b_raw) and vector_b_raw[i] else '0'
                success, b_val, err = MatrixValidator.parse_number(b_val_str)
                if not success:
                    return json.dumps({"status": "error", "message": f"Error en b[{i+1}]: {err}"})
                fila.append(b_val)
                
                augmented_data.append(fila)

            augmented_matrix = Matrix(rows=m, cols=n + 1, data=augmented_data)
            solver = GaussSolver(augmented_matrix)
            result = solver.solve()

            # Mapear los pasos intermedios de las matrices a formato LaTeX para la UI
            intermediate_steps_latex = []
            for step in result.get("steps", []):
                intermediate_steps_latex.append({
                    "descripcion": step["description"],
                    "matriz": matrix_to_latex(step["matrix"])
                })

            # Generar los pasos de comprobación reutilizando MatrixValidator.verify_solution
            verification_steps_latex = []
            solution = result.get("solution")
            if solution and result.get("status") == "UNIQUE_SOLUTION":
                A_vals = [[augmented_data[i][j] for j in range(n)] for i in range(m)]
                b_vals = [augmented_data[i][n] for i in range(m)]
                
                x_vals = []
                for s in solution:
                    try:
                        x_vals.append(float(Fraction(str(s))))
                    except Exception:
                        x_vals.append(0.0)

                _, verification_steps_latex = MatrixValidator.verify_solution(
                    A=A_vals,
                    x=x_vals,
                    b=b_vals,
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

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error interno en el controlador: {str(e)}"
            })