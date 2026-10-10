"""Construcción de pasos y grupos didácticos para el reproductor en Operaciones con Vectores."""

from __future__ import annotations

import re
from typing import Any

from nicegui import ui

from src.backend.models.matrix import Matrix
from src.frontend.components.reproductor_pasos.cuerpos import render_latex
from src.frontend.components.reproductor_pasos.html_tablas import html_tabla_aumentada
from src.frontend.components.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor


class _CuerpoLatex:
    """Cuerpo ejecutable que renderiza la expresión LaTeX mediante render_latex."""

    def __init__(self, latex: str) -> None:
        self.latex = latex

    def __call__(self) -> None:
        render_latex(self.latex)

    def __str__(self) -> str:
        return self.latex


class _CuerpoTexto:
    """Cuerpo ejecutable que renderiza una descripción textual."""

    def __init__(self, texto: str) -> None:
        self.texto = texto

    def __call__(self) -> None:
        ui.label(self.texto).classes("text-sm font-medium text-main text-center")

    def __str__(self) -> str:
        return self.texto


def _limpiar_latex_plano(texto: str) -> str:
    """Elimina comandos LaTeX para dejar texto plano en la descripción."""
    t = re.sub(r"\\text\{([^}]*)\}", r"\1", str(texto))
    t = t.replace(r"\implies", "=>").replace(r"\;", " ").replace(r"\\", " ")
    return " ".join(re.sub(r"[{}\\]", "", t).split())


def _clasificar_paso_basico(desc: str, latex: str | None) -> tuple[str, str, str, Any]:
    """Clasifica un paso básico según el prefijo de su descripción."""
    if desc.startswith("Iniciando"):
        return (
            "inicial", "Inicial",
            "Iniciamos la operación vector a vector comprobando dimensiones y orientaciones.",
            _CuerpoTexto(desc),
        )
    if desc.startswith("Ajuste de orientación"):
        return (
            "ajuste", "Ajuste",
            "Ajustamos la orientación del vector para que coincida con la del primero.",
            _CuerpoLatex(latex) if latex else _CuerpoTexto(desc),
        )
    return (
        "componente", "Componente",
        "Calculamos el resultado correspondiente para esta componente celda a celda.",
        _CuerpoLatex(latex) if latex else _CuerpoTexto(desc),
    )


def construir_pasos_vector_basico(
    respuesta: dict,
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Construye los pasos del reproductor para operaciones básicas de vectores."""
    raw_steps = respuesta.get("steps", [])
    if not raw_steps:
        return (), ()

    items: list[tuple[str, str, str, str, Any]] = []
    for s in raw_steps:
        desc = s.get("description", "")
        tipo, etq, expl, cuerpo = _clasificar_paso_basico(desc, s.get("detail_latex"))
        items.append((tipo, etq, desc, expl, cuerpo))

    final_latex = respuesta.get("result_vector_latex") or (
        respuesta.get("latex_details", [""])[-1] if respuesta.get("latex_details") else ""
    )
    if final_latex:
        items.append((
            "resultado", "Resultado", "Vector resultante",
            "Vector resultante obtenido tras evaluar todas las componentes.",
            _CuerpoLatex(final_latex),
        ))

    total = len(items)
    pasos = [
        PasoReproductor(
            indice=i, tipo=t, etiqueta_tipo=etq, descripcion=d, explicacion=exp,
            indice_grupo=0, cuerpo=c,
            meta_explicar={"index": i + 1, "total": total, "kind": t, "op": d, "rows_before": {}, "rows_after": {}, "cols": None},
        )
        for i, (t, etq, d, exp, c) in enumerate(items)
    ]
    resumen = f"{total} pasos" if total != 1 else "1 paso"
    grupo = GrupoReproductor(titulo="Operaciones de componentes", resumen=resumen, tipo="operacion", indices_pasos=tuple(range(total)))
    return tuple(pasos), (grupo,)


def _construir_pasos_planteamiento(
    setup_steps: list[dict], total: int, pasos: list[PasoReproductor], grp_idx: int
) -> list[int]:
    """Construye los pasos del planteamiento algebraico previo."""
    expl_map = {
        1: "Escribimos la ecuación vectorial con una incógnita escalar multiplicando a cada vector.",
        2: "Multiplicamos cada escalar en las componentes del vector correspondiente.",
        3: "Sumamos los vectores componente a componente en el lado izquierdo.",
        4: "Obtenemos el sistema de ecuaciones lineales equivalente igualando componentes.",
        5: "Construimos la matriz aumentada [A | b] con los vectores como columnas y b a la derecha.",
    }
    indices: list[int] = []
    for s in setup_steps:
        idx = len(pasos)
        indices.append(idx)
        n = s.get("step_number", len(indices))
        desc = s.get("description", f"Planteamiento {n}")
        meta = {"index": idx + 1, "total": total, "kind": "planteamiento", "op": desc, "rows_before": {}, "rows_after": {}, "cols": None}
        pasos.append(PasoReproductor(
            indice=idx, tipo="planteamiento", etiqueta_tipo="Planteamiento",
            descripcion=desc, explicacion=expl_map.get(n, desc),
            indice_grupo=grp_idx, cuerpo=_CuerpoLatex(s.get("detail_latex", "")), meta_explicar=meta,
        ))
    return indices


def _construir_pasos_gauss(
    steps_view: list[dict], steps_meta: list[dict], n_vars: int,
    variables: list[str], total: int, pasos: list[PasoReproductor], grp_idx: int
) -> list[int]:
    """Construye los pasos interactivos de eliminación gaussiana sobre la matriz aumentada."""
    indices: list[int] = []
    for s in steps_view:
        idx = len(pasos)
        indices.append(idx)
        kind, desc, expl = s.get("kind", "eliminacion"), s.get("description", ""), s.get("explanation", "")
        mat_dict = s.get("matrix", {})
        mat = Matrix(mat_dict["rows"], mat_dict["cols"], mat_dict["data"]) if isinstance(mat_dict, dict) and "rows" in mat_dict else mat_dict

        cuerpo = html_tabla_aumentada(
            mat, n_vars, filas_cambiadas=tuple(s.get("rows_changed") or ()),
            pivote=tuple(s["pivot"]) if s.get("pivot") is not None else None,
            filas_intercambio=tuple(s["swap_rows"]) if s.get("swap_rows") is not None else (),
            bloque_resultado=False, etiquetas_izq=variables, etiquetas_der=["b"],
        )
        s_idx = s.get("index", len(indices) - 1)
        meta = dict(steps_meta[s_idx]) if s_idx < len(steps_meta) else {
            "index": idx + 1, "total": total, "kind": kind, "op": desc,
            "pivot": s.get("pivot"), "rows_before": {}, "rows_after": {}, "cols": None,
        }
        meta.update({"total": total, "index": idx + 1})
        pasos.append(PasoReproductor(
            indice=idx, tipo=kind, etiqueta_tipo=kind.capitalize(),
            descripcion=desc, explicacion=expl or desc,
            indice_grupo=grp_idx, cuerpo=cuerpo, meta_explicar=meta,
        ))
    return indices


def _construir_pasos_sustitucion(
    back_steps: list[str], total: int, pasos: list[PasoReproductor], grp_idx: int
) -> list[int]:
    """Construye los pasos de sustitución hacia atrás."""
    indices: list[int] = []
    for linea in back_steps:
        idx = len(pasos)
        indices.append(idx)
        op_txt = _limpiar_latex_plano(linea)
        meta = {"index": idx + 1, "total": total, "kind": "sustitucion", "op": op_txt, "rows_before": {}, "rows_after": {}, "cols": None}
        pasos.append(PasoReproductor(
            indice=idx, tipo="sustitucion", etiqueta_tipo="Sustitución",
            descripcion=op_txt, explicacion="Despejamos y sustituimos hacia atrás los valores conocidos.",
            indice_grupo=grp_idx, cuerpo=_CuerpoLatex(linea), meta_explicar=meta,
        ))
    return indices


def _construir_pasos_verificacion(
    v_step: dict, total: int, pasos: list[PasoReproductor], grp_idx: int
) -> list[int]:
    """Construye los 4 pasos formales de comprobación."""
    indices: list[int] = []
    bloques = (
        (v_step.get("formula_latex", ""), "Definición simbólica del vector", "Planteamos la combinación lineal simbólica del vector y."),
        (v_step.get("substitution_latex", ""), "Sustitución de escalares y vectores", "Sustituimos los coeficientes y vectores en la combinación."),
        (v_step.get("evaluated_vector_latex", ""), "Evaluación numérica del vector", "Evaluamos numéricamente el vector resultante de la combinación."),
        (v_step.get("comparison_latex", ""), "Comparación con el vector objetivo b", "Comprobamos si el vector evaluado coincide con el vector b."),
    )
    for latex, desc, expl in bloques:
        idx = len(pasos)
        indices.append(idx)
        meta = {"index": idx + 1, "total": total, "kind": "verificacion", "op": desc, "rows_before": {}, "rows_after": {}, "cols": None}
        pasos.append(PasoReproductor(
            indice=idx, tipo="verificacion", etiqueta_tipo="Verificación",
            descripcion=desc, explicacion=expl,
            indice_grupo=grp_idx, cuerpo=_CuerpoLatex(latex), meta_explicar=meta,
        ))
    return indices


def construir_pasos_combinacion_lineal(
    respuesta: dict,
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Construye las tuplas de pasos y grupos para el reproductor de combinación lineal."""
    if respuesta.get("status") == "ERROR":
        return (), ()

    setup_steps = respuesta.get("setup_steps") or []
    steps_view = respuesta.get("steps_view") or []
    back_steps = respuesta.get("back_substitution_steps") or []
    v_step = respuesta.get("verification_step")
    steps_meta = respuesta.get("steps_meta") or []
    variables = respuesta.get("variables") or []
    n_vars = respuesta.get("n_vars", len(variables))

    num_verif = 4 if v_step else 0
    total = len(setup_steps) + len(steps_view) + len(back_steps) + num_verif
    if total == 0:
        return (), ()

    pasos: list[PasoReproductor] = []
    grupos: list[GrupoReproductor] = []

    if setup_steps:
        idx_setup = _construir_pasos_planteamiento(setup_steps, total, pasos, len(grupos))
        grupos.append(GrupoReproductor(
            titulo="Planteamiento algebraico", resumen=f"{len(idx_setup)} operaciones",
            tipo="planteamiento", indices_pasos=tuple(idx_setup),
        ))

    if steps_view:
        idx_gauss = _construir_pasos_gauss(steps_view, steps_meta, n_vars, variables, total, pasos, len(grupos))
        res_gauss = f"{len(idx_gauss)} operaciones" if len(idx_gauss) != 1 else "1 operación"
        grupos.append(GrupoReproductor(
            titulo="Eliminación gaussiana", resumen=res_gauss,
            tipo="eliminacion", indices_pasos=tuple(idx_gauss),
        ))

    if back_steps:
        idx_sust = _construir_pasos_sustitucion(back_steps, total, pasos, len(grupos))
        res_sust = f"{len(idx_sust)} operaciones" if len(idx_sust) != 1 else "1 operación"
        grupos.append(GrupoReproductor(
            titulo="Sustitución hacia atrás", resumen=res_sust,
            tipo="sustitucion", indices_pasos=tuple(idx_sust),
        ))

    if v_step:
        idx_verif = _construir_pasos_verificacion(v_step, total, pasos, len(grupos))
        grupos.append(GrupoReproductor(
            titulo="Comprobación", resumen="4 operaciones",
            tipo="verificacion", indices_pasos=tuple(idx_verif),
        ))

    return tuple(pasos), tuple(grupos)
