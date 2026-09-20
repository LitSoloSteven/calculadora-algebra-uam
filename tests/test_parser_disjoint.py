from fractions import Fraction
from src.backend.utils.parsers import SystemParser


def test_disjoint_system_is_accepted_by_default():
    """Sistema con dos ecuaciones disjuntas se acepta (modo permisivo)."""
    raw = "x1 = 1\nx2 = 2"
    ok, matrix, variables, msg = SystemParser.parse_system(raw)
    assert ok, msg
    assert variables == ["x1", "x2"]
    assert matrix.rows == 2
    assert matrix.cols == 3
    # Fila 0: [1, 0 | 1] ; Fila 1: [0, 1 | 2]
    assert matrix.get(0, 0) == Fraction(1)
    assert matrix.get(0, 1) == Fraction(0)
    assert matrix.get(0, 2) == Fraction(1)
    assert matrix.get(1, 0) == Fraction(0)
    assert matrix.get(1, 1) == Fraction(1)
    assert matrix.get(1, 2) == Fraction(2)


def test_strict_mode_still_rejects_disjoint():
    """Con strict_variables=True, la validación sigue activa."""
    raw = "x1 = 1\nx2 = 2"
    ok, _, _, msg = SystemParser.parse_system(raw, strict_variables=True)
    assert not ok
    assert "no tienen relación" in msg


def test_coherent_system_still_works():
    """Un sistema acoplado se resuelve igual que antes."""
    raw = "2x + y = 5\nx - y = 1"
    ok, matrix, variables, msg = SystemParser.parse_system(raw)
    assert ok, msg
    assert variables == ["x", "y"]
    assert matrix.rows == 2
    assert matrix.cols == 3


def test_mixed_partial_coherence_is_accepted():
    """Sistema con x,y acoplados + z aislado se acepta."""
    raw = "x + y = 3\nx - y = 1\nz = 7"
    ok, _, variables, msg = SystemParser.parse_system(raw)
    assert ok, msg
    assert set(variables) == {"x", "y", "z"}