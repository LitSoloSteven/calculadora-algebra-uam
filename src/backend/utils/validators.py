from src.backend.models.matrix import Matrix
from fractions import Fraction
from typing import Any

class MatrixValidator:
    @staticmethod
    def parse_number(val: Any) -> tuple[bool, float, str]:
        if isinstance(val, (int, float)):
            return True, float(val), ""
        
        if isinstance(val, str):
            val_clean = val.strip()
            if not val_clean:
                return False, 0.0, "El campo está vacío."
            try:
                # Fraction maneja '1/3', '-5/2', '0.5', '4', etc.
                parsed_val = float(Fraction(val_clean))
                return True, parsed_val, ""
            except ValueError:
                return False, 0.0, f"'{val}' no es una fracción o número válido."
                
        return False, 0.0, "Tipo de dato no soportado."

    @staticmethod
    def validate_dimensions(rows: int, cols: int) -> tuple[bool, str]:
        if not isinstance(rows, int) or not isinstance(cols, int):
            return False, "Las dimensiones deben ser números enteros."
        if rows <= 0 or cols <= 0:
            return False, "El número de filas y columnas debe ser mayor a 0."
        return True, "Dimensiones válidas."

    @staticmethod
    def validate_matrix_data(data: list[list[float]], expected_rows: int, expected_cols: int) -> tuple[bool, str]:
        if len(data) != expected_rows:
            return False, f"Se esperaban {expected_rows} filas, pero se recibieron {len(data)}."
        for i, row in enumerate(data):
            if len(row) != expected_cols:
                return False, f"La fila {i} tiene {len(row)} columnas; se esperaban {expected_cols}."
        return True, "Datos matriciales estructurados correctamente."

    @staticmethod
    def validate_and_parse_raw_matrix(raw_data: list[list[Any]], expected_rows: int, expected_cols: int) -> tuple[bool, list[list[float]], str]:
        if len(raw_data) != expected_rows:
            return False, [], f"Se esperaban {expected_rows} filas, pero hay {len(raw_data)}."
        
        parsed_matrix = []
        for r_idx, row in enumerate(raw_data):
            if len(row) != expected_cols:
                return False, [], f"La fila {r_idx + 1} no tiene {expected_cols} columnas."
            
            parsed_row = []
            for c_idx, item in enumerate(row):
                success, num_float, err_msg = MatrixValidator.parse_number(item)
                if not success:
                    return False, [], f"Error en celda [{r_idx + 1}, {c_idx + 1}]: {err_msg}"
                parsed_row.append(num_float)
                
            parsed_matrix.append(parsed_row)

        return True, parsed_matrix, "Matriz parseada correctamente."

    @staticmethod
    def is_augmented_system(matrix: Matrix) -> bool:
        return matrix.cols == matrix.rows + 1

    @staticmethod
    def verify_solution(
        A: list[list[Any]], 
        x: list[Any], 
        b: list[Any],
        as_latex: bool = False,
        tolerance: float = 1e-4
    ) -> tuple[bool, list[str]]:
        is_valid = True
        report = []

        for i in range(len(A)):
            lhs = 0.0 
            terms = []

            for j in range(len(x)):
                coeff = float(A[i][j])
                var_val = float(x[j])
                prod = coeff * var_val
                lhs += prod
                
                if as_latex:
                    terms.append(rf"\left({coeff}\right) \cdot \left({var_val}\right)")
                else:
                    terms.append(f"({coeff})·({var_val})")

            rhs = float(b[i])
            
            # Se evalúa la igualdad utilizando un margen de tolerancia
            is_eq_correct = abs(lhs - rhs) < tolerance
            
            # Para la representación visual, se redondea lhs
            lhs_display = round(lhs, 6)
            
            if as_latex:
                substitution_str = " + ".join(terms)
                status_text = r"\text{Correcto}" if is_eq_correct else r"\text{Incorrecto}"
                report.append(rf"Ecuación {i + 1}: {substitution_str} = {lhs_display} \quad ({status_text})")
            else:
                substitution_str = " + ".join(terms)
                status_text = "Correcto" if is_eq_correct else "Incorrecto"
                report.append(f"Ecuación {i + 1}: {substitution_str} = {lhs_display}  {status_text} (b_{i + 1} = {rhs})")

            if not is_eq_correct:
                is_valid = False

        return is_valid, report