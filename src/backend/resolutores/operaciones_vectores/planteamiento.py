"""Pasos pedagógicos de planteamiento previo y verificación formal para combinación lineal."""

from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.formateadores import (
    formatear_combinacion_lineal_vector,
    formatear_componente_escalar,
    formatear_expresion_lineal,
    formatear_variable_latex,
    formatear_vector_latex,
    matriz_aumentada_a_latex,
    vector_columna_a_latex,
)
from src.backend.utilidades.formateadores import (
    formatear_fraccion_str,
    numero_a_latex,
)


def _empaquetar_pasos_planteamiento(
    latex_pasos: tuple[str, str, str, str, str, str],
    mat_aug: Matriz | None,
) -> list[dict]:
    """Empaqueta la lista de los 5 pasos con metadatos y matrices asociadas."""
    p1, p2, p3, p3_desc, p4, p5 = latex_pasos
    return [
        {"numero_paso": 1, "step_number": 1, "descripcion": "1. Ecuación vectorial con incógnitas (pesos):", "detail_latex": p1, "matriz": mat_aug, "matrix": mat_aug},
        {"numero_paso": 2, "step_number": 2, "descripcion": "2. Multiplicación de los escalares dentro de cada vector:", "detail_latex": p2, "matriz": mat_aug, "matrix": mat_aug},
        {"numero_paso": 3, "step_number": 3, "descripcion": p3_desc, "detail_latex": p3, "matriz": mat_aug, "matrix": mat_aug},
        {"numero_paso": 4, "step_number": 4, "descripcion": "4. Sistema de ecuaciones lineales equivalente:", "detail_latex": p4, "matriz": mat_aug, "matrix": mat_aug},
        {"numero_paso": 5, "step_number": 5, "descripcion": "5. Matriz aumentada del sistema [A | b]:", "detail_latex": p5, "matriz": mat_aug, "matrix": mat_aug},
    ]


def _construir_paso2_vecs(vectores: list[Matriz], var_tex: list[str], n: int) -> str:
    """Genera la expresión LaTeX para la distribución escalar en componentes."""
    vecs = []
    for j, v in enumerate(vectores):
        var = var_tex[j]
        filas = [formatear_componente_escalar(v.obtener(i, 0), var) for i in range(n)]
        vecs.append(r"\begin{bmatrix} " + r" \\ ".join(filas) + r" \end{bmatrix}")
    return " + ".join(vecs)


def construir_pasos_planteamiento(
    b: Matriz,
    vectores: list[Matriz],
    nombres_variables: list[str],
    aumentada: Matriz | None = None,
) -> list[dict]:
    """Genera los 5 pasos de planteamiento pedagógico formal (David C. Lay)."""
    k = len(vectores)
    n = b.filas
    var_tex = [formatear_variable_latex(v) for v in nombres_variables]
    b_tex = vector_columna_a_latex(b)

    paso1_terminos = [f"{var} {vector_columna_a_latex(v)}" for var, v in zip(var_tex, vectores)]
    paso1_latex = f"{' + '.join(paso1_terminos)} = {b_tex}"
    paso2_latex = f"{_construir_paso2_vecs(vectores, var_tex, n)} = {b_tex}"

    lhs_filas = [
        formatear_expresion_lineal([vectores[j].obtener(i, 0) for j in range(k)], var_tex)
        for i in range(n)
    ]
    paso3_latex = r"\begin{bmatrix} " + r" \\ ".join(lhs_filas) + r" \end{bmatrix} = " + b_tex
    paso3_desc = (
        "3. Igualdad vectorial componente a componente (un solo vector):"
        if k == 1
        else "3. Suma vectorial componente a componente (Lado Izquierdo):"
    )

    ecuaciones = [f"{lhs_filas[i]} = {numero_a_latex(b.obtener(i, 0))}" for i in range(n)]
    paso4_latex = r"\begin{cases} " + r" \\ ".join(ecuaciones) + r" \end{cases}"
    paso5_latex = matriz_aumentada_a_latex(vectores, b)

    mat_aug = aumentada.clonar() if aumentada else None
    return _empaquetar_pasos_planteamiento(
        (paso1_latex, paso2_latex, paso3_latex, paso3_desc, paso4_latex, paso5_latex),
        mat_aug,
    )


def _evaluar_vector_y(
    b: Matriz,
    vectores: list[Matriz],
    coeficientes: list[Fraction],
) -> tuple[list[Fraction], str, str]:
    """Evalúa numéricamente el vector y y genera su representación LaTeX."""
    n = b.filas
    y_vals = []
    for i in range(n):
        comp = Fraction(0)
        for j, v in enumerate(vectores):
            comp += coeficientes[j] * Fraction(v.obtener(i, 0))
        y_vals.append(comp)

    y_matriz = Matriz(n, 1, [[comp] for comp in y_vals])
    y_col_latex = vector_columna_a_latex(y_matriz)
    evaluated_latex = rf"\mathbf{{y}} = {y_col_latex}"
    return y_vals, y_col_latex, evaluated_latex


def _construir_detalle_latex_comprobacion(
    comb_symb: str,
    lhs_sub_latex: str,
    y_col_latex: str,
    meta_comp: tuple[bool, list[Fraction], Matriz, list[str]],
) -> tuple[str, str]:
    """Genera la comparación LaTeX y el bloque completo con compatibilidad hacia atrás."""
    coincide, y_vals, b, nombres_variables = meta_comp
    b_col_latex = vector_columna_a_latex(b)
    status_text = r"(\checkmark \text{ Coincide})" if coincide else r"(\times \text{ No coincide})"
    comparison_latex = rf"\mathbf{{y}} = {y_col_latex} \stackrel{{?}}{{=}} {b_col_latex} = \mathbf{{b}} \quad {status_text}"
    eq_symbol = "=" if coincide else r"\neq"
    legacy_y = " \\\\ ".join(numero_a_latex(c) for c in y_vals)
    legacy_b = " \\\\ ".join(numero_a_latex(b.obtener(i, 0)) for i in range(b.filas))
    legacy_compat = rf"% {', '.join(nombres_variables)} \begin{{pmatrix}} {legacy_y} \end{{pmatrix}} \begin{{pmatrix}} {legacy_b} \end{{pmatrix}}"
    full_latex = rf"\mathbf{{y}} = {comb_symb} = {lhs_sub_latex} {eq_symbol} {y_col_latex} = \mathbf{{b}} \quad {status_text} {legacy_compat}"
    return comparison_latex, full_latex


def _construir_terminos_sustitucion(
    coeficientes: list[Fraction],
    vectores: list[Matriz],
) -> str:
    """Genera la sustitución de coeficientes y vectores en LaTeX."""
    terminos = []
    for c, v in zip(coeficientes, vectores):
        c_f = Fraction(c)
        c_tex = numero_a_latex(c_f)
        term_c = rf"\left({c_tex}\right)" if c_f.denominator != 1 else f"({c_tex})"
        terminos.append(f"{term_c} {vector_columna_a_latex(v)}")
    return " + ".join(terminos)


def _construir_descripcion_comprobacion(
    coeficientes: list[Fraction],
    nombres_vec: list[str],
    valores_y: list[Fraction],
    b: Matriz,
    coincide: bool,
) -> str:
    """Genera la descripción textual legible de la comprobación formal."""
    terminos_plano = [f"({formatear_fraccion_str(c)})·{nombres_vec[j]}" for j, c in enumerate(coeficientes)]
    izq_plano = " + ".join(terminos_plano)
    y_plano = ", ".join(formatear_fraccion_str(val) for val in valores_y)
    b_plano = ", ".join(formatear_fraccion_str(b.obtener(i, 0)) for i in range(b.filas))
    return f"Comprobación formal: y = {izq_plano} = ({y_plano})ᵀ vs b = ({b_plano})ᵀ → {'OK' if coincide else 'FALLA'}"


def construir_paso_comprobacion(
    b: Matriz,
    vectores: list[Matriz],
    coeficientes: list[Fraction],
    nombres_variables: list[str],
    nombres_vectores: list[str] | None = None,
) -> dict:
    """Construye el paso de verificación formal y = c_1·v_1 + ... + c_k·v_k."""
    k, n = len(vectores), b.filas
    nombres_vec = nombres_vectores if nombres_vectores else [f"v_{j + 1}" for j in range(k)]
    var_tex = [formatear_variable_latex(var) for var in nombres_variables]
    vec_tex = [formatear_vector_latex(v) for v in nombres_vec]

    formula_latex = rf"\mathbf{{y}} = {' + '.join([f'{var}{vt}' for var, vt in zip(var_tex, vec_tex)])}"
    sub_izq_latex = _construir_terminos_sustitucion(coeficientes, vectores)
    sustitucion_latex = rf"\mathbf{{y}} = {sub_izq_latex}"

    valores_y, y_col_latex, vector_evaluado_latex = _evaluar_vector_y(b, vectores, coeficientes)
    coincide = all(valores_y[i] == Fraction(b.obtener(i, 0)) for i in range(n))

    comb_simb = formatear_combinacion_lineal_vector(coeficientes, nombres_vec)
    comp_latex, full_latex = _construir_detalle_latex_comprobacion(
        comb_simb, sub_izq_latex, y_col_latex, (coincide, valores_y, b, nombres_variables)
    )
    desc = _construir_descripcion_comprobacion(coeficientes, nombres_vec, valores_y, b, coincide)

    return {
        "descripcion": desc,
        "description": desc,
        "formula_latex": formula_latex,
        "sustitucion_latex": sustitucion_latex,
        "substitution_latex": sustitucion_latex,
        "vector_evaluado_latex": vector_evaluado_latex,
        "evaluated_vector_latex": vector_evaluado_latex,
        "comparacion_latex": comp_latex,
        "comparison_latex": comp_latex,
        "detalle_latex": full_latex,
        "detail_latex": full_latex,
        "coincide": coincide,
    }

