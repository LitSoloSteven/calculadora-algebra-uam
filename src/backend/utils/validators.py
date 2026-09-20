from src.backend.models.matrix import Matrix
from fractions import Fraction
from typing import Any
from src.backend.constants import SOLUTION_VERIFICATION_TOLERANCE
from src.backend.exceptions import DimensionMismatchError

class MatrixValidator:
    @staticmethod
    def parse_number_exact(val: Any) -> tuple[bool, Fraction, str]:
        """Parsea un valor numérico y lo devuelve como Fraction exacto."""
        if isinstance(val, (int, Fraction)):
            return True, Fraction(val), ""

        if isinstance(val, float):
            try:
                return True, Fraction(val).limit_denominator(10**6), ""
            except (ValueError, OverflowError):
                # Fallback: parsear la representación decimal como string.
                try:
                    return True, Fraction(str(val)), ""
                except (ValueError, ZeroDivisionError):
                    return False, Fraction(0), "Valor flotante no convertible a fracción."

        if isinstance(val, str):
            val_clean = val.strip()
            if not val_clean:
                return False, Fraction(0), "El campo está vacío."
            try:
                return True, Fraction(val_clean), ""
            except ZeroDivisionError:
                return False, Fraction(0), "División por cero en la fracción ingresada."
            except ValueError:
                return False, Fraction(0), "El valor ingresado no es un número o fracción válida."

        return False, Fraction(0), "Tipo de dato no soportado."

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
    def validate_and_parse_raw_matrix(raw_data: list[list[Any]], expected_rows: int, expected_cols: int) -> tuple[bool, list[list[Fraction]], str]:
        if len(raw_data) != expected_rows:
            return False, [], f"Se esperaban {expected_rows} filas, pero hay {len(raw_data)}."
        
        parsed_matrix = []
        for r_idx, row in enumerate(raw_data):
            if len(row) != expected_cols:
                return False, [], f"La fila {r_idx + 1} no tiene {expected_cols} columnas."
            
            parsed_row = []
            for c_idx, item in enumerate(row):
                # parse_number_exact preserva denominadores > 1000 que el
                # float intermedio perdería antes de llegar a Matrix.
                success, num_frac, err_msg = MatrixValidator.parse_number_exact(item)
                if not success:
                    return False, [], f"Error en celda [{r_idx + 1}, {c_idx + 1}]: {err_msg}"
                parsed_row.append(num_frac)
                
            parsed_matrix.append(parsed_row)

        return True, parsed_matrix, "Matriz parseada correctamente."

    @staticmethod
    def validate_variable_coherence(parsed_equations: list[tuple[dict[str, float], float]]) -> tuple[bool, str]:
        """
        Verifica que las ecuaciones estén interrelacionadas y no formen sistemas disjuntos o inconexos.
        """
        if len(parsed_equations) <= 1:
            return True, "Coherencia de variables válida."

        for idx, (eq_coeffs, _) in enumerate(parsed_equations, 1):
            eq_vars = set(eq_coeffs.keys())
            other_vars = set().union(*[e[0].keys() for i, e in enumerate(parsed_equations) if i != idx - 1])
            
            # Si una ecuación no comparte ninguna variable con el resto del sistema
            if not eq_vars.intersection(other_vars):
                return False, (
                    f"Línea {idx}: Las variables {sorted(list(eq_vars))} "
                    f"no tienen relación ni comparten columnas con el resto de ecuaciones."
                )

        return True, "Coherencia de variables válida."

    @staticmethod
    def _to_float(val: Any) -> float:
        """Convierte a float aceptando int, float, Fraction y strings
        con formato de fracción ('229/50', '1/2', '3', '2.5').

        Si el string no es parseable, devuelve 0.0 (mismo comportamiento
        que el controller de Gauss tenía para casos irrecuperables)."""
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, Fraction):
            return float(val)
        try:
            return float(Fraction(str(val).strip()))
        except (ValueError, ZeroDivisionError):
            return 0.0
        
    @staticmethod
    def _to_fraction(val: Any) -> Fraction:
        """Convierte a Fraction para display, tolerante a tipos mixtos
        (int, float, Fraction, str tipo '9/7' o '1.5'). Delega en
        parse_number_exact para no duplicar reglas de parsing."""
        ok, frac, _ = MatrixValidator.parse_number_exact(val)
        return frac if ok else Fraction(0)

    @staticmethod
    def verify_solution(
        A: list[list[Any]],
        x: list[Any],
        b: list[Any],
        as_latex: bool = False,
        tolerance: float = SOLUTION_VERIFICATION_TOLERANCE
    ) -> tuple[bool, list[str]]:
        from src.backend.utils.formatters import format_fraction_str, number_to_latex

        is_valid = True
        report = []

        for i in range(len(A)):
            lhs = 0.0
            terms = []

            for j in range(len(x)):
                # Cálculo: float con tolerancia (contrato actual, no cambia).
                coeff_f = MatrixValidator._to_float(A[i][j])
                var_f = MatrixValidator._to_float(x[j])
                lhs += coeff_f * var_f

                # Display: representación exacta cuando sea posible.
                coeff_disp = MatrixValidator._to_fraction(A[i][j])
                var_disp = MatrixValidator._to_fraction(x[j])

                if as_latex:
                    c_tex = number_to_latex(coeff_disp)
                    v_tex = number_to_latex(var_disp)
                    terms.append(rf"\left({c_tex}\right) \cdot \left({v_tex}\right)")
                else:
                    c_str = format_fraction_str(coeff_disp)
                    v_str = format_fraction_str(var_disp)
                    terms.append(f"({c_str})·({v_str})")

            rhs = MatrixValidator._to_float(b[i])
            is_eq_correct = abs(lhs - rhs) < tolerance

            # Limpiar el LHS para display: entero si aplica (2 en vez de 2.0),
            # sino 6 decimales redondeados.
            lhs_display = round(lhs, 6)
            if lhs_display == int(lhs_display):
                lhs_display = int(lhs_display)

            b_disp = MatrixValidator._to_fraction(b[i])
            b_str = format_fraction_str(b_disp)
            b_tex = number_to_latex(b_disp)

            if as_latex:
                substitution_str = " + ".join(terms)
                status_text = r"\text{Correcto}" if is_eq_correct else r"\text{Incorrecto}"
                report.append(
                    rf"Ecuación {i + 1}: {substitution_str} = {lhs_display} \quad "
                    rf"({status_text}, \; b_{{{i + 1}}} = {b_tex})"
                )
            else:
                substitution_str = " + ".join(terms)
                status_text = "Correcto" if is_eq_correct else "Incorrecto"
                report.append(
                    f"Ecuación {i + 1}: {substitution_str} = {lhs_display}  "
                    f"{status_text} (b_{i + 1} = {b_str})"
                )
            if not is_eq_correct:
                is_valid = False

        return is_valid, report
    
    @staticmethod
    def validate_raw_data(raw_data: Any) -> tuple[bool, str]:
        if raw_data is None:
            return False, "Los datos de la matriz no pueden ser nulos."
        if isinstance(raw_data, list) and len(raw_data) == 0:
            return False, "La matriz no puede estar vacía."
        return True, "Datos válidos."
    

def validate_same_dimensions(matrix_a: Matrix, matrix_b: Matrix) -> None:
    """
    Valida que dos matrices tengan exactamente las mismas dimensiones (m x n)
    para operaciones de suma y resta.
    """
    if matrix_a.rows != matrix_b.rows or matrix_a.cols != matrix_b.cols:
        raise DimensionMismatchError(
            operation="suma/resta",
            shape_a=(matrix_a.rows, matrix_a.cols),
            shape_b=(matrix_b.rows, matrix_b.cols),
        )


def validate_multiplication_dimensions(matrix_a: Matrix, matrix_b: Matrix) -> None:
    """
    Valida que el número de columnas de A (n) sea igual al número de filas de B (p).
    La matriz resultante tendrá tamaño (m x q).
    """
    if matrix_a.cols != matrix_b.rows:
        raise DimensionMismatchError(
            operation="multiplicación (A.cols debe igualar B.rows)",
            shape_a=(matrix_a.rows, matrix_a.cols),
            shape_b=(matrix_b.rows, matrix_b.cols),
        )