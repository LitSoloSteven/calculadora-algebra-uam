from fractions import Fraction
from src.backend.utils.validators import MatrixValidator


def test_verify_solution_shows_exact_fractions_in_latex():
    """La comprobación debe mostrar 9/7, no 1.2857142857142858."""
    A = [[Fraction(7)]]
    x = ["9/7"]
    b = [Fraction(9)]
    ok, report = MatrixValidator.verify_solution(A, x, b, as_latex=True)
    assert ok
    assert r"\frac{9}{7}" in report[0]
    assert "1.2857" not in report[0]


def test_verify_solution_shows_exact_fractions_plain():
    A = [[Fraction(7)]]
    x = [Fraction(9, 7)]
    b = [Fraction(9)]
    ok, report = MatrixValidator.verify_solution(A, x, b, as_latex=False)
    assert ok
    assert "9/7" in report[0]
    assert "1.2857" not in report[0]


def test_verify_solution_correct_after_display_change():
    """El cambio es de display: la verificación sigue validando bien."""
    A = [[Fraction(1), Fraction(1)]]
    x = ["1/2", "1/2"]
    b = [Fraction(1)]
    ok, _ = MatrixValidator.verify_solution(A, x, b)
    assert ok


def test_verify_solution_detects_incorrect_values():
    """Si la solución no satisface, el reporte lo marca como Incorrecto."""
    A = [[Fraction(1)]]
    x = ["1/2"]
    b = [Fraction(9)]
    ok, report = MatrixValidator.verify_solution(A, x, b)
    assert not ok
    assert "Incorrecto" in report[0]


def test_verify_solution_lhs_displays_integer_cleanly():
    """El resultado de la suma debe verse como 2, no 2.0."""
    A = [[Fraction(1), Fraction(1)]]
    x = ["1", "1"]
    b = [Fraction(2)]
    ok, report = MatrixValidator.verify_solution(A, x, b)
    assert ok
    assert "= 2 " in report[0] or "= 2  " in report[0]
    assert "= 2.0" not in report[0]