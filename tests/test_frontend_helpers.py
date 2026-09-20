import pytest
from fractions import Fraction
from src.frontend.helpers import to_float

def test_to_float():
    assert to_float("1/2") == 0.5
    assert to_float("9/7") == 9/7
    assert to_float("-3") == -3.0
    assert to_float(" 0.25 ") == 0.25
    assert to_float(Fraction(1, 3)) == 1/3
    
    with pytest.raises(ValueError):
        to_float("abc")
    with pytest.raises(ValueError):
        to_float("1/0")
    with pytest.raises(ValueError):
        to_float("")
