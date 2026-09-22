import html
import re
import pytest
from src.backend.utils.validators import MatrixValidator


def build_preview_latex(matrix_A, vector_b):
    """Lógica exacta de construcción de LaTeX de LinearSystemsResultsMixin._update_preview."""
    if not matrix_A or len(matrix_A) == 0 or len(matrix_A[0]) == 0:
        return None, "La matriz está vacía."

    m = len(matrix_A)
    n = len(matrix_A[0])

    def sanitize(val):
        if not val:
            return '0'
        success, _, _ = MatrixValidator.parse_number_exact(val)
        if not success:
            return r"\color{gray}{?}"
        return val

    # Construir LaTeX para matriz aumentada
    latex_lines = []
    for i, row in enumerate(matrix_A):
        row_strs = [sanitize(val) for val in row]
        b_val = sanitize(vector_b[i] if i < len(vector_b) else '0')
        latex_lines.append(" & ".join(row_strs) + f" & {b_val}")

    spec = "c" * n + "|c"
    matrix_tex = rf"\left[ \begin{{array}}{{{spec}}} " + r" \\ ".join(latex_lines) + r" \end{array} \right]"
    matrix_tex = html.escape(matrix_tex)

    if m * n > 48:
        return matrix_tex, "Sistema demasiado grande para vista previa en ecuaciones."

    # Validar celdas antes de exportar a ecuaciones
    todas_validas = True
    for i in range(m):
        for j in range(n):
            val = matrix_A[i][j]
            if val:
                success, _, _ = MatrixValidator.parse_number_exact(val)
                if not success:
                    todas_validas = False
                    break
        if not todas_validas:
            break

    b_valid = True
    for i in range(m):
        val = vector_b[i] if i < len(vector_b) else ''
        if val:
            success, _, _ = MatrixValidator.parse_number_exact(val)
            if not success:
                b_valid = False
                break

    if not todas_validas or not b_valid:
        return matrix_tex, "Corrige los valores inválidos para ver las ecuaciones."

    # Simular export_to_equations
    ecuaciones = []
    for i, row in enumerate(matrix_A):
        terms = []
        for j, val in enumerate(row):
            if val and val != '0':
                success, _, _ = MatrixValidator.parse_number_exact(val)
                if not success:
                    continue
                sign = "-" if val.startswith("-") else "+"
                val_abs = val.lstrip("+-").strip()
                term = f"x{j+1}" if (val_abs == "1" or val_abs == "") else f"{val_abs}x{j+1}"
                if not terms and sign == "+":
                    terms.append(term)
                elif not terms and sign == "-":
                    terms.append(f"-{term}")
                else:
                    terms.append(f"{sign} {term}")
        if not terms:
            if vector_b[i] and vector_b[i] != '0':
                ecuaciones.append(f"0 = {vector_b[i]}")
        else:
            b_str = vector_b[i] if vector_b[i] else '0'
            ecuaciones.append(" ".join(terms) + f" = {b_str}")

    if not ecuaciones:
        return matrix_tex, "No hay ecuaciones válidas."

    eqs_tex = r" \\ ".join(ecuaciones)
    eqs_tex = re.sub(r'x(\d+)', r'x_{\1}', eqs_tex)
    system_tex = r" \begin{cases} " + eqs_tex + r" \end{cases} "
    system_tex = html.escape(system_tex)

    return matrix_tex, system_tex


def test_preview_no_double_braces_in_end_array():
    """Bug 1: Asegura que el cierre del array usa \\end{array} y nunca \\end{{array}}."""
    matrix_A = [["1", "2"], ["3", "4"]]
    vector_b = ["5", "6"]
    m_tex, _ = build_preview_latex(matrix_A, vector_b)
    
    assert r"\begin{array}" in m_tex
    assert r"\end{array}" in m_tex
    assert "{{array}}" not in m_tex
    assert "}}" not in m_tex


def test_preview_empty_matrix_shows_valid_augmented_and_no_equations():
    """Para matriz vacía (todas las celdas ''), la matriz aumentada se rellena con 0

    y el sistema de ecuaciones reporta 'No hay ecuaciones válidas.' sin error."""
    matrix_A = [["", ""], ["", ""]]
    vector_b = ["", ""]
    m_tex, s_msg = build_preview_latex(matrix_A, vector_b)

    assert r"\begin{array}{cc|c}" in m_tex
    assert r"\end{array}" in m_tex
    assert "{{array}}" not in m_tex
    assert s_msg == "No hay ecuaciones válidas."


@pytest.mark.parametrize("dim", range(1, 11))
def test_preview_all_dimensions_1_to_10(dim):
    """Verifica dimensiones desde 1x1 hasta 10x10, tanto vacías como llenas."""
    # Caso vacía
    mat_empty = [["" for _ in range(dim)] for _ in range(dim)]
    vec_empty = ["" for _ in range(dim)]
    m_tex, s_res = build_preview_latex(mat_empty, vec_empty)

    assert r"\begin{array}" in m_tex
    assert r"\end{array}" in m_tex
    assert "{{array}}" not in m_tex
    assert s_res == "No hay ecuaciones válidas." or "demasiado grande" in s_res

    # Caso con datos
    mat_val = [[str(i * dim + j + 1) for j in range(dim)] for i in range(dim)]
    vec_val = [str(i + 1) for i in range(dim)]
    m_tex_val, s_res_val = build_preview_latex(mat_val, vec_val)

    assert r"\begin{array}" in m_tex_val
    assert r"\end{array}" in m_tex_val
    assert "{{array}}" not in m_tex_val

    if dim * dim <= 48:
        assert r"\begin{cases}" in s_res_val
        assert r"\end{cases}" in s_res_val
        assert "{{cases}}" not in s_res_val
    else:
        assert s_res_val == "Sistema demasiado grande para vista previa en ecuaciones."
