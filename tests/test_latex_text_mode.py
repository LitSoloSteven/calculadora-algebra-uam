from fractions import Fraction
from src.backend.utils.formatters import format_parametric_expr
from src.backend.utils.validators import MatrixValidator
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver


# --- format_parametric_expr: coeficientes fraccionarios ---

def test_fractional_coefficient_uses_parentheses():
    assert format_parametric_expr(Fraction(0), {"t": Fraction(1, 2)}) == "(1/2)t"


def test_negative_fractional_coefficient_uses_parentheses():
    assert format_parametric_expr(Fraction(0), {"t": Fraction(-1, 2)}) == "-(1/2)t"


def test_integer_coefficient_unchanged():
    assert format_parametric_expr(Fraction(0), {"t": Fraction(2)}) == "2t"
    assert format_parametric_expr(Fraction(0), {"t": Fraction(-3)}) == "-3t"


def test_coefficient_one_and_minus_one():
    assert format_parametric_expr(Fraction(0), {"t": Fraction(1)}) == "t"
    assert format_parametric_expr(Fraction(0), {"t": Fraction(-1)}) == "-t"


def test_lone_fraction_constant():
    assert format_parametric_expr(Fraction(1, 2), {}) == "1/2"


def test_fraction_constant_plus_fractional_term():
    result = format_parametric_expr(Fraction(1, 2), {"t": Fraction(-1, 3)})
    assert result == "1/2 - (1/3)t"


# --- verify_solution: texto en modo matemático ---

def test_verify_solution_wraps_equation_label_in_text():
    _, r = MatrixValidator.verify_solution(
        [[Fraction(7)]], [Fraction(9, 7)], [Fraction(9)], as_latex=True
    )
    assert r"\text{Ecuación 1: }" in r[0]


def test_verify_solution_status_is_in_text():
    _, r = MatrixValidator.verify_solution(
        [[Fraction(1)]], [Fraction(1)], [Fraction(1)], as_latex=True
    )
    assert r"\text{Correcto}" in r[0]


# --- back_substitute: encabezado en \text{} ---

def test_back_substitute_free_vars_header_is_text():
    m = Matrix(1, 4, [[1, 1, 1, 1]])
    r = GaussSolver(m).solve()
    assert r["status"] == "INFINITE_SOLUTIONS"
    assert any(
        s.startswith(r"\text{Variables libres identificadas: }")
        for s in r["back_substitution_steps"]
    )


def test_back_substitute_var_line_has_no_raw_text():
    m = Matrix(1, 4, [[1, 1, 1, 1]])
    r = GaussSolver(m).solve()
    # La línea de x_1 = ... no debe tener texto plano (solo el header lo tiene)
    var_lines = [s for s in r["back_substitution_steps"] if not s.startswith(r"\text{")]
    assert len(var_lines) >= 1
    # Y no debe contener palabras sueltas en español
    for line in var_lines:
        assert "identificadas" not in line
        assert "libres" not in line