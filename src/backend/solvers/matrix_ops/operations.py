from fractions import Fraction
from src.backend.models.matrix import Matrix, Numeric
from src.backend.solvers._tracing import StepTraceMixin
from src.backend.utils.validators import (
    validate_same_dimensions,
    validate_multiplication_dimensions,
    MatrixValidator,
)
from src.backend.utils.formatters import format_fraction_str, number_to_latex
from src.backend.exceptions import DimensionMismatchError

class MatrixOpsSolver(StepTraceMixin):
    """
    Clase para realizar operaciones básicas entre matrices (Suma, Resta, Multiplicación)
    registrando la trazabilidad paso a paso para el frontend.
    """

    def _elementwise_binary_op(
        self,
        matrix_a: Matrix,
        matrix_b: Matrix,
        *,
        op_symbol: str,
        op_word: str,
    ) -> dict:
        """Suma o resta elemento a elemento: C_{i,j} = A_{i,j} ± B_{i,j}.

        Helper compartido por `add` y `subtract`. `op_symbol` es "+" o "-",
        `op_word` es "suma" o "resta". El resultado es byte a byte idéntico
        al de la implementación previa duplicada.
        """
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

        self._log_step(f"Iniciando {op_word} de matrices {m}×{n}")

        latex_details = []
        for r in range(m):
            for c in range(n):
                val_a = matrix_a.get(r, c)
                val_b = matrix_b.get(r, c)
                res_val = val_a + val_b if op_symbol == "+" else val_a - val_b
                result.set(r, c, res_val)

                a_plain = format_fraction_str(val_a)
                b_plain = format_fraction_str(val_b)
                res_plain = format_fraction_str(res_val)

                a_tex = number_to_latex(val_a)
                b_tex = number_to_latex(val_b)
                res_tex = number_to_latex(res_val)

                detail_latex = f"C_{{{r+1},{c+1}}} = A_{{{r+1},{c+1}}} {op_symbol} B_{{{r+1},{c+1}}} = ({a_tex}) {op_symbol} ({b_tex}) = {res_tex}"
                latex_details.append(detail_latex)

                self._log_step(
                    f"Celda ({r+1}, {c+1}): {a_plain} {op_symbol} {b_plain} = {res_plain}",
                    current_matrix=result,
                    detail_latex=detail_latex
                )

        return {
            "status": "SUCCESS",
            "message": f"{op_word.capitalize()} completada con éxito ({m}×{n}).",
            "result_matrix": result,
            "steps": self.steps,
            "latex_details": latex_details
        }

    def add(self, matrix_a: Matrix, matrix_b: Matrix) -> dict:
        """Suma elemento a elemento: C_{i,j} = A_{i,j} + B_{i,j}"""
        return self._elementwise_binary_op(
            matrix_a, matrix_b,
            op_symbol="+", op_word="suma",
        )

    def subtract(self, matrix_a: Matrix, matrix_b: Matrix) -> dict:
        """Resta elemento a elemento: C_{i,j} = A_{i,j} - B_{i,j}"""
        return self._elementwise_binary_op(
            matrix_a, matrix_b,
            op_symbol="-", op_word="resta",
        )
        
    def scalar_multiply(self, scalar: Numeric, matrix_a: Matrix) -> dict:
        """Multiplicación de un escalar por una matriz: C_{i,j} = k · A_{i,j}.

        Correspondencia algebraica (Lay, sección 2.1): el múltiplo escalar rA
        es la matriz cuyas entradas son r veces las entradas correspondientes
        de A. La operación conserva el orden de la matriz original (m×n).

        El escalar se parsea con `parse_number_exact` para preservar la
        precisión exacta: '1/2' → Fraction(1,2), no float(0.5).
        """
        self.steps = []

        # Parseo exacto del escalar — misma fuente de verdad que el resto del backend.
        ok, scalar_frac, err = MatrixValidator.parse_number_exact(scalar)
        if not ok:
            return {
                "status": "ERROR",
                "message": f"Escalar inválido: {err}",
                "result_matrix": None,
                "steps": []
            }

        m, n = matrix_a.rows, matrix_a.cols
        result = Matrix(m, n)

        k_plain = format_fraction_str(scalar_frac)
        self._log_step(f"Iniciando multiplicación escalar: {k_plain} · A ({m}×{n})")

        latex_details = []
        for r in range(m):
            for c in range(n):
                val_a = matrix_a.get(r, c)
                prod_val = scalar_frac * val_a
                result.set(r, c, prod_val)

                a_plain = format_fraction_str(val_a)
                res_plain = format_fraction_str(prod_val)

                k_tex = number_to_latex(scalar_frac)
                a_tex = number_to_latex(val_a)
                res_tex = number_to_latex(prod_val)

                detail_latex = (
                    f"C_{{{r+1},{c+1}}} = ({k_tex}) \\cdot A_{{{r+1},{c+1}}} "
                    f"= ({k_tex})({a_tex}) = {res_tex}"
                )
                latex_details.append(detail_latex)

                self._log_step(
                    f"Celda ({r+1}, {c+1}): {k_plain} · {a_plain} = {res_plain}",
                    current_matrix=result,
                    detail_latex=detail_latex
                )

        return {
            "status": "SUCCESS",
            "message": f"Multiplicación escalar completada con éxito ({m}×{n}).",
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

    def transpose(self, matrix_a: Matrix) -> Matrix:
        """Transpuesta: (Aᵀ)_{i,j} = A_{j,i}.

        Devuelve una Matrix nueva del shape traspuesto. La operación es
        pura: no registra steps (no hay cálculo celda a celda que mostrar,
        solo un reindexado) y no muta el operando.

        Correspondencia algebraica (Lay, sección 2.1): la transpuesta de
        una matriz A de m×n es la matriz Aᵀ de n×m cuyas columnas son las
        filas de A.
        """
        new_data = [
            [matrix_a.get(i, j) for i in range(matrix_a.rows)]
            for j in range(matrix_a.cols)
        ]
        return Matrix(matrix_a.cols, matrix_a.rows, new_data)
    
    def determinant(self, matrix_a: Matrix) -> Fraction:
        """Determinante de una matriz cuadrada.

        Algoritmo: eliminación a forma triangular superior con pivoteo
        parcial + producto de la diagonal × (-1)^(swaps). NO usa
        cofactores recursivos (O(n!), inviable para n > 10 — ver PPT
        Determinantes, pág. 15-16).

        Correspondencia algebraica (PPT Determinantes):
        - n=2: det = ad - bc (pág. 3).
        - Triangular (sup/inf): det = producto de la diagonal (pág. 15).
        - Swap de filas: det cambia de signo (pág. 18-19).
        - det(A) = 0 ⇔ A singular (pág. 25).

        Devuelve Fraction puro (análogo a `transpose`). No registra steps:
        el cálculo no tiene trazabilidad pedagógica que exponer al frontend.
        Si el controller necesita mostrar el procedimiento, lo genera a
        partir de la matriz original.

        Raises:
            DimensionMismatchError: si matrix_a no es cuadrada.
        """
        n_rows, n_cols = matrix_a.rows, matrix_a.cols
        if n_rows != n_cols:
            raise DimensionMismatchError(
                operation="determinant (A debe ser cuadrada)",
                shape_a=(n_rows, n_cols),
                shape_b=(n_rows, n_rows),
            )
        n = n_rows

        # --- Casos base con fórmula directa ---
        if n == 1:
            return Fraction(matrix_a.get(0, 0))
        if n == 2:
            a = Fraction(matrix_a.get(0, 0))
            b = Fraction(matrix_a.get(0, 1))
            c = Fraction(matrix_a.get(1, 0))
            d = Fraction(matrix_a.get(1, 1))
            return a * d - b * c

        # --- n >= 3: eliminación a triangular con pivoteo parcial ---
        # Clonamos para no mutar el input (consistente con el resto del solver).
        M = matrix_a.clone()
        sign = Fraction(1)

        for col in range(n):
            # Pivoteo parcial: mayor valor absoluto en la columna, desde 'col'.
            pivot_row = col
            for r in range(col + 1, n):
                if abs(M.get(r, col)) > abs(M.get(pivot_row, col)):
                    pivot_row = r

            pivot_val = M.get(pivot_row, col)
            if pivot_val == 0:
                # Toda la columna debajo del pivote es cero → singular.
                return Fraction(0)

            if pivot_row != col:
                M.swap_rows(col, pivot_row)
                sign = -sign
                pivot_val = M.get(col, col)

            # Eliminar debajo del pivote. Conserva el determinante.
            for r in range(col + 1, n):
                val = M.get(r, col)
                if val != 0:
                    factor = Fraction(val) / Fraction(pivot_val)
                    M.add_scaled_row(r, col, -factor)

        # det(A) = signo · producto de la diagonal de la triangular superior.
        det = sign
        for i in range(n):
            det *= Fraction(M.get(i, i))
        return det

    # Alias canónicos en castellano
    sumar = add
    restar = subtract
    multiplicar = multiply
    multiplicar_escalar = scalar_multiply
    transponer = transpose
    determinante = determinant
    _operacion_binaria_elemento_a_elemento = _elementwise_binary_op