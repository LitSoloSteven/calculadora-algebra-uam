from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator


def _scalar_product(token: str, scalar_in_matrix: Fraction) -> Fraction:
    """Helper: evalúa `token * A` con A = [[scalar]] y devuelve la celda."""
    ev = MatrixExpressionEvaluator()
    A = Matrix(1, 1, [[scalar_in_matrix]])
    r = ev.evaluate(f"{token}A", {"A": A})
    assert r["status"] == "SUCCESS", r.get("message")
    return r["result_matrix"].data[0][0]


def test_tiny_decimal_is_not_truncated_to_zero():
    """0.0000001 no debe convertirse en 0."""
    result = _scalar_product("0.0000001", Fraction(1))
    assert result == Fraction(1, 10_000_000)


def test_pi_decimal_is_exact():
    """3.14159265 debe quedar como fracción exacta, no aproximada."""
    result = _scalar_product("3.14159265", Fraction(1))
    assert result == Fraction(62831853, 20_000_000)


def test_simple_decimal_is_exact():
    """0.5 → 1/2, sigue funcionando."""
    result = _scalar_product("0.5", Fraction(1))
    assert result == Fraction(1, 2)


def test_integer_literal_is_exact():
    """5 → 5."""
    result = _scalar_product("5", Fraction(1))
    assert result == Fraction(5)


def test_large_denominator_literal():
    """0.000001234 → 617/500000000 exacto."""
    result = _scalar_product("0.000001234", Fraction(1))
    assert result == Fraction(1234, 1_000_000_000)