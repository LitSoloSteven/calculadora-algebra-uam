import pytest
from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator
from src.backend.utils.parsers import SystemParser
from src.backend.exceptions import DimensionMismatchError


# ============================================================
# 1. MatrixOpsSolver con dimensiones incompatibles
# ============================================================

def test_matrix_ops_add_dimension_mismatch():
    A = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    B = Matrix(3, 2, [[1, 2], [3, 4], [5, 6]])
    res = MatrixOpsSolver().add(A, B)
    assert res["status"] == "ERROR"
    assert "Dimensiones incompatibles" in res["message"]


def test_matrix_ops_subtract_dimension_mismatch():
    A = Matrix(2, 2, [[1, 2], [3, 4]])
    B = Matrix(1, 2, [[1, 2]])
    res = MatrixOpsSolver().subtract(A, B)
    assert res["status"] == "ERROR"
    assert "Dimensiones incompatibles" in res["message"]


def test_matrix_ops_multiply_dimension_mismatch():
    A = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    B = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    # A.cols=3 != B.rows=2
    res = MatrixOpsSolver().multiply(A, B)
    assert res["status"] == "ERROR"
    assert "Dimensiones incompatibles" in res["message"]


def test_validate_same_dimensions_raises_domain_error():
    A = Matrix(2, 2)
    B = Matrix(3, 3)
    from src.backend.utils.validators import validate_same_dimensions
    with pytest.raises(DimensionMismatchError):
        validate_same_dimensions(A, B)


def test_validate_multiplication_dimensions_raises_domain_error():
    A = Matrix(2, 3)
    B = Matrix(2, 3)
    from src.backend.utils.validators import validate_multiplication_dimensions
    with pytest.raises(DimensionMismatchError):
        validate_multiplication_dimensions(A, B)


# ============================================================
# 2. Matrix.get fuera de rango y fila irregular
# ============================================================

def test_matrix_get_out_of_bounds_negative():
    m = Matrix(2, 2, [[1, 2], [3, 4]])
    with pytest.raises(IndexError):
        m.get(-1, 0)


def test_matrix_get_out_of_bounds_row():
    m = Matrix(2, 2, [[1, 2], [3, 4]])
    with pytest.raises(IndexError):
        m.get(2, 0)


def test_matrix_get_out_of_bounds_col():
    m = Matrix(2, 2, [[1, 2], [3, 4]])
    with pytest.raises(IndexError):
        m.get(0, 2)


def test_matrix_ragged_data_raises():
    from src.backend.exceptions import MatrixDataError
    with pytest.raises(MatrixDataError):
        Matrix(2, 2, [[1, 2], [3]])   # segunda fila con 1 columna


# ============================================================
# 3. Precedencia del menos unario
# ============================================================

def test_unary_minus_before_matrix():
    """A*-B se evalúa como A*(-B), no como (A*0)-B."""
    A = Matrix(1, 1, [[2]])
    B = Matrix(1, 1, [[3]])
    ev = MatrixExpressionEvaluator()
    r = ev.evaluate("A*-B", {"A": A, "B": B})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(-6)


def test_double_unary_minus():
    """--A se evalúa como -(-A) = A."""
    A = Matrix(1, 1, [[5]])
    ev = MatrixExpressionEvaluator()
    r = ev.evaluate("--A", {"A": A})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(5)


def test_unary_minus_at_start():
    """-A en posición inicial."""
    A = Matrix(1, 1, [[7]])
    ev = MatrixExpressionEvaluator()
    r = ev.evaluate("-A", {"A": A})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(-7)


def test_unary_minus_in_parentheses():
    """(-A) preserva el signo correctamente."""
    A = Matrix(1, 1, [[3]])
    ev = MatrixExpressionEvaluator()
    r = ev.evaluate("(-A)", {"A": A})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(-3)


# ============================================================
# 4. Parser con constante en el lado izquierdo
# ============================================================

def test_parser_shifts_constant_from_lhs():
    """2x + 5 = 10 debe interpretarse como 2x = 5."""
    raw = "2x + 5 = 10"
    ok, matrix, variables, msg = SystemParser.parse_system(raw)
    assert ok, msg
    assert variables == ["x"]
    # A[0,0]=2, b[0]=5 (10 - 5)
    assert matrix.get(0, 0) == Fraction(2)
    assert matrix.get(0, 1) == Fraction(5)


def test_parser_multiple_lhs_constants():
    """x + 1 + 2 = 10 → x = 7."""
    raw = "x + 1 + 2 = 10"
    ok, matrix, _, msg = SystemParser.parse_system(raw)
    assert ok, msg
    assert matrix.get(0, 0) == Fraction(1)
    assert matrix.get(0, 1) == Fraction(7)


def test_parser_negative_lhs_constant():
    """x - 3 = 5 → x = 8."""
    raw = "x - 3 = 5"
    ok, matrix, _, msg = SystemParser.parse_system(raw)
    assert ok, msg
    assert matrix.get(0, 0) == Fraction(1)
    assert matrix.get(0, 1) == Fraction(8)


def test_parser_rejects_variable_on_rhs():
    """El parser actual no soporta variables en el RHS. Documentamos
    el comportamiento (backlog)."""
    raw = "2x + 3 = x + 5"
    ok, _, _, msg = SystemParser.parse_system(raw)
    assert not ok  # ← documenta limitación actual