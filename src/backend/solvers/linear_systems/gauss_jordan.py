from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.utils.formatters import format_fraction_str

class GaussJordanSolver(GaussSolver):
    """
    Solver para el método de Gauss-Jordan empleando Eliminación Entera por MCM.
    Hereda de GaussSolver para compartir sustitución paramétrica y utilidades.
    """

    def _eliminate_gauss_jordan(self):
        m = self.matrix.rows
        n = self.matrix.cols
        pivot_row = 0
        pivot_cols = []

        self._log_step("Matriz inicial aumentada [A|b]:", self.matrix)

        for col in range(n - 1):
            if pivot_row >= m:
                break

            max_row = pivot_row
            max_val = abs(self.matrix.get(pivot_row, col))
            for r in range(pivot_row + 1, m):
                val = abs(self.matrix.get(r, col))
                if val > max_val:
                    max_val = val
                    max_row = r

            if max_val < self.eps:
                continue

            if max_row != pivot_row:
                self.matrix.swap_rows(pivot_row, max_row)
                self._log_step(f"Intercambio: Fila {pivot_row + 1} ↔ Fila {max_row + 1}", self.matrix)

            self._log_step(
                f"Pivote seleccionado en Fila {pivot_row + 1}, Columna {col + 1}",
                self.matrix
            )

            row_piv = self._get_row(pivot_row)

            for r in range(m):
                if r != pivot_row and abs(self.matrix.get(r, col)) > self.eps:
                    row_target = self._get_row(r)
                    new_row, op_desc = self._eliminate_row_with_lcm(row_piv, row_target, col, r, pivot_row)
                    self._set_row(r, new_row)
                    self._log_step(op_desc, self.matrix)

            pivot_cols.append(col)
            pivot_row += 1

        rank = pivot_row

        # Normalizar pivotes a 1 (Forma Escalonada Reducida)
        for r, c in enumerate(pivot_cols):
            pivot_val = self.matrix.get(r, c)
            if abs(pivot_val) >= self.eps and abs(pivot_val - 1) > self.eps:
                scale = Fraction(1) / Fraction(pivot_val)
                row = self._get_row(r)
                normalized_row = [elem * scale for elem in row]
                self._set_row(r, normalized_row)
                self._log_step(
                    f"Normalizar pivote a 1: Fila {r + 1} = Fila {r + 1} / {format_fraction_str(pivot_val)}",
                    self.matrix
                )

        return rank, pivot_cols

    def solve(self):
        rank, pivot_cols = self._eliminate_gauss_jordan()
        status, message = self._check_system_status(rank)

        if status == "NO_SOLUTION":
            return {
                "status": status,
                "classification": message,
                "message": message,
                "echelon_matrix": self.matrix,
                "solution": None,
                "steps": self.steps,
                "back_substitution_steps": []
            }

        solution, back_steps = self._back_substitute(pivot_cols)

        return {
            "status": status,
            "classification": message,
            "message": message,
            "echelon_matrix": self.matrix,
            "solution": solution,
            "steps": self.steps,
            "back_substitution_steps": back_steps
        }
