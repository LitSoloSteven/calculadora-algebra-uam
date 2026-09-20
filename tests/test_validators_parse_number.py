"""Tests de parse_number_exact vs parse_number.

Cubre:
- Preservación de Fraction exacto (denominador > 1000)
- Compatibilidad de parse_number (float para frontend)
- Consistencia de mensajes de error entre ambos
- Preservación a través de SystemParser
"""
from fractions import Fraction
from src.backend.utils.validators import MatrixValidator
from src.backend.utils.parsers import SystemParser


def test_parse_number_exact_preserves_large_denominator():
    ok, val, msg = MatrixValidator.parse_number_exact("1/1001")
    assert ok, msg
    assert isinstance(val, Fraction), f"Tipo incorrecto: {type(val).__name__}"
    assert val == Fraction(1, 1001)


def test_parse_number_returns_float_for_compatibility():
    ok, val, msg = MatrixValidator.parse_number("1/1001")
    assert ok, msg
    assert isinstance(val, float)


def test_float_is_normalized_to_simple_fraction():
    ok, val, msg = MatrixValidator.parse_number_exact(0.1)
    assert ok
    assert val == Fraction(1, 10)


def test_error_messages_are_consistent_between_versions():
    ok, _, msg_exact = MatrixValidator.parse_number_exact("1/0")
    assert not ok and "División por cero" in msg_exact

    ok2, _, msg_float = MatrixValidator.parse_number("1/0")
    assert not ok2
    assert msg_float == msg_exact, "Los mensajes deben ser idénticos"


def test_invalid_string_is_rejected():
    ok, _, msg = MatrixValidator.parse_number_exact("abc")
    assert not ok and "no es un número" in msg


def test_system_parser_preserves_large_denominator():
    """Regresión: parse_system debe preservar '1/1001' como Fraction exacta."""
    ok, matrix, variables, msg = SystemParser.parse_system("1/1001 x + y = 1\nx + y = 2")
    assert ok, msg
    val = matrix.get(0, 0)
    assert isinstance(val, Fraction), f"Esperado Fraction, obtenido {type(val).__name__}"
    assert val == Fraction(1, 1001)


def test_system_parser_handles_integer_coefficients():
    ok, matrix, variables, msg = SystemParser.parse_system("2x + 3y = 8\nx - y = 1")
    assert ok, msg
    val = matrix.get(0, 0)
    assert isinstance(val, Fraction) and val == 2


def test_system_parser_handles_negative_fractions():
    """Fracciones negativas con signo deben parsearse correctamente."""
    ok, matrix, variables, msg = SystemParser.parse_system("-1/2 x + y = 0\nx + y = 1")
    assert ok, msg
    val = matrix.get(0, 0)
    assert val == Fraction(-1, 2), f"Esperado -1/2, obtenido {val}"