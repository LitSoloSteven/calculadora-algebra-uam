from fractions import Fraction
from typing import Dict
from src.backend.constants import ZERO_EPSILON
from src.backend.models.matrix import Matrix
from src.backend.utils.formatters import format_fraction_str, format_parametric_expr, format_variable_for_latex

class GaussSolver:
    FULL_REDUCTION: bool = False

    def __init__(self, augmented_matrix: Matrix, eps: float = ZERO_EPSILON,
             variable_names: list[str] | None = None):
        self.matrix = augmented_matrix.clone()
        self.eps = eps
        self.variable_names = variable_names
        self.steps = []

    def _log_step(self, description: str, current_matrix: Matrix):
        self.steps.append({
            "description": description,
            "matrix": current_matrix.clone()
        })

    def _get_row(self, row_idx: int) -> list:
        return [self.matrix.get(row_idx, c) for c in range(self.matrix.cols)]

    def _set_row(self, row_idx: int, row_values: list) -> None:
        # No forzar a float: Matrix._normalize_val conserva Fraction/int tal cual,
        # así se preserva la precisión exacta ganada en _eliminate_row_exact.
        for c, val in enumerate(row_values):
            self.matrix.set(row_idx, c, val)

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

    def _eliminate_row_exact(self, pivot_row: list, target_row: list, col_idx: int, target_idx: int, pivot_idx: int) -> tuple[list, str]:
        # Eliminación con aritmética exacta: el factor se calcula como
        # target_val / pivot_val y se aplica con Fraction, sin redondeos
        # intermedios. Se preserva la representación exacta de fracciones
        # y decimales a lo largo de la eliminación..
        pivot_val = Fraction(pivot_row[col_idx])
        target_val = Fraction(target_row[col_idx])

        if target_val == 0:
            return target_row, ""

        factor = target_val / pivot_val
        new_row = [Fraction(tv) - factor * Fraction(pv) for tv, pv in zip(target_row, pivot_row)]

        op_desc = f"Fila {target_idx + 1} = Fila {target_idx + 1} − ({format_fraction_str(factor)}) · Fila {pivot_idx + 1}"

        return new_row, op_desc

    def _eliminate(self, full_reduction: bool) -> tuple[int, list[int]]:
        """Eliminación por eliminación exacta con Fraction.

        full_reduction=False -> Gauss (elimina solo debajo del pivote)
        full_reduction=True  -> Gauss-Jordan (elimina arriba y debajo)
        """
        m = self.matrix.rows
        n = self.matrix.cols
        pivot_row = 0
        pivot_cols = []

        self._log_step("Matriz inicial aumentada [A|b]:", self.matrix)

        for col in range(n - 1):
            if pivot_row >= m:
                break

            # Pivoteo parcial: elegir el mayor valor absoluto en la columna.
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

            # El texto del paso "Pivote seleccionado" difiere entre los métodos:
            # Gauss lo reporta con el valor, Gauss-Jordan sin él.
            if full_reduction:
                self._log_step(
                    f"Pivote seleccionado en Fila {pivot_row + 1}, Columna {col + 1}",
                    self.matrix
                )
            else:
                self._log_step(
                    f"Pivote seleccionado en Fila {pivot_row + 1}, Columna {col + 1} "
                    f"(valor = {format_fraction_str(self.matrix.get(pivot_row, col))})",
                    self.matrix
                )

            row_piv = self._get_row(pivot_row)

            # Gauss-Jordan elimina también por encima del pivote; Gauss solo por debajo.
            if full_reduction:
                target_rows = [r for r in range(m) if r != pivot_row]
            else:
                target_rows = list(range(pivot_row + 1, m))

            for r in target_rows:
                if abs(self.matrix.get(r, col)) > self.eps:
                    row_target = self._get_row(r)
                    new_row, op_desc = self._eliminate_row_exact(row_piv, row_target, col, r, pivot_row)
                    self._set_row(r, new_row)
                    self._log_step(op_desc, self.matrix)

            pivot_cols.append(col)
            pivot_row += 1

        rank = pivot_row

        # Normalizar pivotes a 1. El prefijo del mensaje difiere entre métodos.
        normalize_prefix = "Normalizar pivote a 1" if full_reduction else "Normalizar pivote"
        for r, c in enumerate(pivot_cols):
            pivot_val = self.matrix.get(r, c)
            if abs(pivot_val) >= self.eps and abs(pivot_val - 1) > self.eps:
                scale = Fraction(1) / Fraction(pivot_val)
                row = self._get_row(r)
                normalized_row = [elem * scale for elem in row]
                self._set_row(r, normalized_row)
                self._log_step(
                    f"{normalize_prefix}: Fila {r + 1} = Fila {r + 1} / {format_fraction_str(pivot_val)}",
                    self.matrix
                )

        return rank, pivot_cols

    def _back_substitute(self, pivot_cols: list[int]):
        num_vars = self.matrix.cols - 1
        free_cols = [c for c in range(num_vars) if c not in pivot_cols]
        param_names = ['t', 's', 'r', 'u', 'v']
        
        free_var_map = {}
        for idx, col in enumerate(free_cols):
            p_name = param_names[idx] if idx < len(param_names) else f"t_{idx + 1}"
            free_var_map[col] = p_name

        expr_const = [Fraction(0)] * num_vars
        expr_terms = [{} for _ in range(num_vars)]
        back_sub_steps = []

        if free_cols:
            free_desc_parts = []
            for c in free_cols:
                if self.variable_names and c < len(self.variable_names):
                    var_label = format_variable_for_latex(self.variable_names[c])
                else:
                    var_label = f"x_{{{c + 1}}}"
                free_desc_parts.append(f"{var_label} = {free_var_map[c]}")
            free_desc = ", ".join(free_desc_parts)
            back_sub_steps.append(f"Variables libres identificadas: {free_desc}")
            for c in free_cols:
                expr_terms[c] = {free_var_map[c]: Fraction(1)}

        for i in range(len(pivot_cols) - 1, -1, -1):
            p_col = pivot_cols[i]
             # Matrix.get() ya garantiza Fraction exacto (vía _normalize_val).
            # Reaplicar limit_denominator(1000) truncaría fracciones con
            # denominador > 1000 e introduciría error silencioso en la solución.
            a_ii = Fraction(self.matrix.get(i, p_col))
            b_i = Fraction(self.matrix.get(i, num_vars))

            c_val = b_i
            t_val: Dict[str, Fraction] = {}

            for j in range(p_col + 1, num_vars):
                coeff = Fraction(self.matrix.get(i, j))
                if coeff != 0:
                    c_val -= coeff * expr_const[j]
                    for var, v_coeff in expr_terms[j].items():
                        t_val[var] = t_val.get(var, Fraction(0)) - (coeff * v_coeff)

            c_val /= a_ii
            t_val = {k: v / a_ii for k, v in t_val.items() if (v / a_ii) != 0}

            expr_const[p_col] = c_val
            expr_terms[p_col] = t_val

            res_str = format_parametric_expr(c_val, t_val)
            if self.variable_names and p_col < len(self.variable_names):
                var_label = format_variable_for_latex(self.variable_names[p_col])
            else:
                var_label = f"x_{{{p_col + 1}}}"
            back_sub_steps.append(f"{var_label} = {res_str}")

        solution = [format_parametric_expr(expr_const[i], expr_terms[i]) for i in range(num_vars)]
        return solution, back_sub_steps

    def solve(self):
        rank, pivot_cols = self._eliminate(full_reduction=self.FULL_REDUCTION)
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
