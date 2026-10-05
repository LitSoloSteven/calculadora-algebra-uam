"""Geometria pura de la escalera del Hub. Sin NiceGUI ni efectos."""
from __future__ import annotations

from collections.abc import Sequence

BOARD_COLUMNS: int = 4
HUB_STAIRCASE: bool = True
HUB_BRACKETS: bool = True


def step_offset(index: int, columns: int = BOARD_COLUMNS) -> int:
    """Columnas que se desplaza el peldaño de indice dado (0 para el primero)."""
    if index < 0:
        raise ValueError("index debe ser mayor o igual a 0")
    if columns < 1:
        raise ValueError("columns debe ser mayor o igual a 1")
    return min(index, columns - 1)


def step_span(index: int, columns: int = BOARD_COLUMNS) -> int:
    """Columnas disponibles para el peldaño de indice dado."""
    return columns - step_offset(index, columns)


def board_fits(counts: Sequence[int], columns: int = BOARD_COLUMNS) -> bool:
    """True si cada peldaño cabe en una sola fila de su grilla."""
    return all(count <= step_span(index, columns) for index, count in enumerate(counts))


def board_classes() -> str:
    """Clases del tablero; lee los modificadores al llamar (permite probarlos)."""
    classes = ["hub-board"]
    if not HUB_STAIRCASE:
        classes.append("hub-board-flat")
    if not HUB_BRACKETS:
        classes.append("hub-board-bare")
    return " ".join(classes)


def step_class(index: int) -> str:
    """Clases de un peldaño: base mas variante por indice (hub-step-0 a hub-step-3)."""
    return f"hub-step hub-step-{step_offset(index)}"
