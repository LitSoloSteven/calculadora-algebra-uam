from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.utils.validators import (
    validate_same_dimensions,
    validate_multiplication_dimensions
)
from src.backend.utils.formatters import format_fraction_str
from src.backend.utils.formatters import format_fraction_str, number_to_latex

class MatrixOpsSolver:
    """
    Clase para realizar operaciones básicas entre matrices (Suma, Resta, Multiplicación)
    registrando la trazabilidad paso a paso para el frontend.
    """

    def __init__(self):
        self.steps = []

    def _log_step(self, description: str, current_matrix: Matrix = None, detail_latex: str = None):
        """Registra un paso intermedio en la ejecución."""
        self.steps.append({
            "description": description,
            "matrix": current_matrix.clone() if current_matrix else None,
            "detail_latex": detail_latex
        })

    def add(self, matrix_a: Matrix, matrix_b: Matrix) -> dict:
        """Suma elemento a elemento: C_{i,j} = A_{i,j} + B_{i,j}"""
        self.steps = []

        try:
            validate_same_dimensions(matrix_a, matrix_b)
        except ValueError as e:
            return {
                "status": "ERROR",
                "message": str(e),
                "result_matrix": None,
                "steps": []
            }

        m, n = matrix_a.rows, matrix_a.cols
        result = Matrix(m, n)

        self._log_step(f"Iniciando suma de matrices {m}×{n}")

        latex_details = []
        for r in range(m):
            for c in range(n):
                val_a = matrix_a.get(r, c)
                val_b = matrix_b.get(r, c)
                sum_val = val_a + val_b
                result.set(r, c, sum_val)

                a_plain = format_fraction_str(val_a)
                b_plain = format_fraction_str(val_b)
                res_plain = format_fraction_str(sum_val)

                a_tex = number_to_latex(val_a)
                b_tex = number_to_latex(val_b)
                res_tex = number_to_latex(sum_val)

                detail_latex = f"C_{{{r+1},{c+1}}} = A_{{{r+1},{c+1}}} + B_{{{r+1},{c+1}}} = ({a_tex}) + ({b_tex}) = {res_tex}"
                latex_details.append(detail_latex)

                self._log_step(
                    f"Celda ({r+1}, {c+1}): {a_plain} + {b_plain} = {res_plain}",
                    current_matrix=result,
                    detail_latex=detail_latex
                )

        return {
            "status": "SUCCESS",
            "message": f"Suma completada con éxito ({m}×{n}).",
            "result_matrix": result,
            "steps": self.steps,
            "latex_details": latex_details
        }

    def subtract(self, matrix_a: Matrix, matrix_b: Matrix) -> dict:
        """Resta elemento a elemento: C_{i,j} = A_{i,j} - B_{i,j}"""
        self.steps = []

        try:
            validate_same_dimensions(matrix_a, matrix_b)
        except ValueError as e:
            return {
                "status": "ERROR",
                "message": str(e),
                "result_matrix": None,
                "steps": []
            }

        m, n = matrix_a.rows, matrix_a.cols
        result = Matrix(m, n)

        self._log_step(f"Iniciando resta de matrices {m}×{n}")

        latex_details = []
        for r in range(m):
            for c in range(n):
                val_a = matrix_a.get(r, c)
                val_b = matrix_b.get(r, c)
                diff_val = val_a - val_b
                result.set(r, c, diff_val)

                a_plain = format_fraction_str(val_a)
                b_plain = format_fraction_str(val_b)
                res_plain = format_fraction_str(diff_val)

                a_tex = number_to_latex(val_a)
                b_tex = number_to_latex(val_b)
                res_tex = number_to_latex(diff_val)

                detail_latex = f"C_{{{r+1},{c+1}}} = A_{{{r+1},{c+1}}} - B_{{{r+1},{c+1}}} = ({a_tex}) - ({b_tex}) = {res_tex}"
                latex_details.append(detail_latex)

                self._log_step(
                    f"Celda ({r+1}, {c+1}): {a_plain} - {b_plain} = {res_plain}",
                    current_matrix=result,
                    detail_latex=detail_latex
                )

        return {
            "status": "SUCCESS",
            "message": f"Resta completada con éxito ({m}×{n}).",
            "result_matrix": result,
            "steps": self.steps,
            "latex_details": latex_details
        }

    def multiply(self, matrix_a: Matrix, matrix_b: Matrix) -> dict:
        """Multiplicación matricial: C_{i,j} = sum_k (A_{i,k} * B_{k,j})"""
        self.steps = []

        try:
            validate_multiplication_dimensions(matrix_a, matrix_b)
        except ValueError as e:
            return {
                "status": "ERROR",
                "message": str(e),
                "result_matrix": None,
                "steps": []
            }

        m = matrix_a.rows
        n = matrix_a.cols
        q = matrix_b.cols
        result = Matrix(m, q)

        self._log_step(
            f"Multiplicación de A ({m}×{n}) por B ({n}×{q}). Matriz resultante C de {m}×{q}."
        )

        latex_details = []
        for r in range(m):
            for c in range(q):
                cell_sum = Fraction(0)
                terms_plain = []
                terms_latex = []

                for k in range(n):
                    val_a = matrix_a.get(r, k)
                    val_b = matrix_b.get(k, c)
                    prod = val_a * val_b
                    cell_sum += prod

                    a_plain = format_fraction_str(val_a)
                    b_plain = format_fraction_str(val_b)
                    terms_plain.append(f"({a_plain})·({b_plain})")

                    a_tex = number_to_latex(val_a)
                    b_tex = number_to_latex(val_b)
                    terms_latex.append(f"({a_tex})({b_tex})")

                result.set(r, c, cell_sum)
                res_plain = format_fraction_str(cell_sum)
                res_tex = number_to_latex(cell_sum)

                expr_plain = " + ".join(terms_plain) + f" = {res_plain}"
                expr_latex = f"C_{{{r+1},{c+1}}} = " + " + ".join(terms_latex) + f" = {res_tex}"
                latex_details.append(expr_latex)

                self._log_step(
                    f"Fila {r+1} de A × Columna {c+1} de B: {expr_plain}",
                    current_matrix=result,
                    detail_latex=expr_latex
                )

        return {
            "status": "SUCCESS",
            "message": f"Multiplicación completada con éxito. Matriz resultante de {m}×{q}.",
            "result_matrix": result,
            "steps": self.steps,
            "latex_details": latex_details
        }
