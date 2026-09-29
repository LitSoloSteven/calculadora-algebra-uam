"""Formatters LaTeX específicos de operaciones con matrices.

Viven aquí — y no en `utils/formatters.py` — porque operan sobre la
semántica de matrices en operaciones binarias (renderizado genérico en
bmatrix, suma/resta elemento a elemento, producto matricial), no sobre
números sueltos ni vectores.

Los helpers genéricos (`number_to_latex`, `format_fraction_str`, etc.)
siguen en `utils/formatters.py`. Este módulo importa de allí lo que
necesita, no al revés.

Fase 2 del refactor: extracción mecánica desde `utils/formatters.py`.
Sin cambios de comportamiento. Los 3 helpers son byte a byte idénticos
a los previos; solo cambia su ubicación y pasan a ser parte del
contrato público de `matrix_ops`.
"""
from src.backend.constants import FRACTION_MATCH_TOLERANCE
from src.backend.models.matrix import Matrix
from src.backend.utils.formatters import number_to_latex


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

def partitioned_matrix_to_latex(m: Matrix, num_left_cols: int) -> str:
    """Renderiza una matriz aumentada [A | B] con línea divisoria vertical.

    `num_left_cols` es la cantidad de columnas a la izquierda de la línea.
    Para [A | I] con A de n×n, num_left_cols = n.

    Salida: \\left[ \\begin{array}{c...c|c...c} ... \\end{array} \\right]

    Si num_left_cols no parte la matriz en dos bloques no vacíos,
    cae a `matrix_to_latex` (bmatrix simple).
    """
    total = m.cols
    right = total - num_left_cols
    if num_left_cols < 1 or right < 1:
        return matrix_to_latex(m)

    col_spec = ("c" * num_left_cols) + "|" + ("c" * right)
    rows = []
    for i in range(m.rows):
        row_vals = [number_to_latex(m.get(i, j)) for j in range(total)]
        rows.append(" & ".join(row_vals))
    body = " \\\\ ".join(rows)
    return rf"\left[ \begin{{array}}{{{col_spec}}} {body} \end{{array}} \right]"