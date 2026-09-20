from fractions import Fraction
import pytest
from src.backend.models.matrix import Matrix
from src.backend.exceptions import MatrixDataError


def test_string_fraction_large_denominator_is_exact():
    m = Matrix(1, 1, [["1/1001"]])
    assert m.data[0][0] == Fraction(1, 1001)


def test_string_fraction_simple_is_exact():
    m = Matrix(1, 1, [["2/3"]])
    assert m.data[0][0] == Fraction(2, 3)


def test_string_decimal_parses_exact():
    m = Matrix(1, 1, [["0.1"]])
    assert m.data[0][0] == Fraction(1, 10)


def test_float_that_matches_fraction_is_converted():
    m = Matrix(1, 1, [[0.5]])
    assert m.data[0][0] == Fraction(1, 2)


def test_string_with_invalid_content_raises():
    with pytest.raises(MatrixDataError):
        Matrix(1, 1, [["abc"]])


def test_string_empty_becomes_zero():
    m = Matrix(1, 1, [[""]])
    assert m.data[0][0] == Fraction(0)