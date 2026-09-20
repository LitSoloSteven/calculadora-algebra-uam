from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator


def _eval(expr, matrices):
    return MatrixExpressionEvaluator().evaluate(expr, matrices)


def test_AB_means_A_times_B():
    A = Matrix(1, 1, [[2]])
    B = Matrix(1, 1, [[3]])
    r = _eval("AB", {"A": A, "B": B})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(6)


def test_ABC_means_A_times_B_times_C():
    A = Matrix(1, 1, [[2]])
    B = Matrix(1, 1, [[3]])
    C = Matrix(1, 1, [[4]])
    r = _eval("ABC", {"A": A, "B": B, "C": C})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(24)


def test_A_with_digit_is_name_not_multiplication():
    """A2 se interpreta como nombre 'A2', no como A * 2.
    Preserva retrocompatibilidad con tests y consumidores que usan
    nombres con dígitos."""
    A2 = Matrix(1, 1, [[5]])
    r = _eval("A2", {"A2": A2})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(5)


def test_2A_still_works():
    A = Matrix(1, 1, [[5]])
    r = _eval("2A", {"A": A})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(10)


def test_underscore_name_still_works():
    A_foo = Matrix(1, 1, [[7]])
    r = _eval("A_foo", {"A_foo": A_foo})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(7)


def test_AB_with_explicit_star_still_works():
    A = Matrix(1, 1, [[2]])
    B = Matrix(1, 1, [[3]])
    r = _eval("A*B", {"A": A, "B": B})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(6)


def test_A_plus_B_still_works():
    A = Matrix(1, 1, [[2]])
    B = Matrix(1, 1, [[3]])
    r = _eval("A + B", {"A": A, "B": B})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(5)
    
def test_A3_plus_B3_still_works():
    """El test preexistente que rompió con el fix anterior ahora pasa."""
    A3 = Matrix(2, 2, [[1, 0], [0, 1]])
    B3 = Matrix(2, 2, [[1, 2], [3, 4]])
    r = _eval("A3 + B3", {"A3": A3, "B3": B3})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(2)