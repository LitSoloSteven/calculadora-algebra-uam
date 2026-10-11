"""Funciones auxiliares para parseo numérico y formateo visual en la interfaz."""
from fractions import Fraction
from typing import Any


def a_flotante(valor: Any) -> float:
    """Convierte un entero, flotante, fracción o cadena numérica a float.

    Raises:
        ValueError: si la entrada no es convertible o divide por cero.
    """
    try:
        return float(Fraction(str(valor).strip()))
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise ValueError(f"Valor no numérico: {valor!r}") from error


def formatear_paso_mathjax(paso: str) -> str:
    """Prepara un paso textual o algebraico para su renderizado en MathJax.

    Envuelve prefijos descriptivos antes de dos puntos en \\text{} preservando
    las fórmulas matemáticas posteriores.
    """
    cadena = str(paso).strip()
    if cadena.startswith(r"\text"):
        return cadena
    encabezado, separador, resto = cadena.partition(":")
    if separador and encabezado and not any(c in encabezado for c in r"\{}^_="):
        return rf"\text{{{encabezado}:}}\;{resto}"
    return cadena
