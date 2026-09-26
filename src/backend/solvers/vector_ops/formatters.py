"""Helpers de formato LaTeX específicos del dominio vectorial.

Viven aquí — y no en `src/backend/utils/formatters.py` — porque operan
sobre la semántica de vectores en R^n (columnas vs filas, matrices
aumentadas con barra, combinaciones lineales con nombres con subíndice),
no sobre números o matrices genéricas.

Los helpers verdaderamente genéricos (number_to_latex, format_fraction_str,
matrix_to_latex, etc.) siguen en `utils/formatters.py`. Este módulo importa
de allí lo que necesita, no al revés.

Fase 1 del refactor: extracción mecánica desde `operations.py`. Sin cambios
de comportamiento. Fase 2 (futuro): consolidar con formatters de matrix_ops
si aparece duplicación real.
"""
from fractions import Fraction
import re

from src.backend.models.matrix import Matrix
from src.backend.utils.formatters import number_to_latex


def vector_to_latex(v: Matrix) -> str:
    """Renderiza un vector como matriz LaTeX \\begin{bmatrix} ... \\end{bmatrix}.

    Acepta vectores fila (1×n) y columna (n×1). El shape determina el
    separador: `&` para filas, `\\\\` para columnas.
    """
    if v.rows == 1 and v.cols > 1:
        cols = [number_to_latex(v.get(0, j)) for j in range(v.cols)]
        return r"\begin{bmatrix} " + r" & ".join(cols) + r" \end{bmatrix}"
    rows = [number_to_latex(v.get(i, 0)) for i in range(v.rows)]
    return r"\begin{bmatrix} " + r" \\ ".join(rows) + r" \end{bmatrix}"


def col_vector_to_latex(v: Matrix) -> str:
    """Renderiza un vector columna como matriz LaTeX \\begin{bmatrix} ... \\end{bmatrix}."""
    return vector_to_latex(v)


def augmented_gauss_matrix_to_latex(m: Matrix, num_vars: int | None = None) -> str:
    """Renderiza una matriz aumentada [A|b] con barra divisoria vertical."""
    vars_count = (m.cols - 1) if num_vars is None else num_vars
    col_spec = ("c" * vars_count) + "|c"
    rows = []
    for i in range(m.rows):
        row_vals = [number_to_latex(m.get(i, j)) for j in range(m.cols)]
        rows.append(" & ".join(row_vals))
    body = " \\\\ ".join(rows)
    return rf"\left[ \begin{{array}}{{{col_spec}}} {body} \end{{array}} \right]"


def format_var_latex(var_name: str) -> str:
    """Normaliza el nombre de una variable a LaTeX math mode.

    Acepta `x_1` y `x1` (guion bajo opcional). Si ya viene con backslash
    asume que el caller sabe lo que hace y lo devuelve tal cual.
    """
    if var_name.startswith("\\"):
        return var_name
    m = re.match(r'^([a-zA-Z]+)_?(\d+)$', var_name)
    if m:
        letters, digits = m.groups()
        return f"{letters}_{{{digits}}}"
    return var_name


def format_vec_latex(vec_name: str) -> str:
    """Formatea el símbolo de un vector en negrita canónica LaTeX."""
    if vec_name.startswith(r"\mathbf{"):
        return vec_name
    m = re.match(r'^([a-zA-Z]+)_?(\d+)$', vec_name)
    if m:
        letters, digits = m.groups()
        if len(digits) == 1:
            return rf"\mathbf{{{letters}}}_{digits}"
        return rf"\mathbf{{{letters}}}_{{{digits}}}"
    return rf"\mathbf{{{vec_name}}}"


def format_scalar_component(val: Fraction | int | float, var: str) -> str:
    """Multiplicación de escalar por variable para las entradas de Paso 2."""
    f = Fraction(val)
    if f == 0:
        return "0"
    if f == 1:
        return var
    if f == -1:
        return f"-{var}"
    if f.denominator == 1:
        return f"{f.numerator} {var}"
    return f"{number_to_latex(f)} {var}"


def format_linear_expression(coeffs: list[Fraction | int | float], vars: list[str]) -> str:
    """Combina los términos de una fila en una expresión lineal respetando signos (+ y -)."""
    parts = []
    for c_raw, var in zip(coeffs, vars):
        c = Fraction(c_raw)
        if c == 0:
            continue

        abs_c = abs(c)
        if abs_c == 1:
            term = var
        elif abs_c.denominator == 1:
            term = f"{abs_c.numerator} {var}"
        else:
            term = f"{number_to_latex(abs_c)} {var}"

        if not parts:
            parts.append(f"-{term}" if c < 0 else term)
        else:
            sign = "-" if c < 0 else "+"
            parts.append(f"{sign} {term}")

    return " ".join(parts) if parts else "0"


def augmented_matrix_to_latex(vectors: list[Matrix], b: Matrix) -> str:
    """Renderiza la matriz aumentada [A | b] con línea divisoria [array{c...c|c}]."""
    k = len(vectors)
    n = b.rows
    col_spec = ("c" * k) + "|c"
    rows = []
    for i in range(n):
        row_vals = [number_to_latex(vectors[j].get(i, 0)) for j in range(k)]
        row_vals.append(number_to_latex(b.get(i, 0)))
        rows.append(" & ".join(row_vals))
    body = " \\\\ ".join(rows)
    return rf"\left[ \begin{{array}}{{{col_spec}}} {body} \end{{array}} \right]"


def format_vector_linear_combination(
    coeffs: list[Fraction | int | float], vec_names: list[str]
) -> str:
    """Formatea la combinación escalar-vector para la comprobación formal."""
    parts = []
    for c_raw, v_name in zip(coeffs, vec_names):
        c = Fraction(c_raw)
        v_tex = format_vec_latex(v_name)
        if c == 0:
            continue

        abs_c = abs(c)
        if abs_c == 1:
            term = v_tex
        elif abs_c.denominator == 1:
            term = f"{abs_c.numerator}{v_tex}"
        else:
            term = f"{number_to_latex(abs_c)}{v_tex}"

        if not parts:
            parts.append(f"-{term}" if c < 0 else term)
        else:
            sign = "-" if c < 0 else "+"
            parts.append(f"{sign} {term}")

    return " ".join(parts) if parts else "0"