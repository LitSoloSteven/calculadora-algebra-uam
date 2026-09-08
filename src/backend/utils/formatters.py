from fractions import Fraction
from src.backend.models.matrix import Matrix

def matrix_to_latex(matrix: Matrix, eps: float = 1e-6) -> str:
    rows_str = []
    
    for r in range(matrix.rows):
        row_vals = []
        for c in range(matrix.cols):
            val = matrix.get(r, c)
            
            if abs(val) < eps:
                row_vals.append("0")
            else:
                frac = Fraction(val).limit_denominator(100)
                if abs(float(frac) - val) < 1e-4:
                    if frac.denominator == 1:
                        row_vals.append(str(frac.numerator))
                    else:
                        row_vals.append(f"\\frac{{{frac.numerator}}}{{{frac.denominator}}}")
                else:
                    row_vals.append(f"{val:.4f}".rstrip('0').rstrip('.'))
                    
        rows_str.append(" & ".join(row_vals))
    
    body = " \\\\\n".join(rows_str)
    return f"\\begin{{bmatrix}}\n{body}\n\\end{{bmatrix}}"


def system_to_latex(matrix: Matrix, sorted_vars: list[str] | None = None, eps: float = 1e-6) -> str:
    """
    Convierte una matriz aumentada [A|b] a una representación LaTeX del sistema de ecuaciones
    utilizando el entorno \\begin{cases} ... \\end{cases}.
    """
    num_vars = matrix.cols - 1
    if sorted_vars is None or len(sorted_vars) != num_vars:
        sorted_vars = [f"x_{{{i+1}}}" for i in range(num_vars)]

    eq_lines = []
    
    for r in range(matrix.rows):
        terms = []
        for c, var in enumerate(sorted_vars):
            coeff = matrix.get(r, c)
            if abs(coeff) < eps:
                continue

            frac = Fraction(coeff).limit_denominator(100)
            if abs(float(frac) - coeff) < 1e-4:
                num, den = frac.numerator, frac.denominator
                if abs(num) == 1 and den == 1:
                    coeff_str = "" if num == 1 else "-"
                elif den == 1:
                    coeff_str = str(num)
                else:
                    coeff_str = f"\\frac{{{abs(num)}}}{{{den}}}"
                    if num < 0:
                        coeff_str = "-" + coeff_str
            else:
                coeff_str = f"{coeff:.4f}".rstrip('0').rstrip('.')

            if not terms:
                terms.append(f"{coeff_str}{var}")
            else:
                if coeff_str.startswith("-"):
                    terms.append(f"- {coeff_str[1:]}{var}")
                else:
                    terms.append(f"+ {coeff_str}{var}")

        rhs = matrix.get(r, matrix.cols - 1)
        rhs_frac = Fraction(rhs).limit_denominator(100)
        if abs(float(rhs_frac) - rhs) < 1e-4:
            if rhs_frac.denominator == 1:
                rhs_str = str(rhs_frac.numerator)
            else:
                rhs_str = f"\\frac{{{rhs_frac.numerator}}}{{{rhs_frac.denominator}}}"
        else:
            rhs_str = f"{rhs:.4f}".rstrip('0').rstrip('.')

        lhs_expr = " ".join(terms) if terms else "0"
        eq_lines.append(f"{lhs_expr} = {rhs_str}")

    body = " \\\\\n".join(eq_lines)
    return f"\\begin{{cases}}\n{body}\n\\end{{cases}}"