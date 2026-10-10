"""Adaptación de los datos del controlador al modelo compartido de pasos."""

from dataclasses import dataclass
from typing import Mapping

from src.frontend.components.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor


@dataclass(frozen=True)
class _CuerpoPasoInversa:
    """Contexto de solo lectura para pintar la matriz y conservar su procedencia."""

    paso: Mapping
    dimension: int
    total_pasos: int


def adaptar_pasos_inversa(resultado: dict) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Convierte pasos y grupos del controlador a estructuras del reproductor."""
    grupos = tuple(_adaptar_grupo(grupo) for grupo in resultado.get("groups", []))
    pasos_fuente = resultado.get("steps", [])
    pasos = tuple(
        _adaptar_paso(
            paso, indice, len(pasos_fuente), resultado.get("n", 0)
        )
        for indice, paso in enumerate(pasos_fuente)
    )
    return pasos, grupos


def _adaptar_grupo(grupo: dict) -> GrupoReproductor:
    """Convierte un grupo del controlador al modelo inmutable."""
    return GrupoReproductor(
        titulo=grupo.get("title", ""),
        resumen=grupo.get("summary", ""),
        tipo=grupo.get("kind", "otro"),
        indices_pasos=tuple(grupo.get("step_indices", ())),
    )


def _adaptar_paso(paso: dict, indice: int, total: int, n: int) -> PasoReproductor:
    """Convierte un paso y guarda los datos necesarios para la Glosa."""
    tipo = "final" if indice == total - 1 else paso.get("kind", "otro")
    descripcion = paso.get("description", "")
    meta = {"kind": paso.get("kind", "otro"), "op": descripcion}
    return PasoReproductor(
        indice=indice,
        tipo=tipo,
        descripcion=descripcion,
        explicacion=paso.get("explanation", ""),
        indice_grupo=paso.get("group_index", 0),
        cuerpo=_CuerpoPasoInversa(paso, n, total),
        meta_explicar=meta,
    )
