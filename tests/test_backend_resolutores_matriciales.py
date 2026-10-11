"""Pruebas unitarias para los resolutores algebraicos en espanol ASCII."""

from fractions import Fraction
import pytest

from src.backend.constantes import (
    ERROR,
    EXITO,
    SINGULAR,
    SIN_SOLUCION,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
)
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices import (
    EvaluadorExpresionesMatriciales,
    ResolutorDeterminante,
    ResolutorInversa,
    ResolutorModeloLeontief,
    ResolutorOperacionesMatrices,
    ResolutorTransformacionesLineales,
)
from src.backend.resolutores.sistemas_lineales import (
    ResolutorGauss,
    ResolutorGaussJordan,
)


def test_resolutor_gauss_solucion_unica():
    """Valida resolucion con solucion unica y verificacion de Rouche-Frobenius."""
    datos = [
        [Fraction(2), Fraction(1), Fraction(-1), Fraction(8)],
        [Fraction(-3), Fraction(-1), Fraction(2), Fraction(-11)],
        [Fraction(-2), Fraction(1), Fraction(2), Fraction(-3)],
    ]
    matriz = Matriz(3, 4, datos)
    resolutor = ResolutorGauss(matriz)
    res = resolutor.resolver()

    assert res["estado"] == SOLUCION_UNICA
    assert res["solucion"] == ["2", "3", "-1"]
    assert res["solucion_exacta"] == [Fraction(2), Fraction(3), Fraction(-1)]
    assert res["analisis_sistema"]["clasificacion_rouche"] == "Sistema Compatible Determinado"


def test_resolutor_gauss_sin_solucion():
    """Valida deteccion de sistema inconsistente sin solucion."""
    datos = [
        [Fraction(1), Fraction(1), Fraction(3)],
        [Fraction(1), Fraction(1), Fraction(5)],
    ]
    matriz = Matriz(2, 3, datos)
    res = ResolutorGauss(matriz).resolver()

    assert res["estado"] == SIN_SOLUCION
    assert res["solucion"] is None
    assert res["analisis_sistema"]["clasificacion_rouche"] == "Sistema Incompatible"


def test_resolutor_gauss_jordan_infinitas_soluciones():
    """Valida solucion parametrica para sistemas compatibles indeterminados."""
    datos = [
        [Fraction(1), Fraction(2), Fraction(1), Fraction(4)],
        [Fraction(2), Fraction(4), Fraction(2), Fraction(8)],
    ]
    matriz = Matriz(2, 4, datos)
    res = ResolutorGaussJordan(matriz).resolver()

    assert res["estado"] == SOLUCIONES_INFINITAS
    assert res["solucion_exacta"] is None
    assert len(res["columnas_libres"]) > 0
    assert res["parametros_solucion"] is not None


def test_operaciones_matrices_basicas():
    """Valida suma, resta, producto escalar y multiplicacion matricial."""
    ops = ResolutorOperacionesMatrices()
    a = Matriz(2, 2, [[1, 2], [3, 4]])
    b = Matriz(2, 2, [[5, 6], [7, 8]])

    res_suma = ops.sumar(a, b)
    assert res_suma["estado"] == EXITO
    assert res_suma["matriz_resultado"].datos == [[Fraction(6), Fraction(8)], [Fraction(10), Fraction(12)]]

    res_esc = ops.multiplicar_escalar("2", a)
    assert res_esc["estado"] == EXITO
    assert res_esc["matriz_resultado"].datos == [[Fraction(2), Fraction(4)], [Fraction(6), Fraction(8)]]

    res_mul = ops.multiplicar(a, b)
    assert res_mul["estado"] == EXITO
    assert res_mul["matriz_resultado"].datos == [[Fraction(19), Fraction(22)], [Fraction(43), Fraction(50)]]

    trans = ops.transponer(a)
    assert trans.datos == [[Fraction(1), Fraction(3)], [Fraction(2), Fraction(4)]]

    det = ops.determinante(a)
    assert det == Fraction(-2)


def test_resolutor_determinante_laplace_y_lu():
    """Valida metodos de calculo de determinantes de orden 2x2 y 3x3."""
    m = Matriz(3, 3, [[1, 2, 3], [0, 4, 5], [1, 0, 6]])
    res_laplace = ResolutorDeterminante.resolver_laplace(m)
    res_lu = ResolutorDeterminante.resolver_lu(m)

    assert res_laplace["determinante"] == res_lu["determinante"]
    assert res_lu["es_singular"] is False


def test_resolutor_inversa():
    """Valida inversion exacta y deteccion de matrices singulares."""
    inv = ResolutorInversa()
    a = Matriz(2, 2, [[4, 7], [2, 6]])
    res = inv.resolver(a)

    assert res["estado"] == EXITO
    assert res["inversa"].datos == [[Fraction(3, 5), Fraction(-7, 10)], [Fraction(-1, 5), Fraction(2, 5)]]
    assert res["paso_verificacion"]["se_cumple"] is True

    singular = Matriz(2, 2, [[1, 2], [2, 4]])
    res_sing = inv.resolver(singular)
    assert res_sing["estado"] == SINGULAR


def test_evaluador_expresiones_matriciales():
    """Valida evaluacion de expresiones compuestas con transpuesta y escalares."""
    evaluador = EvaluadorExpresionesMatriciales()
    a = Matriz(2, 2, [[1, 2], [3, 4]])
    b = Matriz(2, 2, [[2, 0], [1, 2]])
    res = evaluador.evaluar("2A - Bᵀ", {"A": a, "B": b})

    assert res["estado"] == EXITO
    assert res["matriz_resultado"].datos == [[Fraction(0), Fraction(3)], [Fraction(6), Fraction(6)]]


def test_transformaciones_y_leontief():
    """Valida analisis de nucleo e imagen y modelo de insumo-producto."""
    a = Matriz(2, 2, [[1, 0], [0, 1]])
    res_t = ResolutorTransformacionesLineales().resolver(a)
    assert res_t["estado"] == EXITO
    assert res_t["es_inyectiva"] is True
    assert res_t["es_sobreyectiva"] is True

    c = Matriz(2, 2, [[Fraction(1, 5), Fraction(2, 5)], [Fraction(2, 5), Fraction(1, 5)]])
    d = [Fraction(100), Fraction(200)]
    res_l = ResolutorModeloLeontief().resolver(c, d)
    assert res_l["estado"] == EXITO
    assert res_l["hawkins_simon"]["es_economicamente_viable"] is True
