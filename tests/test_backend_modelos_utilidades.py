"""Pruebas unitarias para modelos, constantes, excepciones y utilidades del backend."""

from fractions import Fraction
import pytest

from src.backend.constantes import (
    CERO_EPSILON,
    DECIMALES_VISUALIZACION,
    LIMITE_RECONSTRUCCION_ESTRICTA,
    LONGITUD_MAXIMA_CADENA_NUMERO,
)
from src.backend.excepciones import (
    AlgebraLinealError,
    ErrorDatosMatriz,
    ErrorDiscrepanciaDimension,
    ErrorNumeroInvalido,
    ErrorSistemaSingular,
    ErrorVectorInvalido,
)
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.analizadores import AnalizadorSistema
from src.backend.utilidades.formateadores import (
    formatear_expresion_parametrica,
    formatear_fraccion_str,
    formatear_variable_para_latex,
    numero_a_latex,
)
from src.backend.utilidades.reglas_dominio import (
    validar_datos_transferencia_matriz,
    validar_datos_transferencia_vectores,
    validar_entrada_base,
)
from src.backend.utilidades.utilidades_matematicas import (
    mcd,
    mcd_lista,
    mcm,
    simplificar_fila,
)
from src.backend.utilidades.validadores import (
    ValidadorMatriz,
    validar_dimensiones_multiplicacion,
    validar_mismas_dimensiones,
)


def test_modelo_matriz_operaciones_basicas():
    """Valida creación, clonación y operaciones elementales de Matriz."""
    m = Matriz(2, 2, [[1, 2], [3, 4]])
    assert m.filas == 2 and m.columnas == 2
    assert m.obtener(0, 1) == 2

    m.establecer(0, 1, "5/2")
    assert m.obtener(0, 1) == Fraction(5, 2)

    copia = m.clonar()
    assert copia == m
    copia.intercambiar_filas(0, 1)
    assert copia.obtener(0, 0) == 3

    m.sumar_fila_escalada(1, 0, -3)
    assert m.obtener(1, 0) == 0


def test_modelo_matriz_guardas_seguridad():
    """Valida rechazo de notación científica y cadenas excesivamente largas."""
    with pytest.raises(ErrorDatosMatriz):
        Matriz(1, 1, [["1e999"]])

    cadena_larga = "1" * (LONGITUD_MAXIMA_CADENA_NUMERO + 1)
    with pytest.raises(ErrorDatosMatriz):
        Matriz(1, 1, [[cadena_larga]])


def test_utilidades_matematicas():
    """Valida MCD, MCM y simplificación de fila."""
    assert mcd(12, 18) == 6
    assert mcm(4, 6) == 12
    assert mcd_lista([12, 24, 36]) == 12
    assert simplificar_fila([2, 4, 6]) == [1, 2, 3]


def test_formateadores_exactos():
    """Valida formateo de números a cadenas y LaTeX exacto."""
    assert formatear_fraccion_str(Fraction(3, 4)) == "3/4"
    assert formatear_fraccion_str(5) == "5"
    assert numero_a_latex(Fraction(-1, 2)) == r"-\frac{1}{2}"
    assert formatear_variable_para_latex("x1") == "x_{1}"
    assert formatear_expresion_parametrica(Fraction(2), {"t": Fraction(3, 2)}) == "2 + (3/2)t"


def test_analizador_sistema():
    """Valida parseo de sistemas de ecuaciones a Matriz aumentada."""
    texto = "2x + y = 5\nx - y = 1"
    ok, mat, vars_detectadas, _ = AnalizadorSistema.parsear_sistema(texto)
    assert ok and mat is not None
    assert mat.filas == 2 and mat.columnas == 3
    assert vars_detectadas == ["x", "y"]


def test_validadores_y_reglas_dominio():
    """Valida parseo numérico exacto y validación de bases numéricas."""
    ok, frac, _ = ValidadorMatriz.parsear_numero_exacto("7/3")
    assert ok and frac == Fraction(7, 3)

    assert validar_entrada_base("1010", 2)[0] is True
    assert validar_entrada_base("FF", 16)[0] is True
    assert validar_entrada_base("109", 8)[0] is False

    assert validar_datos_transferencia_matriz([[1, 2], [3, 4]], 5)[0] is True
    assert validar_datos_transferencia_matriz([[1, 2]], 5)[0] is False
