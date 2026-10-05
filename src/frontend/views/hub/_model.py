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


@dataclass(frozen=True)
class InitialSelection:
    """Estado de seleccion focal inicial deducido de historial o estado vacio."""
    pillar_id: str
    tile_key: str
    has_history: bool


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
        pillars.append(PillarModel(id=pillar.id, short_name=pillar.short_name, tiles=tiles))
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
