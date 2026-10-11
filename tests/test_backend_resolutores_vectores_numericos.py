"""Pruebas unitarias de resolutores de operaciones vectoriales y sistemas numéricos."""

from fractions import Fraction
import pytest

from src.backend.constantes import (
    ERROR,
    EXITO,
    SIN_SOLUCION,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
)
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import (
    ResolutorCombinacionLineal,
)
from src.backend.resolutores.operaciones_vectores.operaciones import (
    ResolutorOperacionesVectores,
)
from src.backend.resolutores.sistemas_numericos.calculadora_romana import (
    ERROR_CERO_NO_REPRESENTABLE,
    CalculadoraRomana,
    ErrorNumeroRomano,
    entero_a_romano,
    romano_a_entero,
)
from src.backend.resolutores.sistemas_numericos.conversor_bases import (
    ConversorBases,
)


def test_operaciones_vectores_suma_y_resta():
    """Verifica suma y resta de vectores en R^3 con aritmética exacta."""
    v1 = Matriz(3, 1, [[Fraction(1)], [Fraction(2)], [Fraction(3)]])
    v2 = Matriz(3, 1, [[Fraction(4)], [Fraction(5)], [Fraction(6)]])
    resolutor = ResolutorOperacionesVectores()

    res_suma = resolutor.sumar(v1, v2)
    assert res_suma["estado"] == EXITO
    assert res_suma["matriz_resultado"].datos == [[Fraction(5)], [Fraction(7)], [Fraction(9)]]

    res_resta = resolutor.restar(v1, v2)
    assert res_resta["estado"] == EXITO
    assert res_resta["matriz_resultado"].datos == [[Fraction(-3)], [Fraction(-3)], [Fraction(-3)]]


def test_operaciones_vectores_multiplicacion_escalar():
    """Verifica multiplicación escalar exacta sobre un vector fila."""
    v = Matriz(1, 3, [[Fraction(2), Fraction(4), Fraction(6)]])
    resolutor = ResolutorOperacionesVectores()
    res = resolutor.multiplicar_escalar("1/2", v)
    assert res["estado"] == EXITO
    assert res["matriz_resultado"].datos == [[Fraction(1), Fraction(2), Fraction(3)]]


def test_combinacion_lineal_solucion_unica():
    """Verifica determinación de combinación lineal con solución única."""
    v1 = Matriz(2, 1, [[Fraction(1)], [Fraction(0)]])
    v2 = Matriz(2, 1, [[Fraction(0)], [Fraction(1)]])
    b = Matriz(2, 1, [[Fraction(3)], [Fraction(5)]])
    resolutor = ResolutorCombinacionLineal()

    res = resolutor.resolver(b, [v1, v2])
    assert res["estado"] == SOLUCION_UNICA
    assert res["es_combinacion_lineal"] is True
    assert res["coeficientes"] == [Fraction(3), Fraction(5)]
    assert res["paso_verificacion"]["coincide"] is True


def test_combinacion_lineal_sin_solucion():
    """Verifica rechazo de combinación lineal cuando no existe solución."""
    v1 = Matriz(2, 1, [[Fraction(1)], [Fraction(1)]])
    b = Matriz(2, 1, [[Fraction(1)], [Fraction(2)]])
    resolutor = ResolutorCombinacionLineal()

    res = resolutor.resolver(b, [v1])
    assert res["estado"] == SIN_SOLUCION
    assert res["es_combinacion_lineal"] is False


def test_combinacion_lineal_infinitas_soluciones():
    """Verifica identificación de infinitas combinaciones lineales."""
    v1 = Matriz(2, 1, [[Fraction(1)], [Fraction(2)]])
    v2 = Matriz(2, 1, [[Fraction(2)], [Fraction(4)]])
    b = Matriz(2, 1, [[Fraction(3)], [Fraction(6)]])
    resolutor = ResolutorCombinacionLineal()

    res = resolutor.resolver(b, [v1, v2])
    assert res["estado"] == SOLUCIONES_INFINITAS
    assert res["es_combinacion_lineal"] is True
    assert len(res["parametros_libres"]) == 1


def test_conversor_bases_decimal_y_binario():
    """Verifica conversión posicional entre bases y generación de pasos."""
    conversor = ConversorBases()
    res = conversor.decimal_a_todo("255")
    assert res["estado"] == EXITO
    assert res["binario"] == "11111111"
    assert res["octal"] == "377"
    assert res["hexadecimal"] == "FF"
    assert len(res["pasos"]) > 0

    res_bin = conversor.binario_a_todo("1010")
    assert res_bin["estado"] == EXITO
    assert res_bin["decimal"] == "10"


def test_calculadora_romana_operaciones_y_excepciones():
    """Verifica suma, resta y multiplicación de 1 dígito en números romanos."""
    calc = CalculadoraRomana()

    res_suma = calc.sumar("XIV", "VI")
    assert res_suma.resultado_romano == "XX"
    assert res_suma.resultado_decimal == 20

    res_resta = calc.restar("X", "IV")
    assert res_resta.resultado_romano == "VI"
    assert res_resta.resultado_decimal == 6

    res_mult = calc.multiplicar_un_digito("III", "IV")
    assert res_mult.resultado_romano == "XII"
    assert res_mult.resultado_decimal == 12

    with pytest.raises(ErrorNumeroRomano) as exc_info:
        calc.restar("V", "V")
    assert exc_info.value.codigo == ERROR_CERO_NO_REPRESENTABLE


def test_conversiones_enteros_romanos_canónicos():
    """Verifica conversión bidireccional estricta de números romanos."""
    assert entero_a_romano(1994) == "MCMXCIV"
    assert romano_a_entero("MCMXCIV") == 1994
