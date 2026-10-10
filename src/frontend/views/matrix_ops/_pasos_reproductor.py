"""Adaptador puro de segment_steps al modelo del reproductor de pasos en Matrices."""

from __future__ import annotations

import re

from src.frontend.components.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixOpsController


def limpiar_descripcion_operacion(op_display: str | None, default: str) -> str:
    """Genera una versión legible y en texto plano de operation_display."""
    if not op_display:
        return default
    t = re.sub(r"_\{(\w+)\}", r"\1", str(op_display))
    t = t.replace(r"\cdot", "·").replace("{", "").replace("}", "").strip()
    return " ".join(t.split())


def obtener_explicacion_operacion(tipo_op: str | None) -> str:
    """Devuelve una explicación concisa en español y tuteo según el tipo de operación."""
    t = (tipo_op or "").lower()
    if "suma" in t:
        return "Sumamos las matrices celda a celda."
    if "resta" in t:
        return "Restamos las matrices celda a celda."
    if "escalar" in t:
        return "Multiplicamos cada celda por el escalar."
    if "producto" in t or "multiplicaci" in t:
        return "Cada celda es el producto de una fila de A por una columna de B."
    if "transposi" in t:
        return "Las filas pasan a ser columnas."
    if "negaci" in t:
        return "Cambiamos el signo de cada celda."
    return "Aplicamos la operación celda a celda."


def construir_pasos_matrices(
    respuesta: dict,
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Convierte segment_steps de la respuesta a estructuras inmutables del reproductor.

    Args:
        respuesta: Diccionario devuelto por el controller de matrices.

    Returns:
        Tupla con (pasos, grupos) para ReproductorPasos.
    """
    segment_steps = respuesta.get("segment_steps")
    if not segment_steps or not isinstance(segment_steps, list):
        return (), ()

    total = len(segment_steps)
    pasos: list[PasoReproductor] = []
    varias_suboperaciones = total > 1

    for i, step in enumerate(segment_steps):
        op_type = step.get("operation_type") or "Operación"
        op_disp = step.get("operation_display")
        desc = limpiar_descripcion_operacion(op_disp, f"Operación {i + 1}")
        expl = obtener_explicacion_operacion(op_type)
        meta = MatrixOpsController.build_step_focus(step, i + 1, total)
        grupo_idx = i if varias_suboperaciones else 0

        pasos.append(
            PasoReproductor(
                indice=i,
                tipo="operacion",
                descripcion=desc,
                explicacion=expl,
                indice_grupo=grupo_idx,
                cuerpo=step,
                etiqueta_tipo=op_type,
                meta_explicar=meta,
            )
        )

    if total == 1:
        grupos = [
            GrupoReproductor(
                titulo="Operaciones de la expresión",
                resumen="1 operación",
                tipo="operacion",
                indices_pasos=(0,),
            )
        ]
    else:
        grupos = []
        for i, paso in enumerate(pasos):
            grupos.append(
                GrupoReproductor(
                    titulo=paso.descripcion,
                    resumen="1 operación",
                    tipo="operacion",
                    indices_pasos=(i,),
                )
            )

    return tuple(pasos), tuple(grupos)
