import json
from fractions import Fraction

from src.backend.exceptions import MatrixDataError
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver
from src.backend.utils.formatters import matrix_to_latex
from src.backend.utils.validators import MatrixValidator


class GaussJordanController:
    @staticmethod
    def process_system(json_payload: str) -> str:
        try:
            data = json.loads(json_payload)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "error",
                "message": f"Payload JSON malformado: {e.msg} (línea {e.lineno}, columna {e.colno})."
            })
        if not isinstance(data, dict):
            return json.dumps({
                "status": "error",
                "message": "El payload debe ser un objeto JSON con 'matrix_A' y 'vector_b'."
            })

        matrix_A_raw = data.get("matrix_A", [])
        vector_b_raw = data.get("vector_b", [])
        variables = data.get("variables")

        # --- 1. Validación de forma ---
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

        if len(vector_b_raw) != m:
            return json.dumps({
                "status": "error",
                "message": (
                    f"El vector b tiene {len(vector_b_raw)} valores; "
                    f"se esperaban {m} (uno por fila de A)."
                )
            })

# --- 2. Conversión a Fraction con contexto de celda en errores ---
        A_fractions = []
        for i, row in enumerate(matrix_A_raw):
            fila_frac = []
            for j, cell in enumerate(row):
                raw = str(cell).strip() if cell is not None and str(cell).strip() else '0'
                ok, val, err = MatrixValidator.parse_number_exact(raw)
                if not ok:
                    return json.dumps({
                        "status": "error",
                        "message": f"Error en A[{i+1},{j+1}]: {err}"
                    })
                fila_frac.append(val)
            A_fractions.append(fila_frac)

        b_fractions = []
        for i, cell in enumerate(vector_b_raw):
            raw = str(cell).strip() if cell is not None and str(cell).strip() else '0'
            ok, val, err = MatrixValidator.parse_number_exact(raw)
            if not ok:
                return json.dumps({
                    "status": "error",
                    "message": f"Error en b[{i+1}]: {err}"
                })
            b_fractions.append(val)

        # --- 3. Ejecución del solver ---
        try:
            augmented_data = [
                A_fractions[i] + [b_fractions[i]]
                for i in range(m)
            ]
            matriz_aumentada = Matrix(m, n + 1, augmented_data)
        except MatrixDataError as e:
            return json.dumps({"status": "error", "message": f"Datos inválidos: {e}"})

        solver = GaussJordanSolver(matriz_aumentada, variable_names=variables)
        resultado = solver.solve()

        clasificacion = resultado.get("message", "")
        solucion = resultado.get("solution")

        pasos_latex = []
        for paso in resultado.get("steps", []):
            pasos_latex.append({
                "descripcion": paso["description"],
                "matriz": matrix_to_latex(paso["matrix"])
            })

        reporte_comprobacion = []
        if resultado.get("status") == "UNIQUE_SOLUTION":
            _, reporte_comprobacion = MatrixValidator.verify_solution(
                A_fractions, solucion, b_fractions, as_latex=True
            )

        response = {
            "status": resultado.get("status"),
            "classification": clasificacion,
            "message": clasificacion,
            "solution": [str(x) for x in solucion] if solucion else [],
            "intermediate_steps_latex": pasos_latex,
            "verification_steps_latex": reporte_comprobacion,
            "back_substitution_steps": resultado.get("back_substitution_steps", [])
        }

        return json.dumps(response, ensure_ascii=False)