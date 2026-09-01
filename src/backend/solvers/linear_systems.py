from fractions import Fraction
from src.backend.models.matrix import Matrix

class GaussSolver:
    def __init__(self, augmented_matrix: Matrix, eps: float = 1e-9):
        self.matrix = augmented_matrix.clone()
        self.eps = eps
        self.steps = []

    def _format_factor(self, val: float) -> str:
        frac = Fraction(val).limit_denominator(100)
        if abs(float(frac) - val) < 1e-4:
            return str(frac.numerator) if frac.denominator == 1 else f"{frac.numerator}/{frac.denominator}"
        return f"{val:.4f}".rstrip('0').rstrip('.')

    def _log_step(self, description: str, current_matrix: Matrix):
        self.steps.append({
            "description": description,
            "matrix": current_matrix.clone()
        })

    def _check_system_status(self, rank: int) -> tuple[str, str]:
        m = self.matrix.rows
        n = self.matrix.cols
        num_vars = n - 1

        for r in range(m):
            all_zeros = all(abs(self.matrix.get(r, c)) < self.eps for c in range(num_vars))
            nonzero_b = abs(self.matrix.get(r, num_vars)) >= self.eps
            if all_zeros and nonzero_b:
                return "NO_SOLUTION", "Sistema Inconsistente: Sin Solución."

        if rank < num_vars:
            return "INFINITE_SOLUTIONS", "Sistema Consistente Indeterminado: Presenta Infinitas Soluciones"

        return "UNIQUE_SOLUTION", "Sistema Consistente Determinado: Presenta Solución Única."

    def _eliminate_forward(self):
        """
        Realiza la eliminación gaussiana con pivoteo parcial.
        Deja la matriz en forma escalonada por filas (con unos en los pivotes).
        Devuelve el rango (número de pivotes) y la lista de columnas pivote.
        """
        m = self.matrix.rows
        n = self.matrix.cols
        pivot_row = 0
        pivot_cols = []

        self._log_step("Matriz inicial aumentada [A|b]:", self.matrix)

        for col in range(min(m, n - 1)):
            # Pivoteo parcial
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

            # Normalizar fila pivote
            pivot_val = self.matrix.get(pivot_row, col)
            if abs(pivot_val) >= self.eps and abs(pivot_val - 1.0) > self.eps:
                scale = 1.0 / pivot_val
                for c in range(col, n):
                    current_val = self.matrix.get(pivot_row, c)
                    self.matrix.set(pivot_row, c, current_val * scale)
                self._log_step(f"Fila {pivot_row + 1} = (1 / {self._format_factor(pivot_val)}) * Fila {pivot_row + 1}", self.matrix)

            # Eliminar debajo del pivote
            for r in range(pivot_row + 1, m):
                factor = self.matrix.get(r, col)
                if abs(factor) > self.eps:
                    self.matrix.add_scaled_row(r, pivot_row, -factor)
                    self.matrix.set(r, col, 0.0)
                    self._log_step(f"Fila {r + 1} = Fila {r + 1} - ({self._format_factor(factor)}) * Fila {pivot_row + 1}", self.matrix)

            pivot_cols.append(col)
            pivot_row += 1
            if pivot_row >= m:
                break

        return pivot_row, pivot_cols   # (rank, pivot_columns)

    def _back_substitute(self, num_vars):
        """
        Realiza la sustitución regresiva para obtener la solución única.
        Devuelve la lista de incógnitas y los pasos en LaTeX.
        """
        x = [0.0] * num_vars
        back_sub_steps = []

        for i in range(num_vars - 1, -1, -1):
            b_i = self.matrix.get(i, num_vars)
            a_ii = self.matrix.get(i, i)
            sum_ax = 0.0
            terms = []
            for j in range(i + 1, num_vars):
                coeff = self.matrix.get(i, j)
                if abs(coeff) > self.eps:
                    sum_ax += coeff * x[j]
                    terms.append(f"({self._format_factor(coeff)})({self._format_factor(x[j])})")
            x[i] = (b_i - sum_ax) / a_ii if abs(a_ii) > self.eps else 0.0

            var_str = f"x_{{{i + 1}}}"
            b_str = self._format_factor(b_i)
            a_str = self._format_factor(a_ii)
            res_str = self._format_factor(x[i])
            if not terms:
                step_latex = f"{var_str} = \\frac{{{b_str}}}{{{a_str}}} = {res_str}"
            else:
                sub_str = " + ".join(terms)
                step_latex = f"{var_str} = \\frac{{{b_str} - ({sub_str})}}{{{a_str}}} = {res_str}"
            back_sub_steps.append(step_latex)

        return [0.0 if abs(val) < self.eps else round(val, 6) for val in x], back_sub_steps

    def solve(self):
        # 1. Eliminación hacia adelante
        rank, _ = self._eliminate_forward()

        # 2. Verificar estado del sistema
        status, message = self._check_system_status(rank)

        if status != "UNIQUE_SOLUTION":
            return {
                "status": status,
                "message": message,
                "echelon_matrix": self.matrix,
                "solution": None,
                "steps": self.steps
            }

        # 3. Sustitución hacia atrás
        num_vars = self.matrix.cols - 1
        solution, back_steps = self._back_substitute(num_vars)

        return {
            "status": status,
            "message": message,
            "echelon_matrix": self.matrix,
            "solution": solution,
            "steps": self.steps,
            "back_substitution_steps": back_steps
        }