"""Tests para la excepción estructurada RomanNumeralError.

Verifica que cada error del solver de números romanos lance una
excepción con:
  - code: identificador estable (uno de los ERROR_*)
  - invalid_token: valor ofensivo, cuando aplica
  - to_dict(): payload JSON-serializable para el frontend
  - str(exc): mensaje humano, compatible con tests legados
"""
import json

import pytest

from src.backend.solvers.numeric_systems.roman_calculator import (
    RomanCalculator,
    RomanNumeralError,
    int_to_roman,
    roman_to_int,
    ERROR_OUT_OF_RANGE,
    ERROR_INVALID_SYNTAX,
    ERROR_NOT_CANONICAL,
    ERROR_ZERO_NOT_REPRESENTABLE,
    ERROR_NEGATIVE_NOT_REPRESENTABLE,
    ERROR_INVALID_TYPE,
    ERROR_EMPTY_INPUT,
    ERROR_OPERAND_NOT_SINGLE_DIGIT,
)


# ---------------------------------------------------------------------------
# Constructor y contrato
# ---------------------------------------------------------------------------

def test_exception_stores_code_and_token():
    err = RomanNumeralError(
        "mensaje", code=ERROR_OUT_OF_RANGE, invalid_token="MMMM"
    )
    assert err.code == ERROR_OUT_OF_RANGE
    assert err.invalid_token == "MMMM"
    assert str(err) == "mensaje"


def test_exception_allows_missing_token():
    err = RomanNumeralError("mensaje", code=ERROR_ZERO_NOT_REPRESENTABLE)
    assert err.code == ERROR_ZERO_NOT_REPRESENTABLE
    assert err.invalid_token is None


def test_exception_is_still_a_value_error():
    err = RomanNumeralError("x", code=ERROR_OUT_OF_RANGE)
    assert isinstance(err, ValueError)


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

def test_to_dict_shape_with_token():
    err = RomanNumeralError(
        "mensaje", code=ERROR_OUT_OF_RANGE, invalid_token="MMMM"
    )
    assert err.to_dict() == {
        "status": "ERROR",
        "error_code": ERROR_OUT_OF_RANGE,
        "message": "mensaje",
        "token": "MMMM",
    }


def test_to_dict_shape_without_token():
    err = RomanNumeralError("mensaje", code=ERROR_ZERO_NOT_REPRESENTABLE)
    d = err.to_dict()
    assert d["status"] == "ERROR"
    assert d["error_code"] == ERROR_ZERO_NOT_REPRESENTABLE
    assert d["message"] == "mensaje"
    assert d["token"] is None


def test_to_dict_is_json_serializable():
    err = RomanNumeralError(
        "mensaje", code=ERROR_OUT_OF_RANGE, invalid_token="MMMM"
    )
    payload = json.loads(json.dumps(err.to_dict()))
    assert payload["error_code"] == ERROR_OUT_OF_RANGE
    assert payload["token"] == "MMMM"


# ---------------------------------------------------------------------------
# Cada código aparece en el raise esperado
# ---------------------------------------------------------------------------

def test_int_to_roman_non_int_raises_invalid_type():
    with pytest.raises(RomanNumeralError) as ei:
        int_to_roman("X")
    assert ei.value.code == ERROR_INVALID_TYPE
    assert ei.value.invalid_token == "X"


def test_int_to_roman_above_range_raises_out_of_range():
    with pytest.raises(RomanNumeralError) as ei:
        int_to_roman(4000)
    assert ei.value.code == ERROR_OUT_OF_RANGE
    assert ei.value.invalid_token == "4000"


def test_int_to_roman_below_range_raises_out_of_range():
    with pytest.raises(RomanNumeralError) as ei:
        int_to_roman(0)
    assert ei.value.code == ERROR_OUT_OF_RANGE


def test_roman_to_int_non_str_raises_invalid_type():
    with pytest.raises(RomanNumeralError) as ei:
        roman_to_int(42)
    assert ei.value.code == ERROR_INVALID_TYPE
    assert ei.value.invalid_token == "42"


def test_roman_to_int_empty_raises_empty_input():
    with pytest.raises(RomanNumeralError) as ei:
        roman_to_int("   ")
    assert ei.value.code == ERROR_EMPTY_INPUT


def test_roman_to_int_garbage_raises_invalid_syntax():
    with pytest.raises(RomanNumeralError) as ei:
        roman_to_int("ABC")
    assert ei.value.code == ERROR_INVALID_SYNTAX
    assert ei.value.invalid_token == "ABC"


def test_roman_to_int_iiii_raises_invalid_syntax():
    """IIII falla la ROMAN_REGEX (I{0,3} permite máx 3 I's), por eso
    cae en INVALID_SYNTAX, no en NOT_CANONICAL. La regex ya codifica
    la forma canónica, así que la rama NOT_CANONICAL es defensiva."""
    with pytest.raises(RomanNumeralError) as ei:
        roman_to_int("IIII")
    assert ei.value.code == ERROR_INVALID_SYNTAX
    assert ei.value.invalid_token == "IIII"


def test_not_canonical_code_is_constructible():
    """El código NOT_CANONICAL existe como parte del contrato y se
    serializa correctamente. No hay input real que lo dispare porque
    la ROMAN_REGEX rechaza primero toda forma no canónica (defensivo)."""
    err = RomanNumeralError(
        "'IIII' no es una forma canónica válida.",
        code=ERROR_NOT_CANONICAL,
        invalid_token="IIII",
    )
    assert err.code == ERROR_NOT_CANONICAL
    assert err.to_dict()["error_code"] == ERROR_NOT_CANONICAL
    assert err.to_dict()["token"] == "IIII"


def test_sumar_overflow_raises_out_of_range():
    with pytest.raises(RomanNumeralError) as ei:
        RomanCalculator.sumar("MMM", "M")
    assert ei.value.code == ERROR_OUT_OF_RANGE
    assert ei.value.invalid_token == "4000"


def test_restar_zero_raises_zero_not_representable():
    with pytest.raises(RomanNumeralError) as ei:
        RomanCalculator.restar("V", "V")
    assert ei.value.code == ERROR_ZERO_NOT_REPRESENTABLE
    assert ei.value.invalid_token is None


def test_restar_negative_raises_negative_not_representable():
    with pytest.raises(RomanNumeralError) as ei:
        RomanCalculator.restar("III", "VII")
    assert ei.value.code == ERROR_NEGATIVE_NOT_REPRESENTABLE
    assert ei.value.invalid_token is None


def test_multiplicar_operand_a_not_single_digit():
    with pytest.raises(RomanNumeralError) as ei:
        RomanCalculator.multiplicar_un_digito("X", "II")
    assert ei.value.code == ERROR_OPERAND_NOT_SINGLE_DIGIT
    assert ei.value.invalid_token == "X"


def test_multiplicar_operand_b_not_single_digit():
    with pytest.raises(RomanNumeralError) as ei:
        RomanCalculator.multiplicar_un_digito("III", "XI")
    assert ei.value.code == ERROR_OPERAND_NOT_SINGLE_DIGIT
    assert ei.value.invalid_token == "XI"


# ---------------------------------------------------------------------------
# Regresión: mensajes existentes no cambian
# ---------------------------------------------------------------------------

def test_legacy_messages_still_match():
    """Los tests existentes usan pytest.raises(match=...).
    El texto del mensaje no cambia con esta feature."""
    with pytest.raises(RomanNumeralError, match="excede el límite"):
        RomanCalculator.sumar("MMM", "M")

    with pytest.raises(RomanNumeralError, match="cero"):
        RomanCalculator.restar("V", "V")

    with pytest.raises(RomanNumeralError, match="negativos"):
        RomanCalculator.restar("III", "VII")

    with pytest.raises(RomanNumeralError, match="no es de 1 dígito"):
        RomanCalculator.multiplicar_un_digito("X", "II")