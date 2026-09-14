from fractions import Fraction
from typing import Dict
from src.backend.models.matrix import Matrix
from src.backend.utils.math_utils import mcm, simplificar_fila
from src.backend.utils.formatters import format_fraction_str, format_parametric_expr

class GaussSolver:
    def __init__(self, augmented_matrix: Matrix, eps: float = 1e-9):
        self.matrix = augmented_matrix.clone()
        self.eps = eps
        self.steps = []

    def _log_step(self, description: str, current_matrix: Matrix):
        self.steps.append({
            "description": description,
            "matrix": current_matrix.clone()
        })

    def _get_row(self, row_idx: int) -> list[float]:
        return [self.matrix.get(row_idx, c) for c in range(self.matrix.cols)]

    def _set_row(self, row_idx: int, row_values: list[float]):
        for c, val in enumerate(row_values):
            self.matrix.set(row_idx, c, float(val))

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

    def _eliminate_row_with_lcm(self, pivot_row: list[float], target_row: list[float], col_idx: int, target_idx: int, pivot_idx: int) -> tuple[list[float], str]:
        val_pivot = int(round(pivot_row[col_idx]))
        val_target = int(round(target_row[col_idx]))

        if val_target == 0:
            return target_row, ""

        lcm_val = mcm(val_pivot, val_target)
        m_pivot = lcm_val // abs(val_pivot)
        m_target = lcm_val // abs(val_target)

        sign = "-"
        if (val_pivot > 0 and val_target < 0) or (val_pivot < 0 and val_target > 0):
            sign = "+"
            m_pivot_calc = m_pivot
        else:
            m_pivot_calc = -m_pivot

        new_row = [
            (m_target * elem_target) + (m_pivot_calc * elem_pivot)
            for elem_target, elem_pivot in zip(target_row, pivot_row)
        ]

        simplified_int = simplificar_fila([int(round(x)) for x in new_row])

        t_str = f"{m_target} · " if m_target != 1 else ""
        p_str = f"{m_pivot} · " if m_pivot != 1 else ""
        op_desc = f"Fila {target_idx + 1} = {t_str}Fila {target_idx + 1} {sign} {p_str}Fila {pivot_idx + 1}"

        return [float(x) for x in simplified_int], op_desc

    def _eliminate_forward(self):
        m = self.matrix.rows
        n = self.matrix.cols
        pivot_row = 0
        pivot_cols = []

        self._log_step("Matriz inicial aumentada [A|b]:", self.matrix)

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

            self._log_step(
                f"Pivote seleccionado en Fila {pivot_row + 1}, Columna {col + 1} (valor = {format_fraction_str(self.matrix.get(pivot_row, col))})",
                self.matrix
            )

            row_piv = self._get_row(pivot_row)
            for r in range(pivot_row + 1, m):
                if abs(self.matrix.get(r, col)) > self.eps:
                    row_target = self._get_row(r)
                    new_row, op_desc = self._eliminate_row_with_lcm(row_piv, row_target, col, r, pivot_row)
                    self._set_row(r, new_row)
                    self._log_step(op_desc, self.matrix)

            pivot_cols.append(col)
            pivot_row += 1
            if pivot_row >= m:
                break

        rank = pivot_row

        # Normalizar pivotes a 1 al finalizar el escalonamiento
        for r, c in enumerate(pivot_cols):
            pivot_val = self.matrix.get(r, c)
            if abs(pivot_val) >= self.eps and abs(pivot_val - 1.0) > self.eps:
                scale = 1.0 / pivot_val
                row = self._get_row(r)
                normalized_row = [elem * scale for elem in row]
                self._set_row(r, normalized_row)
                self._log_step(
                    f"Normalizar pivote: Fila {r + 1} = Fila {r + 1} / {format_fraction_str(pivot_val)}",
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
            free_desc = ", ".join([f"x_{{{c + 1}}} = {free_var_map[c]}" for c in free_cols])
            back_sub_steps.append(f"Variables libres identificadas: {free_desc}")
            for c in free_cols:
                expr_terms[c] = {free_var_map[c]: Fraction(1)}

        for i in range(len(pivot_cols) - 1, -1, -1):
            p_col = pivot_cols[i]
            a_ii = Fraction(self.matrix.get(i, p_col)).limit_denominator(1000)
            b_i = Fraction(self.matrix.get(i, num_vars)).limit_denominator(1000)

            c_val = b_i
            t_val: Dict[str, Fraction] = {}

            for j in range(p_col + 1, num_vars):
                coeff = Fraction(self.matrix.get(i, j)).limit_denominator(1000)
                if coeff != 0:
                    c_val -= coeff * expr_const[j]
                    for var, v_coeff in expr_terms[j].items():
                        t_val[var] = t_val.get(var, Fraction(0)) - (coeff * v_coeff)

            c_val /= a_ii
            t_val = {k: v / a_ii for k, v in t_val.items() if (v / a_ii) != 0}

            expr_const[p_col] = c_val
            expr_terms[p_col] = t_val

            res_str = format_parametric_expr(c_val, t_val)
            back_sub_steps.append(f"x_{{{p_col + 1}}} = {res_str}")

        solution = [format_parametric_expr(expr_const[i], expr_terms[i]) for i in range(num_vars)]
        return solution, back_sub_steps

    def solve(self):
        rank, pivot_cols = self._eliminate_forward()
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