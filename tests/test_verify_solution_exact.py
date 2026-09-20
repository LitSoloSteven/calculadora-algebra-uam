from fractions import Fraction
from src.backend.utils.validators import MatrixValidator


# --- Verificación exacta ---

def test_exact_fraction_passes():
    ok, _ = MatrixValidator.verify_solution(
        [[Fraction(1001)]], [Fraction(1, 1001)], [Fraction(1)]
    )
    assert ok


def test_approximate_solution_fails():
    """Solución aproximada NO debe pasar la verificación exacta."""
    ok, report = MatrixValidator.verify_solution(
        [[Fraction(1)]], [Fraction(1, 1000)], [Fraction(1, 1001)]
    )
    assert not ok
    assert "Incorrecto" in report[0]


def test_string_inputs_are_parsed_exactly():
    ok, _ = MatrixValidator.verify_solution([["1001"]], ["1/1001"], ["1"])
    assert ok


def test_simple_fraction_passes():
    ok, _ = MatrixValidator.verify_solution(
        [[Fraction(2), Fraction(3)]],
        [Fraction(1, 2), Fraction(1, 3)],
        [Fraction(2)],
    )
    assert ok


def test_incorrect_solution_fails():
    ok, report = MatrixValidator.verify_solution(
        [[Fraction(1)]], [Fraction(5)], [Fraction(3)]
    )
    assert not ok
    assert "Incorrecto" in report[0]


# --- Falla silenciosa eliminada ---

def test_invalid_cell_in_A_reports_error():
    ok, report = MatrixValidator.verify_solution(
        [["abc"]], [Fraction(1)], [Fraction(1)]
    )
    assert not ok
    assert "A[1,1]" in report[0]


def test_invalid_cell_in_x_reports_error():
    ok, report = MatrixValidator.verify_solution(
        [[Fraction(1)]], ["xyz"], [Fraction(1)]
    )
    assert not ok
    assert "x[1]" in report[0]


def test_invalid_cell_in_b_reports_error():
    ok, report = MatrixValidator.verify_solution(
        [[Fraction(1)]], [Fraction(1)], ["oops"]
    )
    assert not ok
    assert "b[1]" in report[0]


# --- Display sigue funcionando ---

def test_latex_display_shows_exact_fraction():
    ok, report = MatrixValidator.verify_solution(
        [[Fraction(7)]], ["9/7"], [Fraction(9)], as_latex=True
    )
    assert ok
    assert r"\frac{9}{7}" in report[0]


def test_plain_display_shows_exact_fraction():
    ok, report = MatrixValidator.verify_solution(
        [[Fraction(7)]], [Fraction(9, 7)], [Fraction(9)], as_latex=False
    )
    assert ok
    assert "9/7" in report[0]