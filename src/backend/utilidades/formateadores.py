"""Funciones de formateo textual y LaTeX para números y expresiones."""

from fractions import Fraction
import re
from typing import Dict

from src.backend.constantes import (
    CERO_EPSILON,
    DECIMALES_VISUALIZACION,
    LIMITE_DENOMINADOR_LATEX,
    LIMITE_VISUALIZACION_FRACCION,
    TOLERANCIA_COINCIDENCIA_FRACCION,
    TOLERANCIA_FRACCION_VISUALIZACION,
)


def formatear_variable_para_latex(nombre_variable: str) -> str:
    """Convierte el identificador de una variable a notación LaTeX con subíndice."""
    m = re.match(r"^([a-zA-Z]+)(\d+)$", nombre_variable)
    if m:
        letras, digitos = m.groups()
        return f"{letras}_{{{digitos}}}"
    if len(nombre_variable) > 1:
        return f"\\text{{{nombre_variable}}}"
    return nombre_variable


def formatear_fraccion_str(valor: float | Fraction | int) -> str:
    """Formatea valores a cadenas fraccionarias exactas o decimales legibles."""
    if isinstance(valor, (int, Fraction)):
        f = Fraction(valor)
        if f.denominator == 1:
            return str(f.numerator)
        return f"{f.numerator}/{f.denominator}"

    if isinstance(valor, float):
        if abs(valor) < CERO_EPSILON:
            return "0"
        frac = Fraction(valor).limit_denominator(LIMITE_VISUALIZACION_FRACCION)
        if abs(float(frac) - valor) < TOLERANCIA_FRACCION_VISUALIZACION:
            if frac.denominator == 1:
                return str(frac.numerator)
            return f"{frac.numerator}/{frac.denominator}"
        return f"{valor:.{DECIMALES_VISUALIZACION}f}".rstrip("0").rstrip(".")

    return str(valor)


def numero_a_latex(valor: float | Fraction | int) -> str:
    """Convierte un valor numérico a expresión fraccionaria formateada para LaTeX."""
    if isinstance(valor, (int, Fraction)):
        f = Fraction(valor)
        if f == 0:
            return "0"
        num, den = f.numerator, f.denominator
        if den == 1:
            return str(num)
        signo = "-" if num < 0 else ""
        return f"{signo}\\frac{{{abs(num)}}}{{{den}}}"

    if isinstance(valor, float):
        if abs(valor) < TOLERANCIA_COINCIDENCIA_FRACCION:
            return "0"
        frac = Fraction(valor).limit_denominator(LIMITE_DENOMINADOR_LATEX)
        if abs(float(frac) - valor) < TOLERANCIA_FRACCION_VISUALIZACION:
            num, den = frac.numerator, frac.denominator
            if den == 1:
                return str(num)
            signo = "-" if num < 0 else ""
            return f"{signo}\\frac{{{abs(num)}}}{{{den}}}"
        return f"{valor:.{DECIMALES_VISUALIZACION}f}".rstrip("0").rstrip(".")

    return str(valor)


def formatear_expresion_parametrica(
    constante: Fraction,
    terminos: Dict[str, Fraction],
) -> str:
    """Convierte constantes y términos lineales a una cadena paramétrica ordenada."""
    partes = []
    tiene_constante = (constante != 0) or not terminos

    if tiene_constante:
        partes.append(formatear_fraccion_str(constante))

    for variable, coeficiente in terminos.items():
        if coeficiente == 0:
            continue
        coef_abs = abs(coeficiente)
        if coef_abs.denominator == 1:
            num = coef_abs.numerator
            c_str = "" if num == 1 else str(num)
        else:
            c_str = f"({coef_abs.numerator}/{coef_abs.denominator})"

        if not partes:
            prefijo = "" if coeficiente > 0 else "-"
            partes.append(f"{prefijo}{c_str}{variable}")
        else:
            signo = "+" if coeficiente > 0 else "-"
            partes.append(f"{signo} {c_str}{variable}")

    return " ".join(partes) if partes else "0"
