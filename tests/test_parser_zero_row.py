from fractions import Fraction
from src.backend.utils.parsers import SystemParser
from src.backend.solvers.linear_systems.gauss import GaussSolver


def test_zero_equals_nonzero_with_variables():
    """0 = 5 junto a otras ecuaciones produce fila [0...0|5]."""
    raw = "x + y = 3\n0 = 5"
    ok, matrix, variables, msg = SystemParser.parse_system(raw)
    assert ok, msg
    assert variables == ["x", "y"]
    assert matrix.rows == 2
    assert matrix.cols == 3
    assert matrix.get(0, 0) == Fraction(1)
    assert matrix.get(0, 1) == Fraction(1)
    assert matrix.get(0, 2) == Fraction(3)
    assert matrix.get(1, 0) == Fraction(0)
    assert matrix.get(1, 1) == Fraction(0)
    assert matrix.get(1, 2) == Fraction(5)


def test_zero_equals_nonzero_produces_no_solution():
    """El solver detecta la inconsistencia."""
    raw = "x + y = 3\n0 = 5"
    ok, matrix, _, _ = SystemParser.parse_system(raw)
    assert ok
    r = GaussSolver(matrix).solve()
    assert r["status"] == "NO_SOLUTION"


def test_zero_equals_zero_is_zero_row():
    """0 = 0 produce una fila de ceros legítima."""
    raw = "x = 1\n0 = 0"
    ok, matrix, _, msg = SystemParser.parse_system(raw)
    assert ok, msg
    assert matrix.get(1, 0) == Fraction(0)
    assert matrix.get(1, 1) == Fraction(0)


def test_all_rows_without_variables_is_rejected():
    """Sin variables globales, sigue rechazando."""
    ok, _, _, msg = SystemParser.parse_system("0 = 5")
    assert not ok
    assert "variable" in msg.lower()


def test_pure_number_lhs_shifts_to_rhs():
    """5 = 3 con otra ecuación con variables → fila [0, -2]."""
    raw = "x = 1\n5 = 3"
    ok, matrix, _, msg = SystemParser.parse_system(raw)
    assert ok, msg
    # 5 = 3 → 0 = 3 - 5 = -2
    assert matrix.get(1, 0) == Fraction(0)
    assert matrix.get(1, 1) == Fraction(-2)