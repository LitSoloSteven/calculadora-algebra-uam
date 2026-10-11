"""Algoritmo de sustitucion hacia atras con expresiones parametricas exactas."""

from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.modelo_solucion import (
    ParametrosSolucion,
    validar_invariantes_parametricos,
)
from src.backend.utilidades.formateadores import (
    formatear_expresion_parametrica,
    formatear_variable_para_latex,
)


def _obtener_etiqueta_variable(
    indice: int,
    nombres_variables: list[str] | None,
) -> str:
    """Devuelve la representacion en LaTeX de una variable del sistema."""
    if nombres_variables and indice < len(nombres_variables):
        return formatear_variable_para_latex(nombres_variables[indice])
    return f"x_{{{indice + 1}}}"


def _inicializar_variables_libres(
    columnas_libres: list[int],
    num_vars: int,
    nombres_variables: list[str] | None,
) -> tuple[dict[int, str], list[dict[str, Fraction]], list[str]]:
    """Construye nombres y terminos iniciales para variables libres."""
    nombres_parametros = ["t", "s", "r", "u", "v"]
    mapa_libres: dict[int, str] = {}
    for idx, col in enumerate(columnas_libres):
        nom = nombres_parametros[idx] if idx < len(nombres_parametros) else f"t_{idx + 1}"
        mapa_libres[col] = nom

    terminos: list[dict[str, Fraction]] = [{} for _ in range(num_vars)]
    pasos_libres: list[str] = []
    if columnas_libres:
        partes = [
            f"{_obtener_etiqueta_variable(c, nombres_variables)} = {mapa_libres[c]}"
            for c in columnas_libres
        ]
        pasos_libres.append(rf"\text{{Variables libres identificadas: }} {', '.join(partes)}")
        for c in columnas_libres:
            terminos[c] = {mapa_libres[c]: Fraction(1)}

    return mapa_libres, terminos, pasos_libres


def _despejar_fila(
    matriz: Matriz,
    fila_idx: int,
    col_pivote: int,
    num_vars: int,
    acumulados: tuple[list[Fraction], list[dict[str, Fraction]]],
) -> tuple[Fraction, dict[str, Fraction]]:
    """Despeja el valor constante y terminos parametricos de una fila pivote."""
    constantes, terminos = acumulados
    piv_val = Fraction(matriz.obtener(fila_idx, col_pivote))
    termino_indep = Fraction(matriz.obtener(fila_idx, num_vars))

    c_val = termino_indep
    t_val: dict[str, Fraction] = {}
    for j in range(col_pivote + 1, num_vars):
        coef = Fraction(matriz.obtener(fila_idx, j))
        if coef != 0:
            c_val -= coef * constantes[j]
            for var, v_coef in terminos[j].items():
                t_val[var] = t_val.get(var, Fraction(0)) - (coef * v_coef)

    c_val /= piv_val
    t_val = {k: v / piv_val for k, v in t_val.items() if (v / piv_val) != 0}
    return c_val, t_val


def _construir_parametros_solucion(
    num_vars: int,
    columnas_libres: list[int],
    mapa_libres: dict[int, str],
    expr_const: list[Fraction],
    expr_terminos: list[dict[str, Fraction]],
) -> ParametrosSolucion:
    """Construye y valida defensivamente el diccionario de solucion parametrica."""
    nombres_ordenados = [mapa_libres[c] for c in columnas_libres]
    direcciones = [
        [expr_terminos[i].get(nom, Fraction(0)) for i in range(num_vars)]
        for nom in nombres_ordenados
    ]
    validar_invariantes_parametricos(direcciones, expr_const, columnas_libres)
    return {
        "num_variables": num_vars,
        "num_vars": num_vars,
        "columnas_libres": list(columnas_libres),
        "free_cols": list(columnas_libres),
        "nombres_parametros": nombres_ordenados,
        "param_names": nombres_ordenados,
        "particular": list(expr_const),
        "direcciones": direcciones,
        "directions": direcciones,
    }


def ejecutar_sustitucion_hacia_atras(
    matriz: Matriz,
    columnas_pivote: list[int],
    num_vars: int,
    nombres_variables: list[str] | None,
) -> tuple[list[str], list[Fraction] | None, list[str], list[int], ParametrosSolucion]:
    """Resuelve la sustitucion regresiva construyendo representacion parametrica."""
    columnas_libres = [c for c in range(num_vars) if c not in columnas_pivote]
    mapa_libres, expr_terminos, pasos = _inicializar_variables_libres(
        columnas_libres, num_vars, nombres_variables
    )
    expr_const = [Fraction(0)] * num_vars

    for i in range(len(columnas_pivote) - 1, -1, -1):
        p_col = columnas_pivote[i]
        c_val, t_val = _despejar_fila(matriz, i, p_col, num_vars, (expr_const, expr_terminos))
        expr_const[p_col] = c_val
        expr_terminos[p_col] = t_val
        etiqueta = _obtener_etiqueta_variable(p_col, nombres_variables)
        pasos.append(f"{etiqueta} = {formatear_expresion_parametrica(c_val, t_val)}")

    solucion = [
        formatear_expresion_parametrica(expr_const[i], expr_terminos[i])
        for i in range(num_vars)
    ]
    solucion_exacta = None if columnas_libres else list(expr_const)
    params = _construir_parametros_solucion(
        num_vars, columnas_libres, mapa_libres, expr_const, expr_terminos
    )
    return solucion, solucion_exacta, pasos, columnas_libres, params
