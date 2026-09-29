"""
Pruebas unitarias para el módulo roman_calculator.
Cubre conversiones, suma, resta y multiplicación por sumas sucesivas.
"""

import pytest
from src.backend.solvers.numeric_systems.roman_calculator import (
    RomanCalculator,
    RomanNumeralError,
    int_to_roman,
    roman_to_int
)


class TestRomanConversions:
    """Pruebas de conversión entre números romanos y decimales."""

    @pytest.mark.parametrize("decimal, expected_roman", [
        (1, "I"),
        (4, "IV"),
        (9, "IX"),
        (14, "XIV"),
        (40, "XL"),
        (44, "XLIV"),
        (90, "XC"),
        (99, "XCIX"),
        (400, "CD"),
        (900, "CM"),
        (1994, "MCMXCIV"),
        (2026, "MMXXVI"),
        (3999, "MMMCMXCIX"),
    ])
    def test_bidirectional_valid(self, decimal: int, expected_roman: str):
        assert int_to_roman(decimal) == expected_roman
        assert roman_to_int(expected_roman) == decimal

    @pytest.mark.parametrize("invalid_roman", [
        "IIII",      # No canónico (4 debe ser IV)
        "VX",        # Sustracción inválida
        "IL",        # No permitido (debe ser XLIX para 49)
        "IC",        # No permitido
        "MMMM",      # Fuera de rango
        "ABC",       # Caracteres no permitidos
        "123",       # Dígitos decimales
        "",          # Vacío
        "   ",       # Espacios en blanco
        "VV",        # Repetición inválida de V
        "LL",        # Repetición inválida de L
        "DD",        # Repetición inválida de D
    ])
    def test_roman_to_int_invalid(self, invalid_roman: str):
        with pytest.raises(RomanNumeralError):
            roman_to_int(invalid_roman)

    @pytest.mark.parametrize("out_of_range", [0, -1, -50, 4000, 5000])
    def test_int_to_roman_out_of_range(self, out_of_range: int):
        with pytest.raises(RomanNumeralError):
            int_to_roman(out_of_range)


class TestRomanAddition:
    """Pruebas de la operación suma."""

    def test_suma_simple(self):
        res = RomanCalculator.sumar("V", "III")
        assert res.resultado_romano == "VIII"
        assert res.resultado_decimal == 8
        assert len(res.pasos) >= 4

    def test_suma_con_acarreo(self):
        res = RomanCalculator.sumar("XIV", "IX")
        assert res.resultado_romano == "XXIII"
        assert res.resultado_decimal == 23

    def test_suma_grandes(self):
        res = RomanCalculator.sumar("MCMXC", "X")
        assert res.resultado_romano == "MM"
        assert res.resultado_decimal == 2000

    def test_suma_excede_maximo(self):
        with pytest.raises(RomanNumeralError, match="excede el límite"):
            RomanCalculator.sumar("MMM", "M")


class TestRomanSubtraction:
    """Pruebas de la operación resta."""

    def test_resta_valida(self):
        res = RomanCalculator.restar("XX", "VIII")
        assert res.resultado_romano == "XII"
        assert res.resultado_decimal == 12

    def test_resta_caso_borde_uno(self):
        res = RomanCalculator.restar("X", "IX")
        assert res.resultado_romano == "I"
        assert res.resultado_decimal == 1

    def test_resta_da_cero_invalido(self):
        with pytest.raises(RomanNumeralError, match="cero"):
            RomanCalculator.restar("V", "V")

    def test_resta_da_negativo_invalido(self):
        with pytest.raises(RomanNumeralError, match="negativos"):
            RomanCalculator.restar("III", "VII")


class TestRomanSingleDigitMultiplication:
    """Pruebas de la multiplicación de 1 dígito mediante adición sucesiva."""

    def test_multiplicacion_valida_3_por_4(self):
        res = RomanCalculator.multiplicar_un_digito("III", "IV")
        assert res.resultado_romano == "XII"
        assert res.resultado_decimal == 12
        # Verifica que se generaron los pasos de las 4 sumas de III
        assert any("Suma 1" in p for p in res.pasos)
        assert any("Suma 4" in p for p in res.pasos)
        assert any("III + III + III + III" in p for p in res.pasos)

    def test_multiplicacion_por_uno(self):
        res = RomanCalculator.multiplicar_un_digito("VII", "I")
        assert res.resultado_romano == "VII"
        assert res.resultado_decimal == 7

    def test_multiplicacion_maxima_9_por_9(self):
        res = RomanCalculator.multiplicar_un_digito("IX", "IX")
        assert res.resultado_romano == "LXXXI"
        assert res.resultado_decimal == 81

    def test_error_operando_a_mayor_a_9(self):
        with pytest.raises(RomanNumeralError, match="no es de 1 dígito"):
            RomanCalculator.multiplicar_un_digito("X", "II")

    def test_error_operando_b_mayor_a_9(self):
        with pytest.raises(RomanNumeralError, match="no es de 1 dígito"):
            RomanCalculator.multiplicar_un_digito("III", "XI")

    def test_error_ambos_mayores_a_9(self):
        with pytest.raises(RomanNumeralError, match="no es de 1 dígito"):
            RomanCalculator.multiplicar_un_digito("XV", "XX")