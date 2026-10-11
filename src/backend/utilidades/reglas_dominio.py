"""Reglas de dominio y validaciones centralizadas del backend."""

import re
from typing import Any

EXPRESIONES_REGULARES_BASES = {
    10: re.compile(r"^-?\d+$"),
    2: re.compile(r"^-?[01]+$"),
    8: re.compile(r"^-?[0-7]+$"),
    16: re.compile(r"^-?[0-9a-fA-F]+$"),
}


def validar_entrada_base(valor: str, base: int) -> tuple[bool, str]:
    """Valida si una cadena de texto es válida para la base numérica especificada."""
    cadena_limpia = valor.strip().replace(" ", "")
    if not cadena_limpia:
        return False, "El valor está vacío."

    patron = EXPRESIONES_REGULARES_BASES.get(base)
    if not patron:
        return False, f"Base {base} no soportada."

    if not patron.match(cadena_limpia):
        return False, f"El valor '{valor}' contiene caracteres no válidos para la base {base}."

    return True, "Entrada válida."


def validar_datos_transferencia_matriz(
    datos: Any,
    dimension_maxima: int,
) -> tuple[bool, str]:
    """Valida una matriz cuadrada para transferencia segura entre vistas."""
    if not isinstance(datos, list) or not datos:
        return False, "La estructura de matriz no contiene datos válidos."

    dimension = len(datos)
    if dimension > dimension_maxima:
        return False, f"La dimensión ({dimension}) supera el límite permitido ({dimension_maxima})."

    for fila in datos:
        if not isinstance(fila, list) or len(fila) != dimension:
            return False, "La matriz no es cuadrada o sus filas son irregulares."

    return True, "Datos de matriz conformes."


def validar_datos_transferencia_vectores(
    vectores: Any,
    min_vectores: int = 1,
    max_vectores: int = 10,
) -> tuple[bool, str]:
    """Valida una lista de vectores numéricos para transferencia entre vistas."""
    if not isinstance(vectores, list) or len(vectores) < min_vectores:
        return False, f"Se requieren al menos {min_vectores} vectores."

    if len(vectores) > max_vectores:
        return False, f"Se permite un máximo de {max_vectores} vectores."

    longitud_esperada = len(vectores[0]) if isinstance(vectores[0], list) else 0
    if longitud_esperada == 0:
        return False, "Los vectores no pueden estar vacíos."

    for v in vectores:
        if not isinstance(v, list) or len(v) != longitud_esperada:
            return False, "Todos los vectores deben tener la misma dimensión."

    return True, "Datos de vectores conformes."
