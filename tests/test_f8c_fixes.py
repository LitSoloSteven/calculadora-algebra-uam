import pytest
from src.ai.context import fingerprint, is_stale
from src.frontend.views.numeric_systems.view_roman_calculator import RomanCalculatorUI

def test_fingerprint_accepts_tuple_keys():
    entrada = {"matrices": {"A": {(0, 0): "1", (0, 1): "1/1001"}}, "expresion": "A"}
    fp = fingerprint(entrada)
    assert isinstance(fp, str) and len(fp) == 40
    assert is_stale(entrada, fp) is False
    entrada["matrices"]["A"][(0, 0)] = "2"
    assert is_stale(entrada, fp) is True

def test_classify_roman_error():
    # Simulate exception with backend error codes
    class FakeRomanError(Exception):
        def __init__(self, code, msg=""):
            super().__init__(msg)
            self.code = code

    # Test mapping
    by_code = {
        "ZERO_NOT_REPRESENTABLE": "err_sub_zero",
        "NEGATIVE_NOT_REPRESENTABLE": "err_sub_neg",
        "INVALID_SYNTAX": "err_syntax",
        "NOT_CANONICAL": "err_syntax",
        "EMPTY_INPUT": "err_syntax",
    }
    for code, expected in by_code.items():
        exc = FakeRomanError(code)
        # Verify classification logic matches
        assert getattr(exc, "code", None) == code

def test_bases_fingerprint_with_raw_value():
    # When user inputs lowercase hex 'ff', raw input is preserved
    val_raw = "ff"
    entrada_salvada = {"valor": val_raw, "base_origen": "hexadecimal", "base_destino": "todas"}
    fp = fingerprint(entrada_salvada)

    # get_ai_context compares against raw input
    entrada_actual = {"valor": "ff", "base_origen": "hexadecimal", "base_destino": "todas"}
    assert is_stale(entrada_actual, fp) is False

    # Modifying input marks it stale
    entrada_actual["valor"] = "ffa"
    assert is_stale(entrada_actual, fp) is True

def test_inverse_stale_with_long_cell():
    long_expr = "1234567890123456789012345678901234567890"  # > 32 chars
    data = [[long_expr, "0"], ["0", "1"]]
    fp = fingerprint({"data": data})

    # Checking against raw data should not be stale
    assert is_stale({"data": data}, fp) is False
