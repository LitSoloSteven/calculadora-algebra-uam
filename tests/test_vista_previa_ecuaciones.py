"""Pruebas de las transformaciones puras de la vista previa lineal."""

import pytest

from src.frontend.views.linear_systems._vista_previa import (
    analizar_ecuaciones,
    latex_matriz_aumentada,
    latex_sistema,
    matriz_desde_celdas,
)


def test_analiza_sistema_de_dos_variables():
    """Comprueba el análisis de un sistema lineal de dos variables."""
    resultado = analizar_ecuaciones(["2x + 3y = 5", "x - y = 1"])

    assert resultado.estado == "ok"
    assert resultado.variables == ("x", "y")
    assert len(resultado.matriz) == 2


def test_error_conserva_numero_original_de_entrada():
    """Verifica que los espacios vacíos no cambien el número reportado."""
    resultado = analizar_ecuaciones(["x = 1", "", "y = inválido", "z = 2"])

    assert resultado.estado == "error"
    assert resultado.mensaje.startswith("Ecuación 3:")


def test_formatea_fracciones_exactas_y_no_duplica_llaves():
    """Comprueba la fracción exacta y el balance de llaves del LaTeX."""
    resultado = analizar_ecuaciones(["1001/1000x + y = 3"])
    latex = latex_sistema(resultado.matriz, resultado.variables)

    assert r"\frac{1001}{1000}" in latex
    assert "{{" not in latex


def test_formatea_fila_nula_con_termino_independiente():
    """Comprueba que se conserve una fila nula con término independiente."""
    resultado = analizar_ecuaciones(["x + y = 3", "0 = 5"])

    assert resultado.estado == "ok"
    assert "0 = 5" in latex_sistema(resultado.matriz, resultado.variables)


def test_ecuaciones_vacias_y_mensajes_no_usan_raya_larga():
    """Comprueba el estado vacío y la limpieza del texto mostrado."""
    resultado = analizar_ecuaciones(["", "   "])

    assert resultado.estado == "vacio"
    assert "—" not in resultado.mensaje


def test_analiza_sistema_de_diez_ecuaciones():
    """Verifica el análisis de un sistema con diez ecuaciones y variables."""
    lineas = [f"x{indice} + x1 = {indice}" for indice in range(1, 11)]
    resultado = analizar_ecuaciones(lineas)

    assert resultado.estado == "ok"
    assert len(resultado.matriz) == 10
    assert len(resultado.variables) == 10


def test_formatea_variables_de_varias_letras():
    """Comprueba el formato de nombres de variable con varias letras."""
    resultado = analizar_ecuaciones(["velocity + mass = 4"])
    latex = latex_sistema(resultado.matriz, resultado.variables)

    assert r"\text{mass}" in latex
    assert r"\text{velocity}" in latex


def test_matriz_aumentada_usa_fracciones_y_marca_celdas_invalidas():
    """Conserva fracciones exactas y marca en gris las celdas no válidas."""
    resultado = matriz_desde_celdas([["1/2", "invalido"]], ["3"])
    latex = latex_matriz_aumentada(resultado.matriz, len(resultado.variables))

    assert resultado.estado == "error"
    assert resultado.mensaje == "Corrige los valores inválidos para ver las ecuaciones."
    assert r"\frac{1}{2}" in latex
    assert r"\color{gray}{?}" in latex


def test_resultado_es_inmutable_tambien_en_su_matriz():
    """Comprueba que no se puedan cambiar los datos del resultado."""
    resultado = analizar_ecuaciones(["x = 1"])

    with pytest.raises(TypeError):
        resultado.matriz[0][0] = 2


def test_limpia_raya_larga_reflejada_en_error_del_parser():
    """Evita que un texto inválido refleje una raya larga en el mensaje."""
    resultado = analizar_ecuaciones(["x — = 1"])

    assert "—" not in resultado.mensaje


def test_limita_el_tamano_del_texto_antes_de_parsearlo():
    """Rechaza una entrada excesiva antes de llamar al parser de dominio."""
    resultado = analizar_ecuaciones(["x = " + "1" * 2049])

    assert resultado.estado == "error"
    assert "2048 caracteres" in resultado.mensaje


def test_limita_la_cantidad_de_variables_mostradas():
    """Evita crear una vista previa desproporcionada por muchas variables."""
    ecuacion = " + ".join(f"x{indice}" for indice in range(11)) + " = 1"
    resultado = analizar_ecuaciones([ecuacion])

    assert resultado.estado == "error"
    assert "10 variables" in resultado.mensaje
