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

from src.frontend.helpers import format_step_for_mathjax

def test_format_step_for_mathjax():
    assert format_step_for_mathjax('x_{1} = 2') == 'x_{1} = 2'
    assert format_step_for_mathjax('Variables libres identificadas: x_{3} = t') == r'\text{Variables libres identificadas:}\; x_{3} = t'
    assert format_step_for_mathjax(r'Ecuación 1: \left(2\right) = 4') == r'\text{Ecuación 1:}\; \left(2\right) = 4'
    assert format_step_for_mathjax(r'\text{Ecuación 1:} 2 = 2') == r'\text{Ecuación 1:} 2 = 2'
