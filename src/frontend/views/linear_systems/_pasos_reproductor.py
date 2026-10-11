"""Construcción de pasos y grupos didácticos para el reproductor en Sistemas Lineales."""

from __future__ import annotations

import re

from src.backend.models.matrix import Matrix
from src.frontend.components.reproductor_pasos.cuerpos import render_latex
from src.frontend.components.reproductor_pasos.html_tablas import html_tabla_aumentada
from src.frontend.components.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from src.frontend.helpers import formatear_paso_mathjax


class _CuerpoLatex:
    """Cuerpo ejecutable que renderiza la expresión LaTeX mediante render_latex."""

    def __init__(self, latex: str) -> None:
        self.latex = latex

    def __call__(self) -> None:
        render_latex(self.latex)

    def __str__(self) -> str:
        return self.latex


def _limpiar_latex_plano(texto: str) -> str:
    """Elimina etiquetas y comandos LaTeX comunes para dejar una descripción corta en texto plano."""
    t = re.sub(r"\\text\{([^}]*)\}", r"\1", str(texto))
    t = t.replace(r"\implies", "=>").replace(r"\;", " ").replace(r"\\", " ")
    t = re.sub(r"[{}\\]", "", t)
    return " ".join(t.split())


def construir_pasos_reproductor(
    respuesta: dict,
    metodo: str | None = None,
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Construye las tuplas de pasos y grupos del reproductor a partir de la respuesta del solver.

    Args:
        respuesta: Diccionario devuelto por el controller (Gauss o Gauss-Jordan).
        metodo: Método ejecutado ('gauss' o 'gauss-jordan').

    Returns:
        Tupla (pasos, grupos) compatibles con ReproductorPasos.
    """
    steps_view = respuesta.get("steps_view", [])
    if not steps_view:
        return (), ()

    groups_view = respuesta.get("groups", [])
    steps_meta = respuesta.get("steps_meta", [])
    back_steps = respuesta.get("back_substitution_steps") or []
    verif_steps = respuesta.get("verification_steps_latex") or []
    variables = respuesta.get("variables")
    n_vars = respuesta.get("n_vars", len(variables) if variables else 0)

    if not variables and n_vars > 0:
        variables = [f"x{i+1}" for i in range(n_vars)]

    total_pasos = len(steps_view) + len(back_steps) + len(verif_steps)

    pasos: list[PasoReproductor] = []
    grupos: list[GrupoReproductor] = []

    # 1. Fases de eliminación (matrices aumentadas)
    for s in steps_view:
        idx = s["index"]
        kind = s.get("kind", "otro")
        desc = s.get("description", "")
        expl = s.get("explanation", "")
        grp_idx = s.get("group_index", 0)

        mat_dict = s.get("matrix", {})
        mat = Matrix(mat_dict["rows"], mat_dict["cols"], mat_dict["data"])

        filas_cambiadas = tuple(s.get("rows_changed") or ())
        pivote = tuple(s["pivot"]) if s.get("pivot") is not None else None
        filas_intercambio = tuple(s["swap_rows"]) if s.get("swap_rows") is not None else ()

        cuerpo = html_tabla_aumentada(
            mat,
            n_vars,
            filas_cambiadas=filas_cambiadas,
            pivote=pivote,
            filas_intercambio=filas_intercambio,
            bloque_resultado=False,
            etiquetas_izq=variables,
            etiquetas_der=["b"],
        )

        meta = steps_meta[idx] if idx < len(steps_meta) else {
            "index": idx + 1,
            "total": total_pasos,
            "kind": kind,
            "op": desc,
            "pivot": pivote,
            "rows_before": {},
            "rows_after": {},
            "cols": None,
        }

        pasos.append(
            PasoReproductor(
                indice=idx,
                tipo=kind,
                descripcion=desc,
                explicacion=expl,
                indice_grupo=grp_idx,
                cuerpo=cuerpo,
                meta_explicar=meta,
            )
        )

    for g in groups_view:
        grupos.append(
            GrupoReproductor(
                titulo=g.get("title", ""),
                resumen=g.get("summary", ""),
                tipo=g.get("kind", "columna"),
                indices_pasos=tuple(g.get("step_indices", ())),
            )
        )

    es_gauss_jordan = str(metodo).lower() in ("gauss-jordan", "gauss_jordan")

    # 2. Fase de sustitución hacia atrás o solución final (si existen pasos)
    if back_steps:
        idx_grupo_sust = len(grupos)
        indices_sust: list[int] = []
        titulo_sust = "Solución final" if es_gauss_jordan else "Sustitución hacia atrás"

        for linea in back_steps:
            current_idx = len(pasos)
            indices_sust.append(current_idx)
            op_texto = _limpiar_latex_plano(linea)
            if es_gauss_jordan:
                expl = "Lectura del valor de la variable a partir de la forma escalonada reducida."
            else:
                expl = "Despejamos y sustituimos hacia atrás los valores conocidos para hallar la incógnita."

            cuerpo = _CuerpoLatex(formatear_paso_mathjax(linea))
            meta = {
                "index": current_idx + 1,
                "total": total_pasos,
                "kind": "sustitucion",
                "op": op_texto,
                "rows_before": {},
                "rows_after": {},
                "cols": None,
            }
            pasos.append(
                PasoReproductor(
                    indice=current_idx,
                    tipo="sustitucion",
                    descripcion=op_texto,
                    explicacion=expl,
                    indice_grupo=idx_grupo_sust,
                    cuerpo=cuerpo,
                    meta_explicar=meta,
                )
            )

        k_sust = len(indices_sust)
        resumen_sust = "1 operación" if k_sust == 1 else f"{k_sust} operaciones"
        grupos.append(
            GrupoReproductor(
                titulo=titulo_sust,
                resumen=resumen_sust,
                tipo="sustitucion",
                indices_pasos=tuple(indices_sust),
            )
        )

    # 3. Fase de comprobación Ax = b (si existen pasos)
    if verif_steps:
        idx_grupo_verif = len(grupos)
        indices_verif: list[int] = []

        for linea in verif_steps:
            current_idx = len(pasos)
            indices_verif.append(current_idx)
            op_texto = _limpiar_latex_plano(linea)
            expl = "Sustituimos la solución en la ecuación original para verificar que se cumple la igualdad."

            cuerpo = _CuerpoLatex(formatear_paso_mathjax(linea))
            meta = {
                "index": current_idx + 1,
                "total": total_pasos,
                "kind": "verificacion",
                "op": op_texto,
                "rows_before": {},
                "rows_after": {},
                "cols": None,
            }
            pasos.append(
                PasoReproductor(
                    indice=current_idx,
                    tipo="verificacion",
                    descripcion=op_texto,
                    explicacion=expl,
                    indice_grupo=idx_grupo_verif,
                    cuerpo=cuerpo,
                    meta_explicar=meta,
                )
            )

        k_verif = len(indices_verif)
        resumen_verif = "1 operación" if k_verif == 1 else f"{k_verif} operaciones"
        grupos.append(
            GrupoReproductor(
                titulo="Comprobación Ax = b",
                resumen=resumen_verif,
                tipo="verificacion",
                indices_pasos=tuple(indices_verif),
            )
        )

    return tuple(pasos), tuple(grupos)
