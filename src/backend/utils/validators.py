from src.backend.models.matrix import Matrix
from fractions import Fraction
from typing import Any
from src.backend.constants import SOLUTION_VERIFICATION_TOLERANCE
from src.backend.exceptions import DimensionMismatchError

class MatrixValidator:
    @staticmethod
    def parse_number_exact(val: Any) -> tuple[bool, Fraction, str]:
        """Parsea un valor numérico y lo devuelve como Fraction exacto.
        Uso interno del backend, donde la precisión exacta es requerida
        (parsers de sistemas, controllers de métodos lineales). Para el frontend, usar parse_number (devuelve float, serializable a JSON).
        """
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
    def parse_number(val: Any) -> tuple[bool, float, str]:
        """Versión compatible con el frontend: devuelve float (JSON-serializable).

        Delega la validación y el parsing en parse_number_exact para tener
        una sola fuente de verdad de los mensajes de error y reglas de
        aceptación. Solo convierte el resultado final a float.
        """
        ok, frac, msg = MatrixValidator.parse_number_exact(val)
        if not ok:
            return False, 0.0, msg
        return True, float(frac), ""

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
    def validate_variable_coherence(parsed_equations: list[tuple[dict[str, Fraction], Fraction]]) -> tuple[bool, str]:
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
    def _to_fraction_strict(val: Any) -> tuple[bool, Fraction, str]:
        """Convierte a Fraction para verificación exacta.
        A diferencia de _to_fraction (que silencia errores), esta versión
        reporta fallas para que verify_solution pueda rechazar entradas
        no parseables en vez de tratarlas como 0."""
        if isinstance(val, Fraction):
            return True, val, ""
        if isinstance(val, int):
            return True, Fraction(val), ""
        if isinstance(val, float):
            try:
                return True, Fraction(val).limit_denominator(10**6), ""
            except (ValueError, OverflowError):
                return False, Fraction(0), f"Float no convertible: {val!r}"
        if isinstance(val, str):
            val_clean = val.strip()
            if not val_clean:
                return False, Fraction(0), "El campo está vacío."
            try:
                return True, Fraction(val_clean), ""
            except ZeroDivisionError:
                return False, Fraction(0), "División por cero."
            except ValueError:
                return False, Fraction(0), f"'{val}' no es un número o fracción válida."
        return False, Fraction(0), f"Tipo no soportado: {type(val).__name__}"

    @staticmethod
    def _to_fraction(val: Any) -> Fraction:
        """Versión tolerante (mantiene comportamiento previo para display).
        Para verificación exacta usar _to_fraction_strict."""
        ok, frac, _ = MatrixValidator.parse_number_exact(val)
        return frac if ok else Fraction(0)

    @staticmethod
    def verify_solution(
        A: list[list[Any]],
        x: list[Any],
        b: list[Any],
        as_latex: bool = False,
    ) -> tuple[bool, list[str]]:
        """Verifica Ax = b con aritmética exacta de Fraction.

        Devuelve (es_valida, reporte). Si alguna celda de A, x o b no es
        parseable, la verificación falla con mensaje de error en vez de
        asumir 0.0 (falla silenciosa).
        """
        from src.backend.utils.formatters import format_fraction_str, number_to_latex

        is_valid = True
        report = []

        # --- 0. Pre-parseo estricto: detectar celdas inválidas antes de calcular ---
        A_frac: list[list[Fraction]] = []
        for i, row in enumerate(A):
            fila: list[Fraction] = []
            for j, cell in enumerate(row):
                ok, frac, err = MatrixValidator._to_fraction_strict(cell)
                if not ok:
                    return False, [f"Error en A[{i + 1},{j + 1}]: {err}"]
                fila.append(frac)
            A_frac.append(fila)

        x_frac: list[Fraction] = []
        for j, cell in enumerate(x):
            ok, frac, err = MatrixValidator._to_fraction_strict(cell)
            if not ok:
                return False, [f"Error en x[{j + 1}]: {err}"]
            x_frac.append(frac)

        b_frac: list[Fraction] = []
        for i, cell in enumerate(b):
            ok, frac, err = MatrixValidator._to_fraction_strict(cell)
            if not ok:
                return False, [f"Error en b[{i + 1}]: {err}"]
            b_frac.append(frac)

        # --- 1. Cálculo exacto por ecuación ---
        for i in range(len(A_frac)):
            lhs = Fraction(0)
            terms = []

            for j in range(len(x_frac)):
                coeff = A_frac[i][j]
                var = x_frac[j]
                lhs += coeff * var

                if as_latex:
                    c_tex = number_to_latex(coeff)
                    v_tex = number_to_latex(var)
                    terms.append(rf"\left({c_tex}\right) \cdot \left({v_tex}\right)")
                else:
                    c_str = format_fraction_str(coeff)
                    v_str = format_fraction_str(var)
                    terms.append(f"({c_str})·({v_str})")

            rhs = b_frac[i]
            is_eq_correct = (lhs == rhs)

            lhs_str = format_fraction_str(lhs)
            lhs_tex = number_to_latex(lhs)
            b_str = format_fraction_str(rhs)
            b_tex = number_to_latex(rhs)

            if as_latex:
                substitution_str = " + ".join(terms)
                status_word = "Correcto" if is_eq_correct else "Incorrecto"
                report.append(
                    rf"\text{{Ecuación {i + 1}: }} {substitution_str} = {lhs_tex} \quad "
                    rf"(\text{{{status_word}}}, \; b_{{{i + 1}}} = {b_tex})"
                )
            else:
                substitution_str = " + ".join(terms)
                status_text = "Correcto" if is_eq_correct else "Incorrecto"
                report.append(
                    f"Ecuación {i + 1}: {substitution_str} = {lhs_str}  "
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