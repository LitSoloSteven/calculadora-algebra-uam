"""Verificación aritmética exacta de soluciones para sistemas lineales."""

from fractions import Fraction
from typing import Any

from src.backend.utilidades.formateadores import (
    formatear_fraccion_str,
    numero_a_latex,
)


def _a_fraccion_estricta(val: Any) -> tuple[bool, Fraction, str]:
    """Convierte a fracción exacta reutilizando la validación centralizada."""
    from src.backend.utilidades.validadores import ValidadorMatriz

    return ValidadorMatriz.parsear_numero_exacto(val)


def _a_fraccion(val: Any) -> Fraction:
    """Convierte a fracción tolerante reutilizando el parseo centralizado."""
    from src.backend.utilidades.validadores import ValidadorMatriz

    ok, frac, _ = ValidadorMatriz.parsear_numero_exacto(val)
    return frac if ok else Fraction(0)


def _preparsear_entradas_verificacion(
    A: list[list[Any]],
    x: list[Any],
    b: list[Any],
) -> tuple[bool, list[list[Fraction]], list[Fraction], list[Fraction], list[str]]:
    """Convierte matrices y vectores a fracciones exactas previo al cálculo."""
    A_frac: list[list[Fraction]] = []
    for i, fila in enumerate(A):
        fila_frac: list[Fraction] = []
        for j, celda in enumerate(fila):
            ok, frac, err = _a_fraccion_estricta(celda)
            if not ok:
                return False, [], [], [], [f"Error en A[{i + 1},{j + 1}]: {err}"]
            fila_frac.append(frac)
        A_frac.append(fila_frac)

    x_frac: list[Fraction] = []
    for j, celda in enumerate(x):
        ok, frac, err = _a_fraccion_estricta(celda)
        if not ok:
            return False, [], [], [], [f"Error en x[{j + 1}]: {err}"]
        x_frac.append(frac)

    b_frac: list[Fraction] = []
    for i, celda in enumerate(b):
        ok, frac, err = _a_fraccion_estricta(celda)
        if not ok:
            return False, [], [], [], [f"Error en b[{i + 1}]: {err}"]
        b_frac.append(frac)

    return True, A_frac, x_frac, b_frac, []


def _formatear_renglon_verificacion(
    i: int,
    terminos: list[str],
    lhs: Fraction,
    rhs: Fraction,
    como_latex: bool,
) -> str:
    """Genera la cadena de reporte para un renglón de la verificación."""
    sustitucion = " + ".join(terminos)
    es_valida = (lhs == rhs)
    if como_latex:
        estado = "Correcto" if es_valida else "Incorrecto"
        return (
            rf"\text{{Ecuación {i + 1}: }} {sustitucion} = {numero_a_latex(lhs)} \quad "
            rf"(\text{{{estado}}}, \; b_{{{i + 1}}} = {numero_a_latex(rhs)})"
        )
    estado_texto = "Correcto" if es_valida else "Incorrecto"
    return (
        f"Ecuación {i + 1}: {sustitucion} = {formatear_fraccion_str(lhs)}  "
        f"{estado_texto} (b_{i + 1} = {formatear_fraccion_str(rhs)})"
    )


def verificar_solucion(
    A: list[list[Any]],
    x: list[Any],
    b: list[Any],
    como_latex: bool = False,
) -> tuple[bool, list[str]]:
    """Verifica si el vector x satisface el sistema Ax = b con precisión exacta."""
    ok, A_frac, x_frac, b_frac, reporte_error = _preparsear_entradas_verificacion(A, x, b)
    if not ok:
        return False, reporte_error

    es_valida_total = True
    reporte = []

    for i in range(len(A_frac)):
        lhs = Fraction(0)
        terminos = []
        for j in range(len(x_frac)):
            coef = A_frac[i][j]
            var = x_frac[j]
            lhs += coef * var
            if como_latex:
                terminos.append(
                    rf"\left({numero_a_latex(coef)}\right) \cdot \left({numero_a_latex(var)}\right)"
                )
            else:
                terminos.append(f"({formatear_fraccion_str(coef)})·({formatear_fraccion_str(var)})")

        rhs = b_frac[i]
        eq_correcta = (lhs == rhs)
        reporte.append(
            _formatear_renglon_verificacion(i, terminos, lhs, rhs, como_latex)
        )
        if not eq_correcta:
            es_valida_total = False

    return es_valida_total, reporte
