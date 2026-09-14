from fractions import Fraction
from typing import Dict
from src.backend.models.matrix import Matrix

def format_fraction_str(val: float | Fraction) -> str:
    """Formatea números como enteros o fracciones simplificadas en texto plano."""
    frac = Fraction(val).limit_denominator(1000)
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def format_parametric_expr(const: Fraction, terms: Dict[str, Fraction]) -> str:
    """
    Convierte términos algebraicos a una cadena paramétrica limpia.
    Ejemplo: const=9, terms={'t': -8} -> "9 - 8t"
    """
    parts = []
    has_const = (const != 0) or not terms

    if has_const:
        parts.append(format_fraction_str(const))

    for var, coeff in terms.items():
        if coeff == 0:
            continue
        abs_c = abs(coeff)
        c_str = "" if abs_c == 1 else format_fraction_str(abs_c)
        
        if not parts:
            prefix = "" if coeff > 0 else "-"
            parts.append(f"{prefix}{c_str}{var}")
        else:
            sign = "+" if coeff > 0 else "-"
            parts.append(f"{sign} {c_str}{var}")

    return " ".join(parts) if parts else "0"


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

def sum_sub_matrix_to_latex(matrix_a: Matrix, matrix_b: Matrix, operator: str = "+") -> str:
    """
    Genera un string LaTeX con la matriz de expresiones sin resolver.
    Ejemplo: [[1+1, 2+2], [3+3, 4+4]]
    """
    rows_str = []
    for r in range(matrix_a.rows):
        row_vals = []
        for c in range(matrix_a.cols):
            a_str = format_fraction_str(matrix_a.get(r, c))
            b_str = format_fraction_str(matrix_b.get(r, c))
            row_vals.append(f"{a_str} {operator} {b_str}")
        rows_str.append(" & ".join(row_vals))
    
    body = " \\\\\n".join(rows_str)
    return f"\\begin{{bmatrix}}\n{body}\n\\end{{bmatrix}}"


def multiply_matrix_to_latex(matrix_a: Matrix, matrix_b: Matrix) -> str:
    """
    Genera un string LaTeX con la matriz de productos y sumas sin resolver.
    Ejemplo: [[(1)(1)+(2)(3), (1)(2)+(2)(4)], ...]
    """
    m, n, q = matrix_a.rows, matrix_a.cols, matrix_b.cols
    rows_str = []

    for r in range(m):
        row_vals = []
        for c in range(q):
            terms = []
            for k in range(n):
                a_str = format_fraction_str(matrix_a.get(r, k))
                b_str = format_fraction_str(matrix_b.get(k, c))
                terms.append(f"({a_str})({b_str})")
            row_vals.append(" + ".join(terms))
        rows_str.append(" & ".join(row_vals))

    body = " \\\\\n".join(rows_str)
    return f"\\begin{{bmatrix}}\n{body}\n\\end{{bmatrix}}"