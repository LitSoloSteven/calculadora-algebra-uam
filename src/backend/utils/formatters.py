from fractions import Fraction
from typing import Dict
from src.backend.models.matrix import Matrix
from src.backend.constants import (
    ZERO_EPSILON,
    FRACTION_MATCH_TOLERANCE,
    DISPLAY_FRACTION_TOLERANCE,  
    DISPLAY_DECIMALS,
    FRACTION_DISPLAY_LIMIT,
    LATEX_DENOMINATOR_LIMIT,
)
import re


def format_variable_for_latex(var_name: str) -> str:
    m = re.match(r'^([a-zA-Z]+)(\d+)$', var_name)
    if m:
        letters, digits = m.groups()
        return f"{letters}_{{{digits}}}"
    if len(var_name) > 1:
        return f"\\text{{{var_name}}}"
    return var_name


def format_fraction_str(val: float | Fraction | int) -> str:
    """Formatea números como fracciones exactas (si ya lo son) o
    recupera una fracción simple desde un float.

    Regla: Fraction/int nunca se aproximan. El limit_denominator solo
    se aplica a float, donde el decimal binario no es la fuente de verdad.
    """
    if isinstance(val, (int, Fraction)):
        f = Fraction(val)
        if f.denominator == 1:
            return str(f.numerator)
        return f"{f.numerator}/{f.denominator}"

    if isinstance(val, float):
        if abs(val) < ZERO_EPSILON:
            return "0"
        frac = Fraction(val).limit_denominator(FRACTION_DISPLAY_LIMIT)
        if abs(float(frac) - val) < DISPLAY_FRACTION_TOLERANCE:
            if frac.denominator == 1:
                return str(frac.numerator)
            return f"{frac.numerator}/{frac.denominator}"
        return f"{val:.{DISPLAY_DECIMALS}f}".rstrip('0').rstrip('.')

    return str(val)

def number_to_latex(val: float | Fraction | int) -> str:
    """Convierte un número a LaTeX. Fraction/int son exactos; float
    intenta recuperar una fracción simple y sino cae a decimal."""
    if isinstance(val, (int, Fraction)):
        f = Fraction(val)
        if f == 0:
            return "0"
        num, den = f.numerator, f.denominator
        if den == 1:
            return str(num)
        sign = "-" if num < 0 else ""
        return f"{sign}\\frac{{{abs(num)}}}{{{den}}}"

    if isinstance(val, float):
        if abs(val) < FRACTION_MATCH_TOLERANCE:
            return "0"
        frac = Fraction(val).limit_denominator(LATEX_DENOMINATOR_LIMIT)
        if abs(float(frac) - val) < DISPLAY_FRACTION_TOLERANCE:
            num, den = frac.numerator, frac.denominator
            if den == 1:
                return str(num)
            sign = "-" if num < 0 else ""
            return f"{sign}\\frac{{{abs(num)}}}{{{den}}}"
        return f"{val:.{DISPLAY_DECIMALS}f}".rstrip('0').rstrip('.')

    return str(val)

def format_parametric_expr(const: Fraction, terms: Dict[str, Fraction]) -> str:
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


def matrix_to_latex(matrix: Matrix, eps: float = FRACTION_MATCH_TOLERANCE) -> str:
    rows_str = []
    for r in range(matrix.rows):
        row_vals = [number_to_latex(matrix.get(r, c)) for c in range(matrix.cols)]
        rows_str.append(" & ".join(row_vals))
    body = " \\\\\n".join(rows_str)
    return f"\\begin{{bmatrix}}\n{body}\n\\end{{bmatrix}}"


def sum_sub_matrix_to_latex(matrix_a: Matrix, matrix_b: Matrix, operator: str = "+") -> str:
    rows_str = []
    for r in range(matrix_a.rows):
        row_vals = []
        for c in range(matrix_a.cols):
            a_str = number_to_latex(matrix_a.get(r, c))
            b_str = number_to_latex(matrix_b.get(r, c))
            a_fmt = f"({a_str})" if a_str.startswith("-") else a_str
            b_fmt = f"({b_str})" if b_str.startswith("-") else b_str
            row_vals.append(f"{a_fmt} {operator} {b_fmt}")
        rows_str.append(" & ".join(row_vals))
    body = " \\\\\n".join(rows_str)
    return f"\\begin{{bmatrix}}\n{body}\n\\end{{bmatrix}}"


def multiply_matrix_to_latex(matrix_a: Matrix, matrix_b: Matrix) -> str:
    m, n, q = matrix_a.rows, matrix_a.cols, matrix_b.cols
    rows_str = []
    for r in range(m):
        row_vals = []
        for c in range(q):
            terms = []
            for k in range(n):
                a_str = number_to_latex(matrix_a.get(r, k))
                b_str = number_to_latex(matrix_b.get(k, c))
                terms.append(f"({a_str})({b_str})")
            row_vals.append(" + ".join(terms))
        rows_str.append(" & ".join(row_vals))
    body = " \\\\\n".join(rows_str)
    return f"\\begin{{bmatrix}}\n{body}\n\\end{{bmatrix}}"