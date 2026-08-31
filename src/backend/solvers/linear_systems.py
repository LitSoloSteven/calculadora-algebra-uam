from fractions import Fraction
from src.backend.models.matrix import Matrix

class GaussSolver:
    def __init__(self, augmented_matrix: Matrix, eps: float = 1e-9):
        self.matrix = augmented_matrix.clone()
        self.eps = eps
        self.steps = []

    def solve(self) -> dict:
        m = self.matrix.rows
        n = self.matrix.cols
        self._log_step("Matriz inicial aumentada [A|b]:", self.matrix)

        pivot_row = 0
        for col in range(min(m, n - 1)):
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

            for r in range(pivot_row + 1, m):
                factor = self.matrix.get(r, col) / self.matrix.get(pivot_row, col)
                if abs(factor) > self.eps:
                    self.matrix.add_scaled_row(r, pivot_row, -factor)
                    self.matrix.set(r, col, 0.0)
                    
                    factor_str = self._format_factor(factor)
                    self._log_step(f"Fila {r + 1} = Fila {r + 1} - ({factor_str}) * Fila {pivot_row + 1}", self.matrix)

            pivot_row += 1
            if pivot_row >= m:
                break

        status, message = self._check_system_status(pivot_row)
        if status != "UNIQUE_SOLUTION":
            return {
                "status": status,
                "message": message,
                "echelon_matrix": self.matrix,
                "solution": None,
                "steps": self.steps
            }

        num_vars = n - 1
        x = [0.0] * num_vars

        for i in range(num_vars - 1, -1, -1):
            sum_ax = sum(self.matrix.get(i, j) * x[j] for j in range(i + 1, num_vars))
            b_i = self.matrix.get(i, num_vars)
            a_ii = self.matrix.get(i, i)
            x[i] = (b_i - sum_ax) / a_ii

        x = [0.0 if abs(val) < self.eps else round(val, 6) for val in x]

        return {
            "status": "UNIQUE_SOLUTION",
            "message": "Sistema compatible determinado (Solución única encontrada).",
            "echelon_matrix": self.matrix,
            "solution": x,
            "steps": self.steps
        }

    def _format_factor(self, val: float) -> str:
        frac = Fraction(val).limit_denominator(100)
        if abs(float(frac) - val) < 1e-4:
            return str(frac.numerator) if frac.denominator == 1 else f"{frac.numerator}/{frac.denominator}"
        return f"{val:.4f}".rstrip('0').rstrip('.')

    def _check_system_status(self, rank: int) -> tuple[str, str]:
        m = self.matrix.rows
        n = self.matrix.cols
        num_vars = n - 1

        for r in range(m):
            all_zeros = all(abs(self.matrix.get(r, c)) < self.eps for c in range(num_vars))
            nonzero_b = abs(self.matrix.get(r, num_vars)) >= self.eps
            if all_zeros and nonzero_b:
                return "NO_SOLUTION", "Sistema Incompatible (Sin solución)."

        if rank < num_vars:
            return "INFINITE_SOLUTIONS", "Sistema Compatible Indeterminado (Infinitas soluciones)."

        return "UNIQUE_SOLUTION", "OK"

    def _log_step(self, description: str, current_matrix: Matrix):
        self.steps.append({
            "description": description,
            "matrix": current_matrix.clone()
        })