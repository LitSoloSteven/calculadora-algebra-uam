from fractions import Fraction
from src.backend.utils.formatters import format_fraction_str, number_to_latex
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver


# --- format_fraction_str: exactitud con Fraction/int ---

def test_format_fraction_str_exact_fraction_above_limit():
    """El caso estrella: 1/1001 no debe convertirse en 1/1000."""
    assert format_fraction_str(Fraction(1, 1001)) == "1/1001"


def test_format_fraction_str_above_1000():
    assert format_fraction_str(Fraction(123, 4567)) == "123/4567"


def test_format_fraction_str_integer_fraction():
    assert format_fraction_str(Fraction(5, 1)) == "5"
    assert format_fraction_str(5) == "5"
    assert format_fraction_str(Fraction(0)) == "0"


def test_format_fraction_str_keeps_simple_fraction():
    assert format_fraction_str(Fraction(1, 7)) == "1/7"
    assert format_fraction_str(Fraction(-3, 2)) == "-3/2"


def test_format_fraction_str_float_still_recovers_simple_fraction():
    """El path float no cambia: 0.5 -> 1/2."""
    assert format_fraction_str(0.5) == "1/2"
    assert format_fraction_str(0.33333) == "1/3"


# --- number_to_latex: exactitud con Fraction/int ---

def test_number_to_latex_does_not_replace_exact_fraction():
    assert number_to_latex(Fraction(1, 101)) == r"\frac{1}{101}"


def test_number_to_latex_above_100():
    assert number_to_latex(Fraction(1, 1001)) == r"\frac{1}{1001}"


def test_number_to_latex_integer():
    assert number_to_latex(Fraction(5, 1)) == "5"
    assert number_to_latex(0) == "0"
    assert number_to_latex(Fraction(0)) == "0"


def test_number_to_latex_negative_fraction():
    assert number_to_latex(Fraction(-2, 3)) == r"-\frac{2}{3}"


def test_number_to_latex_float_still_recovers_simple_fraction():
    assert number_to_latex(0.5) == r"\frac{1}{2}"


# --- Integración: solución de Gauss no se trunca ---

def test_solution_keeps_denominator_above_display_limit():
    """1001x = 1 -> x = 1/1001, no 1/1000."""
    solver = GaussSolver(Matrix(1, 2, [[1001, 1]]))
    result = solver.solve()
    assert result["solution"] == ["1/1001"]


def test_solution_keeps_simple_fraction():
    """Sanity: 7x = 2 -> x = 2/7."""
    solver = GaussSolver(Matrix(1, 2, [[7, 2]]))
    result = solver.solve()
    assert result["solution"] == ["2/7"]