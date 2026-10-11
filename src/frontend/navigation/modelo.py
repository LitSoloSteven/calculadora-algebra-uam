"""Modelos de datos para taxonomía y navegación de Scalaris."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Pillar:
    """Representa una categoría superior o pilar conceptual en Scalaris."""

    id: str
    name: str
    icon: str = ""
    short_name: str = ""
    prefix: str = ""


@dataclass(frozen=True)
class Tool:
    """Representa una herramienta interactiva dentro de la suite."""

    id: str
    name: str
    descriptor: str
    route: str
    pillar_id: str
    icon: str
    page_title: str
    example_latex: str
    enabled: bool = True


@dataclass(frozen=True)
class LegacyRedirect:
    """Define una regla de redirección desde una ruta previa hacia la canónica."""

    path: str
    target_route: str
    fixed_query: tuple[tuple[str, str], ...] = ()
    permanent: bool = True


@dataclass(frozen=True)
class NavItem:
    """Elemento interactivo de navegación contextual para pilares y escenas."""

    key: str
    label: str
    short_label: str
    descriptor: str
    icon: str
    route: str
    query: tuple[tuple[str, str], ...]
    tool_id: str
