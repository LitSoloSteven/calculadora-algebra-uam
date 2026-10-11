"""Pruebas unitarias para helpers del frontend."""
from fractions import Fraction
import pytest

from src.frontend.helpers import a_flotante, formatear_paso_mathjax


def test_a_flotante():
    """Valida la conversión a flotante de cadenas y fracciones."""
    assert a_flotante("1/2") == 0.5
    assert a_flotante("9/7") == 9 / 7
    assert a_flotante("-3") == -3.0
    assert a_flotante(" 0.25 ") == 0.25
    assert a_flotante(Fraction(1, 3)) == 1 / 3

    with pytest.raises(ValueError):
        a_flotante("abc")
    with pytest.raises(ValueError):
        a_flotante("1/0")
    with pytest.raises(ValueError):
        a_flotante("")


def test_formatear_paso_mathjax():
    """Valida el formateo de pasos textuales para MathJax."""
    assert formatear_paso_mathjax("x_{1} = 2") == "x_{1} = 2"
    assert (
        formatear_paso_mathjax("Variables libres identificadas: x_{3} = t")
        == r"\text{Variables libres identificadas:}\; x_{3} = t"
    )
    assert (
        formatear_paso_mathjax(r"Ecuación 1: \left(2\right) = 4")
        == r"\text{Ecuación 1:}\; \left(2\right) = 4"
    )
    assert (
        formatear_paso_mathjax(r"\text{Ecuación 1:} 2 = 2")
        == r"\text{Ecuación 1:} 2 = 2"
    )
