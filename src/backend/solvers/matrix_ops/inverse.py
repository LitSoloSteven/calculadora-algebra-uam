"""Solver de matriz inversa vía Gauss-Jordan sobre [A | I].

Aprovecha GaussJordanSolver con num_rhs=n (soporte agregado en el
commit previo) para reducir [A | I] -> [I | A^-1]. Esto mantiene a
GaussJordanSolver como fuente única de verdad de la eliminación
exacta y evita reimplementar el algoritmo.

Referencias pedagógicas:
- PPT Inversa de una Matriz, pág. 5-10 (algoritmo formal).
- PPT Determinantes, pág. 25 (det != 0 <=> invertible).
- PPT Inversa, pág. 11: propiedades (A^-1)^-1 = A, (AB)^-1 = B^-1 A^-1,
  (A^T)^-1 = (A^-1)^T.
"""
from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver
from src.backend.solvers.matrix_ops.formatters import (
    matrix_to_latex,
    partitioned_matrix_to_latex,
)
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver


class MatrixInverseSolver:
    """Calcula A^-1 vía Gauss-Jordan sobre [A | I] con verificación.

    El solver es stateless respecto de `steps`: cada llamada a `solve()`
    construye su propio GaussJordanSolver y no conserva estado entre
    invocaciones.
    """

    def __init__(self):
        self.ops_solver = MatrixOpsSolver()

    def solve(self, matrix_a: Matrix) -> dict:
        """Calcula A^-1, si existe, y devuelve pasos + verificaciones.

        Returns:
            dict con:
              - status: "SUCCESS" | "SINGULAR" | "ERROR"
              - message: str
              - determinant: Fraction | None
              - augmented_initial_latex: str | None  ([A | I] inicial)
              - inverse: Matrix | None
              - inverse_latex: str | None
              - steps: list[dict]  (pasos de GJ con detail_latex)
              - verification_step: dict | None         (A · A^-1 = I)
              - verification_reverse_step: dict | None (A^-1 · A = I)
              - transpose_property_step: dict | None   ((A^T)^-1 = (A^-1)^T)
        """
        # --- 1. Validación temprana ---
        if not isinstance(matrix_a, Matrix):
            return self._error("Se esperaba una Matrix.")
        if matrix_a.rows != matrix_a.cols:
            return self._error(
                f"La matriz debe ser cuadrada para tener inversa: "
                f"recibido {matrix_a.rows}×{matrix_a.cols}."
            )

        n = matrix_a.rows

        # --- 2. Determinante: cortocircuito si es singular ---
        det = self.ops_solver.determinant(matrix_a)
        if det == 0:
            return self._singular(
                "La matriz es singular (det = 0). No tiene inversa.",
                det,
            )

        # --- 3. Construir [A | I] ---
        augmented_data = []
        for i in range(n):
            row = [matrix_a.get(i, j) for j in range(n)]
            for j in range(n):
                row.append(Fraction(1) if i == j else Fraction(0))
            augmented_data.append(row)
        augmented = Matrix(n, 2 * n, augmented_data)
        augmented_initial_latex = partitioned_matrix_to_latex(augmented, n)

        # --- 4. Gauss-Jordan con num_rhs=n ---
        # Aquí es donde se ve la importación y uso de GaussJordanSolver.
        gj = GaussJordanSolver(augmented, num_rhs=n)
        reduction = gj.solve_reduction()

        if reduction["rank"] < n:
            # Defensivo: ya detectamos det=0 arriba, pero por si acaso.
            return self._singular(
                f"La matriz es singular (rank {reduction['rank']} < {n}). "
                f"No tiene inversa.",
                det,
                augmented_initial_latex=augmented_initial_latex,
                steps=self._format_steps(reduction["steps"], n),
            )

        # --- 5. Extraer bloque derecho ---
        reduced = reduction["reduced_matrix"]
        inverse_data = [
            [reduced.get(i, n + j) for j in range(n)]
            for i in range(n)
        ]
        inverse = Matrix(n, n, inverse_data)
        inverse_latex = matrix_to_latex(inverse)

        # --- 6. Verificaciones ---
        verification = self._verify_product(
            matrix_a, inverse, n, reverse=False
        )
        verification_reverse = self._verify_product(
            matrix_a, inverse, n, reverse=True
        )
        transpose_property = self._verify_transpose_property(matrix_a, inverse)

        return {
            "status": "SUCCESS",
            "message": f"Inversa calculada con éxito ({n}×{n}).",
            "determinant": det,
            "augmented_initial_latex": augmented_initial_latex,
            "inverse": inverse,
            "inverse_latex": inverse_latex,
            "steps": self._format_steps(reduction["steps"], n),
            "verification_step": verification,
            "verification_reverse_step": verification_reverse,
            "transpose_property_step": transpose_property,
        }

    # ------------------------------------------------------------------
    # Constructores de respuesta
    # ------------------------------------------------------------------

    @staticmethod
    def _error(message: str) -> dict:
        return {
            "status": "ERROR",
            "message": message,
            "determinant": None,
            "augmented_initial_latex": None,
            "inverse": None,
            "inverse_latex": None,
            "steps": [],
            "verification_step": None,
            "verification_reverse_step": None,
            "transpose_property_step": None,
        }

    @staticmethod
    def _singular(
        message: str,
        determinant: Fraction,
        augmented_initial_latex: str | None = None,
        steps: list[dict] | None = None,
    ) -> dict:
        return {
            "status": "SINGULAR",
            "message": message,
            "determinant": determinant,
            "augmented_initial_latex": augmented_initial_latex,
            "inverse": None,
            "inverse_latex": None,
            "steps": steps if steps is not None else [],
            "verification_step": None,
            "verification_reverse_step": None,
            "transpose_property_step": None,
        }

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _format_steps(raw_steps: list[dict], n: int) -> list[dict]:
        """Convierte los steps de Gauss ({description, matrix}) al formato
        de matrix_ops ({description, matrix, detail_latex}).

        El primer paso de Gauss dice "Matriz inicial aumentada [A|b]:";
        para la inversa se reescribe a "[A|I]:" porque la matriz aumentada
        es [A|I], no [A|b].
        """
        out = []
        for i, step in enumerate(raw_steps):
            mat = step.get("matrix")
            description = step["description"]
            if i == 0 and "[A|b]" in description:
                description = description.replace("[A|b]", "[A|I]")
            out.append({
                "description": description,
                "matrix": mat,
                "detail_latex": (
                    partitioned_matrix_to_latex(mat, n) if mat is not None else None
                ),
            })
        return out

    def _verify_product(
        self, A: Matrix, A_inv: Matrix, n: int, *, reverse: bool
    ) -> dict:
        """Verifica A·A^-1 = I (reverse=False) o A^-1·A = I (reverse=True)."""
        left, right = (A_inv, A) if reverse else (A, A_inv)
        left_name = "A^{-1}" if reverse else "A"
        right_name = "A" if reverse else "A^{-1}"

        product = self.ops_solver.multiply(left, right)["result_matrix"]

        coincide = all(
            product.get(i, j) == (Fraction(1) if i == j else Fraction(0))
            for i in range(n)
            for j in range(n)
        )

        status_word = "Correcto" if coincide else "Incorrecto"
        detail_latex = (
            f"{left_name} \\cdot {right_name} = "
            f"{matrix_to_latex(product)}"
            f" \\quad (\\text{{{status_word}}})"
        )

        return {
            "description": (
                f"Verificación {'A⁻¹·A' if reverse else 'A·A⁻¹'} = I."
            ),
            "left_name": left_name,
            "right_name": right_name,
            "product_latex": matrix_to_latex(product),
            "coincide": coincide,
            "detail_latex": detail_latex,
        }

    def _verify_transpose_property(self, A: Matrix, A_inv: Matrix) -> dict:
        """Verifica (A^T)^-1 = (A^-1)^T vía (A^-1)^T · A^T = I.

        Equivalencia: (A^-1)^T = (A^T)^-1  <=>  (A^-1)^T · A^T = I.
        Evita recomputar la inversa de A^T (más rápido y con la misma
        garantía matemática).
        """
        A_T = self.ops_solver.transpose(A)
        A_inv_T = self.ops_solver.transpose(A_inv)

        n = A.rows
        product = self.ops_solver.multiply(A_inv_T, A_T)["result_matrix"]
        coincide = all(
            product.get(i, j) == (Fraction(1) if i == j else Fraction(0))
            for i in range(n)
            for j in range(n)
        )

        status_word = "Coinciden" if coincide else "Difieren"
        detail_latex = (
            f"(A^{{-1}})^T \\cdot A^T = {matrix_to_latex(product)}"
            f" \\quad (\\text{{{status_word}}})"
        )

        return {
            "description": (
                "Verificación (Aᵀ)⁻¹ = (A⁻¹)ᵀ (PPT Inversa, pág. 11)."
            ),
            "coincide": coincide,
            "detail_latex": detail_latex,
        }