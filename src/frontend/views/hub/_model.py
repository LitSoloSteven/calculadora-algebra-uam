"""Modelo puro de datos para el Hub de Scalaris (sin dependencias de UI)."""
from __future__ import annotations

from dataclasses import dataclass

from src.frontend.navigation import (
    PILLARS,
    default_item_key,
    nav_item_href,
    nav_items,
    pillar_of,
)
from src.frontend.views.hub._recent import pick_featured


@dataclass(frozen=True)
class TileModel:
    """Modelo inmutable de un tile de herramienta o escena en el Hub."""
    key: str
    tool_id: str
    name: str
    desc: str
    icon: str
    href: str


@dataclass(frozen=True)
class PillarModel:
    """Modelo inmutable de un pilar con su lista de tiles asociados."""
    id: str
    short_name: str
    tiles: tuple[TileModel, ...]
    icon: str = ""
    blurb: str = ""
    unit_singular: str = "herramienta"
    unit_plural: str = "herramientas"


@dataclass(frozen=True)
class InitialSelection:
    """Estado de seleccion focal inicial deducido de historial o estado vacio."""
    pillar_id: str
    tile_key: str
    has_history: bool


PILLAR_METADATA: dict[str, dict[str, str]] = {
    "algebra": {
        "blurb": "Sistemas, vectores, matrices e inversa, con cada paso a la vista.",
        "unit_singular": "herramienta",
        "unit_plural": "herramientas",
    },
    "visualizador": {
        "blurb": "Mira rectas, planos y vectores en 2D y 3D.",
        "unit_singular": "escena",
        "unit_plural": "escenas",
    },
    "utilidades": {
        "blurb": "Convierte bases y opera con números romanos.",
        "unit_singular": "herramienta",
        "unit_plural": "herramientas",
    },
}


def format_item_count(count: int, singular: str = "herramienta", plural: str = "herramientas") -> str:
    """Devuelve el conteo con el plural correcto (probada con 0, 1 y N)."""
    unit = singular if count == 1 else plural
    return f"{count} {unit}"


def hub_pillars() -> tuple[PillarModel, ...]:
    """Construye los pilares del Hub en el orden de PILLARS con sus tiles."""
    pillars = []
    for pillar in PILLARS:
        items = nav_items(pillar.id)
        tiles = tuple(
            TileModel(
                key=item.key,
                tool_id=item.tool_id,
                name=item.label,
                desc=item.descriptor,
                icon=item.icon,
                href=nav_item_href(item),
            )
            for item in items
        )
        meta = PILLAR_METADATA.get(pillar.id, {})
        pillars.append(
            PillarModel(
                id=pillar.id,
                short_name=pillar.short_name,
                tiles=tiles,
                icon=pillar.icon,
                blurb=meta.get("blurb", ""),
                unit_singular=meta.get("unit_singular", "herramienta"),
                unit_plural=meta.get("unit_plural", "herramientas"),
            )
        )
    return tuple(pillars)


def matrix_cells(n: int = 3) -> tuple[tuple[str, ...], ...]:
    """Genera una matriz identidad n x n con '1' en la diagonal y '0' fuera.

    Raises:
        ValueError: si n < 1.
    """
    if n < 1:
        raise ValueError(f"La dimension de la matriz debe ser mayor o igual a 1, recibido: {n}")
    return tuple(
        tuple("1" if row == col else "0" for col in range(n))
        for row in range(n)
    )


def initial_selection(raw) -> InitialSelection:
    """Calcula el pilar y tile focal inicial a partir del historial sin lanzar excepciones."""
    try:
        tool, has_history = pick_featured(raw)
        pillar_id = pillar_of(tool.id).id
        tile_key = default_item_key(tool.route)
        if tile_key is None:
            tile_key = "sistemas"
        return InitialSelection(pillar_id=pillar_id, tile_key=tile_key, has_history=has_history)
    except Exception:
        return InitialSelection(pillar_id="algebra", tile_key="sistemas", has_history=False)
