"""Estructuras inmutables para pasos y grupos del reproductor compartido."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PasoReproductor:
    """Describe los datos de un paso visual.

    Los campos guardan su índice, tipo, textos, fase, cuerpo y metadatos de Glosa.
    """

    indice: int
    tipo: str
    descripcion: str
    explicacion: str = ""
    indice_grupo: int = 0
    cuerpo: Any = None
    etiqueta_tipo: str | None = None
    meta_explicar: dict | None = None


@dataclass(frozen=True)
class GrupoReproductor:
    """Agrupa pasos de una fase con título, resumen y tipo descriptivos."""

    titulo: str
    resumen: str
    tipo: str
    indices_pasos: tuple[int, ...]
