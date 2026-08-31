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

            # Normalizar el elemento de la diagonal principal a 1
            pivot_val = self.matrix.get(pivot_row, col)
            if abs(pivot_val) >= self.eps and abs(pivot_val - 1.0) > self.eps:
                scale = 1.0 / pivot_val
                for c in range(col, n):
                    current_val = self.matrix.get(pivot_row, c)
                    self.matrix.set(pivot_row, c, current_val * scale)
                self._log_step(f"Normalizar pivote: Fila {pivot_row + 1} = (1 / {self._format_factor(pivot_val)}) * Fila {pivot_row + 1}", self.matrix)

            # Hacer ceros por debajo del pivote
            for r in range(pivot_row + 1, m):
                factor = self.matrix.get(r, col)
                if abs(factor) > self.eps:
                    self.matrix.add_scaled_row(r, pivot_row, -factor)
                    self.matrix.set(r, col, 0.0)
                    
                    factor_str = self._format_factor(factor)
                    self._log_step(f"Eliminación: Fila {r + 1} = Fila {r + 1} - ({factor_str}) * Fila {pivot_row + 1}", self.matrix)

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

        # Registrar el sistema de ecuaciones obtenido en la triangular superior
        self._log_echelon_system_equations()

        # Sustitución hacia atrás (de abajo hacia arriba) con registro detallado
        num_vars = n - 1
        x = [0.0] * num_vars

        for i in range(num_vars - 1, -1, -1):
            b_i = self.matrix.get(i, num_vars)
            sub_expr = []
            sum_ax = 0.0
            
            for j in range(i + 1, num_vars):
                coeff = self.matrix.get(i, j)
                if abs(coeff) > self.eps:
                    sum_ax += coeff * x[j]
                    sub_expr.append(f"({self._format_factor(coeff)})({x[j]})")
            
            x[i] = b_i - sum_ax
            
            # Registrar el paso de despeje algebraico
            eq_desc = f"Despeje de x_{i+1}: x_{i+1} = {self._format_factor(b_i)}"
            if sub_expr:
                eq_desc += " - " + " - ".join(sub_expr)
            eq_desc += f" = {round(x[i], 6)}"
            
            self._log_step(eq_desc, self.matrix)

        x = [0.0 if abs(val) < self.eps else round(val, 6) for val in x]

        return {
            "status": "UNIQUE_SOLUTION",
            "message": "Sistema compatible determinado (Solución única encontrada).",
            "echelon_matrix": self.matrix,
            "solution": x,
            "steps": self.steps
        }

    def _log_echelon_system_equations(self):
        m = self.matrix.rows
        n = self.matrix.cols
        num_vars = n - 1
        eqs_desc = "Sistema de ecuaciones equivalente (Triangular Superior):\n"
        
        for i in range(min(m, num_vars)):
            terms = []
            for j in range(num_vars):
                val = self.matrix.get(i, j)
                if abs(val) >= self.eps:
                    f_str = self._format_factor(val)
                    if f_str == "1":
                        term = f"x_{{{j+1}}}"
                    elif f_str == "-1":
                        term = f"-x_{{{j+1}}}"
                    else:
                        term = f"{f_str}x_{{{j+1}}}"
                    
                    if terms and val > 0:
                        terms.append(f"+ {term}")
                    else:
                        terms.append(term)
            
            b_val = self._format_factor(self.matrix.get(i, num_vars))
            eq_str = " ".join(terms) if terms else "0"
            eqs_desc += f"Ecuación {i+1}: {eq_str} = {b_val}\n"
            
        self._log_step(eqs_desc.strip(), self.matrix)

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