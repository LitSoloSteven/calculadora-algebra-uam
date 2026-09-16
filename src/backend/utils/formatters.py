from fractions import Fraction
from typing import Dict
from src.backend.models.matrix import Matrix

def format_fraction_str(val: float | Fraction) -> str:
    """Formatea números como enteros o fracciones simplificadas en texto plano."""
    if abs(val) < 1e-9:
        return "0"
    frac = Fraction(val).limit_denominator(1000)
    if abs(float(frac) - val) < 1e-4:
        if frac.denominator == 1:
            return str(frac.numerator)
        return f"{frac.numerator}/{frac.denominator}"
    return f"{float(val):.4f}".rstrip('0').rstrip('.')

def number_to_latex(val: float | Fraction, eps: float = 1e-6) -> str:
    """Convierte un número a su representación en LaTeX centralizada (fracción o decimal)."""
    if abs(val) < eps:
        return "0"
    
    frac = Fraction(val).limit_denominator(100)
    if abs(float(frac) - val) < 1e-4:
        num, den = frac.numerator, frac.denominator
        if den == 1:
            return str(num)
        
        # Manejo del signo para LaTeX: -\frac{a}{b}
        sign = "-" if num < 0 else ""
        return f"{sign}\\frac{{{abs(num)}}}{{{den}}}"
    
    return f"{float(val):.4f}".rstrip('0').rstrip('.')

def format_parametric_expr(const: Fraction, terms: Dict[str, Fraction]) -> str:
    """Convierte términos algebraicos a una cadena paramétrica limpia."""
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
        row_vals = [number_to_latex(matrix.get(r, c), eps) for c in range(matrix.cols)]
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
            
            # Envolver en paréntesis si tiene un signo menos inicial para evitar +-
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
