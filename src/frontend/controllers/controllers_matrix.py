import json
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems import GaussSolver
from src.backend.utils.formatters import matrix_to_latex

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

            # Construir la matriz aumentada [A | b] soportando fracciones, enteros y decimales
            augmented_data = []
            for i in range(m):
                fila = []
                for j in range(n):
                    val_str = matrix_A_raw[i][j].strip() if matrix_A_raw[i][j] else '0'
                    try:
                        fila.append(float(Fraction(val_str)))
                    except Exception:
                        fila.append(0.0)
                
                b_val_str = vector_b_raw[i].strip() if i < len(vector_b_raw) and vector_b_raw[i] else '0'
                try:
                    fila.append(float(Fraction(b_val_str)))
                except Exception:
                    fila.append(0.0)
                
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

            # Generar los pasos de comprobación si se obtuvo una solución única
            verification_steps_latex = []
            solution = result.get("solution")
            if solution and result.get("status") == "UNIQUE_SOLUTION":
                for i in range(len(matrix_A_raw)):
                    terms = []
                    row_sum = 0.0
                    for j in range(n):
                        val_str = matrix_A_raw[i][j].strip() if matrix_A_raw[i][j] else '0'
                        coeff = float(Fraction(val_str)) if val_str != '' else 0.0
                        x_val = solution[j]
                        row_sum += coeff * x_val
                        terms.append(f"({coeff:.1f}) \\cdot ({x_val:.1f})")
                    
                    b_val_str = vector_b_raw[i].strip() if i < len(vector_b_raw) and vector_b_raw[i] else '0'
                    b_val = float(Fraction(b_val_str)) if b_val_str != '' else 0.0
                    
                    expr_str = " + ".join(terms)
                    is_correct = abs(row_sum - b_val) < 1e-4
                    correct_label = "Correcto" if is_correct else "Incorrecto"
                    verification_steps_latex.append(f"Ecuación_{{ {i+1} }} : {expr_str} = {row_sum:.1f} \\quad \\text{{({correct_label})}}")

            response_payload = {
                "status": result.get("status"),
                "classification": result.get("message"),
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