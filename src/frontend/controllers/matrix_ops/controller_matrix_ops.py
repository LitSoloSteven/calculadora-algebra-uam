import json
from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator
from src.backend.utils.validators import MatrixValidator


class MatrixEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Matrix):
            return {"rows": obj.rows, "cols": obj.cols, "data": obj.data}
        if isinstance(obj, Fraction):
            return float(obj) if obj.denominator != 1 else obj.numerator
        return super().default(obj)


class MatrixOpsController:

    @staticmethod
    def _build_matrices(matrices_data):
        """Valida y construye las matrices del payload con mensajes contextuales.

        Cada celda pasa por parse_number_exact, preservando precisión exacta.
        Los errores de shape se reportan con el nombre de la matriz y la
        coordenada/campo exacto que falló.
        """
        if not isinstance(matrices_data, dict):
            raise ValueError("El payload debe contener un diccionario de matrices.")
        if not matrices_data:
            raise ValueError("No se recibió ninguna matriz para evaluar.")

        matrices = {}
        for name, mat_data in matrices_data.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Cada matriz debe tener un nombre no vacío.")
            if not isinstance(mat_data, dict):
                raise ValueError(
                    f"Matriz '{name}': se esperaba un objeto con rows/cols/data."
                )

            rows = mat_data.get("rows")
            cols = mat_data.get("cols")
            data = mat_data.get("data")

            if not isinstance(rows, int) or rows <= 0:
                raise ValueError(
                    f"Matriz '{name}': 'rows' debe ser un entero positivo."
                )
            if not isinstance(cols, int) or cols <= 0:
                raise ValueError(
                    f"Matriz '{name}': 'cols' debe ser un entero positivo."
                )
            if not isinstance(data, list):
                raise ValueError(
                    f"Matriz '{name}': 'data' debe ser una lista de filas."
                )
            if len(data) != rows:
                raise ValueError(
                    f"Matriz '{name}': 'data' tiene {len(data)} filas; "
                    f"se esperaban {rows}."
                )

            parsed_data = []
            for i, row in enumerate(data):
                if not isinstance(row, list):
                    raise ValueError(
                        f"Matriz '{name}': fila {i + 1} no es una lista."
                    )
                if len(row) != cols:
                    raise ValueError(
                        f"Matriz '{name}': fila {i + 1} tiene {len(row)} columnas; "
                        f"se esperaban {cols}."
                    )
                parsed_row = []
                for j, raw in enumerate(row):
                    val_str = (
                        str(raw).strip()
                        if raw is not None and str(raw).strip()
                        else '0'
                    )
                    ok, val, err = MatrixValidator.parse_number_exact(val_str)
                    if not ok:
                        raise ValueError(
                            f"Matriz {name}, celda [{i + 1},{j + 1}]: {err}"
                        )
                    parsed_row.append(val)
                parsed_data.append(parsed_row)

            # Matrix ya valida shape internamente, pero pasamos por su
            # constructor para que la normalización de celdas ocurra una sola vez.
            matrices[name] = Matrix(rows=rows, cols=cols, data=parsed_data)

        return matrices

    @staticmethod
    def process_expression(expresion_str: str, matrices_dict_json: str) -> str:
        # --- 1. JSON ---
        try:
            matrices_data = json.loads(matrices_dict_json)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "ERROR",
                "message": (
                    f"Payload JSON malformado: {e.msg} "
                    f"(línea {e.lineno}, columna {e.colno})."
                )
            }, ensure_ascii=False)

        # --- 2. Validación explícita del payload ---
        try:
            matrices = MatrixOpsController._build_matrices(matrices_data)
        except ValueError as e:
            return json.dumps({
                "status": "ERROR",
                "message": str(e)
            }, ensure_ascii=False)

        # --- 3. Evaluación de la expresión ---
        # El evaluador ya devuelve dicts de error para problemas esperados.
        # Este catch es solo para tipos de excepción que el evaluador no
        # documenta: preferimos un error de dominio a un 500.
        try:
            evaluator = MatrixExpressionEvaluator()
            resultado = evaluator.evaluate(expresion_str, matrices)
        except (ValueError, ZeroDivisionError, TypeError) as e:
            return json.dumps({
                "status": "ERROR",
                "message": f"Error al evaluar la expresión ({type(e).__name__}): {e}"
            }, ensure_ascii=False)

        # --- 4. Serialización ---
        try:
            return json.dumps(resultado, ensure_ascii=False, cls=MatrixEncoder)
        except (TypeError, ValueError) as e:
            return json.dumps({
                "status": "ERROR",
                "message": f"Error al serializar el resultado: {e}"
            }, ensure_ascii=False)