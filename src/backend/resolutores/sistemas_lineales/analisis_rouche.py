"""Analisis de sistemas lineales mediante el Teorema de Rouche-Frobenius."""

from src.backend.constantes import (
    SIN_SOLUCION,
    SOLUCION_UNICA,
)


def _generar_explicacion_rouche(
    estado: str,
    rango_a: int,
    rango_aumentada: int,
    num_vars: int,
    es_homogeneo: bool,
) -> tuple[str, str]:
    """Genera la clasificacion y explicacion textual de Rouche-Frobenius."""
    if estado == SIN_SOLUCION:
        return (
            "Sistema Incompatible",
            f"rg(A) = {rango_a} < rg(A|b) = {rango_aumentada}. "
            "Por el Teorema de Rouché-Frobenius, el sistema no tiene solución (incompatible).",
        )
    if estado == SOLUCION_UNICA:
        if es_homogeneo:
            exp = (
                f"Sistema Homogéneo con rg(A) = {rango_a} = n ({num_vars} incógnitas). "
                "Presenta únicamente la solución trivial única (x = 0)."
            )
        else:
            exp = (
                f"rg(A) = rg(A|b) = {rango_a} = n ({num_vars} incógnitas). "
                "Por el Teorema de Rouché-Frobenius, el sistema presenta solución única (compatible determinado)."
            )
        return "Sistema Compatible Determinado", exp

    grados = num_vars - rango_a
    if es_homogeneo:
        exp = (
            f"Sistema Homogéneo con rg(A) = {rango_a} < n ({num_vars} incógnitas). "
            f"Presenta infinitas soluciones no triviales (dimensión del espacio nulo = {grados})."
        )
    else:
        exp = (
            f"rg(A) = rg(A|b) = {rango_a} < n ({num_vars} incógnitas). "
            f"Por el Teorema de Rouché-Frobenius, presenta infinitas soluciones con {grados} variable(s) libre(s)."
        )
    return "Sistema Compatible Indeterminado", exp


def analizar_sistema_rouche(
    estado: str,
    rango_a: int,
    num_vars: int,
    es_homogeneo: bool,
    pivotes: list[int],
) -> dict:
    """Construye el analisis de consistencia, Rouche y dependencia lineal."""
    rango_aumentada = rango_a + 1 if estado == SIN_SOLUCION else rango_a
    clasificacion, explicacion = _generar_explicacion_rouche(
        estado, rango_a, rango_aumentada, num_vars, es_homogeneo
    )
    columnas_indep = (rango_a == num_vars)
    if columnas_indep:
        conclusion_dep = (
            f"Las columnas de la matriz de coeficientes son LINEALMENTE INDEPENDIENTES (rango = {rango_a} = {num_vars} variables)."
        )
    else:
        conclusion_dep = (
            f"Las columnas de la matriz de coeficientes son LINEALMENTE DEPENDIENTES (rango = {rango_a} < {num_vars} variables)."
        )

    return {
        "es_homogeneo": es_homogeneo,
        "rango_a": rango_a,
        "rango_aumentada": rango_aumentada,
        "num_incognitas": num_vars,
        "clasificacion_rouche": clasificacion,
        "explicacion_rouche": explicacion,
        "dependencia_lineal": {
            "son_linealmente_independientes": columnas_indep,
            "conclusion": conclusion_dep,
        },
        "pivotes": pivotes,
    }
