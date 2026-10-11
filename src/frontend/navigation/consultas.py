"""Funciones de consulta e introspección sobre el catálogo de navegación."""
import urllib.parse

from src.frontend.navigation.catalogo import (
    PILLARS,
    TOOLS,
    VISUALIZER_SCENES,
    _PILLARS_BY_ID,
    _SHORT_LABELS,
    _TOOLS_BY_ID,
)
from src.frontend.navigation.modelo import NavItem, Pillar, Tool


def tool_by_id(tool_id: str) -> Tool:
    """Devuelve la herramienta correspondiente al identificador provisto.

    Raises:
        KeyError: si el identificador no existe en el catálogo.
    """
    if tool_id not in _TOOLS_BY_ID:
        raise KeyError(f"Herramienta no encontrada en el registro: '{tool_id}'")
    return _TOOLS_BY_ID[tool_id]


def route_of(tool_id: str) -> str:
    """Devuelve la ruta canónica asociada a la herramienta."""
    return tool_by_id(tool_id).route


def tool_by_route(path: str) -> Tool | None:
    """Busca y devuelve la herramienta activa asociada a la ruta dada."""
    clean_path = path.split("?")[0].rstrip("/")
    if not clean_path:
        clean_path = "/"
    for tool in TOOLS:
        if tool.route.rstrip("/") == clean_path:
            return tool
    return None


def pillar_of(tool_id: str) -> Pillar:
    """Devuelve el pilar al que pertenece la herramienta."""
    tool = tool_by_id(tool_id)
    return _PILLARS_BY_ID[tool.pillar_id]


def visible_tools(pillar_id: str | None = None) -> tuple[Tool, ...]:
    """Devuelve las herramientas habilitadas en orden de catálogo."""
    if pillar_id is None:
        return tuple(t for t in TOOLS if t.enabled)
    return tuple(t for t in TOOLS if t.enabled and t.pillar_id == pillar_id)


def nav_groups() -> tuple[tuple[Pillar, tuple[Tool, ...]], ...]:
    """Devuelve los pilares con al menos una herramienta habilitada."""
    groups = []
    for p in PILLARS:
        tools = visible_tools(p.id)
        if tools:
            groups.append((p, tools))
    return tuple(groups)


def pillar_for_route(path: str) -> Pillar | None:
    """Determina el pilar al que pertenece una ruta base."""
    clean_path = path.split("?")[0].rstrip("/")
    if not clean_path:
        clean_path = "/"
    for p in PILLARS:
        if clean_path == p.prefix or clean_path.startswith(p.prefix + "/"):
            return p
    return None


def breadcrumb(route: str) -> tuple[tuple[str, str | None], ...]:
    """Genera la estructura de migas de pan para una ruta canónica."""
    tool = tool_by_route(route)
    if tool is None:
        return ()
    pillar = _PILLARS_BY_ID[tool.pillar_id]
    return ((pillar.name, None), (tool.name, tool.route))


def _crear_items_algebra() -> tuple[NavItem, ...]:
    """Construye los items de navegación contextual para álgebra lineal."""
    order = ("sistemas", "vectores", "matrices", "inversa")
    items = []
    for tid in order:
        t = tool_by_id(tid)
        items.append(
            NavItem(
                key=t.id,
                label=t.name,
                short_label=_SHORT_LABELS[t.id],
                descriptor=t.descriptor,
                icon=t.icon,
                route=t.route,
                query=(),
                tool_id=t.id,
            )
        )
    return tuple(items)


def _crear_items_visualizador() -> tuple[NavItem, ...]:
    """Construye los items de navegación contextual para el visualizador."""
    items = []
    for escena, label, short_label, descriptor, icon in VISUALIZER_SCENES:
        items.append(
            NavItem(
                key=f"vis:{escena}",
                label=label,
                short_label=short_label,
                descriptor=descriptor,
                icon=icon,
                route="/visualizador",
                query=(("escena", escena),),
                tool_id="visualizador",
            )
        )
    return tuple(items)


def _crear_items_utilidades() -> tuple[NavItem, ...]:
    """Construye los items de navegación contextual para utilidades numéricas."""
    order = ("bases", "romanos")
    items = []
    for tid in order:
        t = tool_by_id(tid)
        items.append(
            NavItem(
                key=t.id,
                label=t.name,
                short_label=_SHORT_LABELS[t.id],
                descriptor=t.descriptor,
                icon=t.icon,
                route=t.route,
                query=(),
                tool_id=t.id,
            )
        )
    return tuple(items)


def nav_items(pillar_id: str) -> tuple[NavItem, ...]:
    """Devuelve los items de navegación contextual asociados a un pilar."""
    if pillar_id in ("algebra", "algebra-lineal"):
        return _crear_items_algebra()
    if pillar_id in ("visualizador", "geometria"):
        return _crear_items_visualizador()
    if pillar_id in ("utilidades", "utilidades-numericas"):
        return _crear_items_utilidades()
    return ()


def nav_item_href(item: NavItem) -> str:
    """Calcula la URL de destino del item con query string codificada si existe."""
    if item.query:
        return f"{item.route}?{urllib.parse.urlencode(item.query)}"
    return item.route


def default_item_key(route: str) -> str | None:
    """Obtiene la clave del item de navegación predeterminado para una ruta."""
    tool = tool_by_route(route)
    if tool is None:
        return None
    if tool.id == "visualizador":
        return "vis:rectas-planos"
    return tool.id
