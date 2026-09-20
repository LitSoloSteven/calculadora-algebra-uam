import json
from fractions import Fraction
from src.backend.exceptions import MatrixDataError
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.utils.formatters import matrix_to_latex
from src.backend.utils.validators import MatrixValidator


class MatrixController:
    @staticmethod
    def process_system(json_payload: str) -> str:
        try:
            data = json.loads(json_payload)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "error",
                "message": f"Payload JSON malformado: {e.msg} (línea {e.lineno}, columna {e.colno})."
            })

        matrix_A_raw = data.get("matrix_A", [])
        vector_b_raw = data.get("vector_b", [])
        variables = data.get("variables")

        # --- 1. Validación de forma del payload ---
        m = len(matrix_A_raw)
        if m == 0:
            return json.dumps({"status": "error", "message": "La matriz A está vacía."})

        if not isinstance(matrix_A_raw[0], list):
            return json.dumps({"status": "error", "message": "La matriz A debe ser una lista de filas."})

        n = len(matrix_A_raw[0])
        if n == 0:
            return json.dumps({"status": "error", "message": "La matriz A no puede tener 0 columnas."})

        valid_shape, msg_shape = MatrixValidator.validate_matrix_data(matrix_A_raw, m, n)
        if not valid_shape:
            return json.dumps({"status": "error", "message": msg_shape})

        # vector_b debe coincidir EXACTAMENTE en longitud con las filas de A.
        # Rellenar con 0 ante un faltante es una falla silenciosa: el usuario
        # vería la solución de un sistema distinto al que ingresó.
        if len(vector_b_raw) != m:
            return json.dumps({
                "status": "error",
                "message": (
                    f"El vector b tiene {len(vector_b_raw)} valores; "
                    f"se esperaban {m} (uno por fila de A)."
                )
            })

        # --- 2. Construcción de la matriz aumentada [A | b] ---
        augmented_data = []
        for i in range(m):
            fila = []
            for j in range(n):
                raw = matrix_A_raw[i][j]
                val_str = str(raw).strip() if raw is not None and str(raw).strip() else '0'
                success, val, err = MatrixValidator.parse_number_exact(val_str)
                if not success:
                    return json.dumps({
                        "status": "error",
                        "message": f"Error en A[{i+1},{j+1}]: {err}"
                    })
                fila.append(val)

            raw_b = vector_b_raw[i]
            b_val_str = str(raw_b).strip() if raw_b is not None and str(raw_b).strip() else '0'
            success, b_val, err = MatrixValidator.parse_number_exact(b_val_str)
            if not success:
                return json.dumps({
                    "status": "error",
                    "message": f"Error en b[{i+1}]: {err}"
                })
            fila.append(b_val)

            augmented_data.append(fila)

        # --- 3. Ejecución del solver ---
        try:
            augmented_matrix = Matrix(rows=m, cols=n + 1, data=augmented_data)
        except MatrixDataError as e:
            return json.dumps({"status": "error", "message": f"Datos inválidos: {e}"})

        solver = GaussSolver(augmented_matrix, variable_names=variables)
        result = solver.solve()

        # --- 4. Formateo de la respuesta ---
        intermediate_steps_latex = []
        for step in result.get("steps", []):
            intermediate_steps_latex.append({
                "descripcion": step["description"],
                "matriz": matrix_to_latex(step["matrix"])
            })

        verification_steps_latex = []
        solution = result.get("solution")
        if solution and result.get("status") == "UNIQUE_SOLUTION":
            A_vals = [[augmented_data[i][j] for j in range(n)] for i in range(m)]
            b_vals = [augmented_data[i][n] for i in range(m)]

            x_vals = []
            for s in solution:
                try:
                    x_vals.append(float(Fraction(str(s))))
                except (ValueError, ZeroDivisionError):
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
