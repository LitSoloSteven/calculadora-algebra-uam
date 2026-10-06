"""Regresión y contrato para el rechazo de notación científica y strings
desmesuradamente largos en el backend.

Motivación (DoS): Fraction("1e999999999") intenta materializar el entero
10^999999999, consume GBs de RAM y bloquea el hilo. Los validators deben
rechazar el string ANTES de llegar a Fraction.

Cubre los 10 casos del MANUAL DE REQUERIMIENTOS PARA BACKEND, más regresión
de que las rutas válidas no se tocan.

Contrato:
  - MatrixValidator.parse_number_exact devuelve tupla (False, Fraction(0), msg).
  - MatrixValidator._to_fraction_strict devuelve tupla (False, Fraction(0), msg).
  - Matrix._normalize_val LANZA MatrixDataError.
"""
import time
from fractions import Fraction

import pytest

from src.backend.constants import MAX_NUMBER_STRING_LENGTH
from src.backend.exceptions import MatrixDataError
from src.backend.models.matrix import Matrix
from src.backend.utils.validators import MatrixValidator


SCI_MSG = "Notación científica no soportada. Escribe el número con decimales o fracción."
LEN_MSG = f"El número excede la longitud máxima permitida ({MAX_NUMBER_STRING_LENGTH} caracteres)."


# =========================================================================
# MatrixValidator.parse_number_exact
# =========================================================================

class TestParseNumberExactRejection:
    def test_sci_notation_huge_exponent_rejected_fast(self):
        """'1e999999999' debe rechazarse en <50 ms (DoS mitigation)."""
        t0 = time.perf_counter()
        ok, val, msg = MatrixValidator.parse_number_exact("1e999999999")
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert ok is False
        assert val == Fraction(0)
        assert msg == SCI_MSG
        assert elapsed_ms < 50, f"Tardó {elapsed_ms:.2f} ms, se esperaba <50 ms"

    def test_sci_notation_positive_exponent(self):
        ok, val, msg = MatrixValidator.parse_number_exact("1E5")
        assert ok is False
        assert val == Fraction(0)
        assert msg == SCI_MSG

    def test_sci_notation_negative_exponent(self):
        ok, val, msg = MatrixValidator.parse_number_exact("1e-4")
        assert ok is False
        assert val == Fraction(0)
        assert msg == SCI_MSG

    def test_string_exceeding_256_chars_rejected_fast(self):
        t0 = time.perf_counter()
        ok, val, msg = MatrixValidator.parse_number_exact("1" * 300)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert ok is False
        assert val == Fraction(0)
        assert msg == LEN_MSG
        assert elapsed_ms < 10, f"Tardó {elapsed_ms:.2f} ms, se esperaba <10 ms"

    def test_boundary_length_256_accepted(self):
        """Un string exactamente de 256 chars NO se rechaza por longitud."""
        s = "1" * MAX_NUMBER_STRING_LENGTH
        ok, val, _ = MatrixValidator.parse_number_exact(s)
        assert ok is True

    def test_boundary_length_257_rejected(self):
        s = "1" * (MAX_NUMBER_STRING_LENGTH + 1)
        ok, val, msg = MatrixValidator.parse_number_exact(s)
        assert ok is False
        assert msg == LEN_MSG

    def test_sci_notation_takes_precedence_over_length(self):
        """Un string largo Y con 'e' debe caer en notación científica."""
        s = "1" * 300 + "e1"
        ok, _, msg = MatrixValidator.parse_number_exact(s)
        assert ok is False
        assert msg == SCI_MSG

    def test_stripped_string_length_is_checked(self):
        """Whitespace no debe salvar a un string demasiado largo."""
        s = "  " + "1" * 300 + "  "
        ok, _, msg = MatrixValidator.parse_number_exact(s)
        assert ok is False
        assert msg == LEN_MSG


class TestParseNumberExactRegression:
    """Estos casos YA pasaban y deben seguir pasando."""

    @pytest.mark.parametrize("s,expected", [
        ("1/3", Fraction(1, 3)),
        ("0.25", Fraction(1, 4)),
        ("-3", Fraction(-3, 1)),
        ("1001/1000", Fraction(1001, 1000)),
        ("-123456789012/987654321", Fraction(-123456789012, 987654321)),
        ("1/1001", Fraction(1, 1001)),
    ])
    def test_valid_strings_still_accepted(self, s, expected):
        ok, val, msg = MatrixValidator.parse_number_exact(s)
        assert ok is True
        assert val == expected
        assert msg == ""

    def test_empty_string_still_reports_empty_field(self):
        ok, val, msg = MatrixValidator.parse_number_exact("")
        assert ok is False
        assert msg == "El campo está vacío."

    def test_int_and_fraction_unaffected(self):
        assert MatrixValidator.parse_number_exact(5)[0] is True
        assert MatrixValidator.parse_number_exact(Fraction(1, 7))[0] is True


# =========================================================================
# MatrixValidator._to_fraction_strict
# =========================================================================

class TestToFractionStrictRejection:
    def test_sci_notation_rejected_fast(self):
        t0 = time.perf_counter()
        ok, val, msg = MatrixValidator._to_fraction_strict("1e999999999")
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert ok is False
        assert val == Fraction(0)
        assert msg == SCI_MSG
        assert elapsed_ms < 50

    def test_long_string_rejected_fast(self):
        t0 = time.perf_counter()
        ok, val, msg = MatrixValidator._to_fraction_strict("1" * 300)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert ok is False
        assert val == Fraction(0)
        assert msg == LEN_MSG
        assert elapsed_ms < 10

    def test_sci_notation_precedence(self):
        ok, _, msg = MatrixValidator._to_fraction_strict("1" * 300 + "e1")
        assert ok is False
        assert msg == SCI_MSG

    def test_valid_strings_still_accepted(self):
        for s, expected in [
            ("1/3", Fraction(1, 3)),
            ("0.25", Fraction(1, 4)),
            ("-3", Fraction(-3, 1)),
        ]:
            ok, val, msg = MatrixValidator._to_fraction_strict(s)
            assert ok is True
            assert val == expected
            assert msg == ""

    def test_empty_string_still_reports_empty_field(self):
        ok, _, msg = MatrixValidator._to_fraction_strict("")
        assert ok is False
        assert msg == "El campo está vacío."


# =========================================================================
# Matrix._normalize_val  →  lanza MatrixDataError
# =========================================================================

class TestNormalizeValRejection:
    def test_sci_notation_raises_fast(self):
        t0 = time.perf_counter()
        with pytest.raises(MatrixDataError) as ei:
            Matrix(1, 1, [["1e999999999"]])
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert SCI_MSG in str(ei.value)
        assert elapsed_ms < 50

    def test_long_string_raises_fast(self):
        t0 = time.perf_counter()
        with pytest.raises(MatrixDataError) as ei:
            Matrix(1, 1, [["1" * 300]])
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert LEN_MSG in str(ei.value)
        assert elapsed_ms < 10

    def test_sci_notation_precedence(self):
        with pytest.raises(MatrixDataError) as ei:
            Matrix(1, 1, [["1" * 300 + "e1"]])
        assert SCI_MSG in str(ei.value)

    def test_set_also_rejects_sci_notation(self):
        """El mismo chequeo debe aplicar en Matrix.set()."""
        m = Matrix(1, 1, [[0]])
        with pytest.raises(MatrixDataError):
            m.set(0, 0, "1e999999999")

    def test_empty_string_still_returns_zero(self):
        """Regresión: un string vacío sigue siendo Fraction(0), no error."""
        m = Matrix(1, 1, [[""]])
        assert m.get(0, 0) == Fraction(0)


class TestNormalizeValRegression:
    """Los casos válidos existentes no se tocan."""

    @pytest.mark.parametrize("s,expected", [
        ("1/1001", Fraction(1, 1001)),
        ("-123456789012/987654321", Fraction(-123456789012, 987654321)),
        ("0.25", Fraction(1, 4)),
        ("-3", Fraction(-3, 1)),
    ])
    def test_valid_strings_still_accepted(self, s, expected):
        m = Matrix(1, 1, [[s]])
        assert m.get(0, 0) == expected