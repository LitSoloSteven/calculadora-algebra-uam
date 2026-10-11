"""Paquete de navegación, taxonomía y resolución de rutas de Scalaris."""

from src.frontend.navigation.catalogo import (
    HUB_ENABLED,
    HUB_PAGE_TITLE,
    HUB_ROUTE,
    NAV_FLAT_ORDER,
    PILLARS,
    TOOLS,
    VISUALIZER_SCENES,
)
from src.frontend.navigation.consultas import (
    breadcrumb,
    default_item_key,
    nav_groups,
    nav_item_href,
    nav_items,
    pillar_for_route,
    pillar_of,
    route_of,
    tool_by_id,
    tool_by_route,
    visible_tools,
)
from src.frontend.navigation.modelo import LegacyRedirect, NavItem, Pillar, Tool
from src.frontend.navigation.redirecciones import legacy_redirects, redirect_location

__all__ = [
    "HUB_ENABLED",
    "HUB_PAGE_TITLE",
    "HUB_ROUTE",
    "LegacyRedirect",
    "NAV_FLAT_ORDER",
    "NavItem",
    "PILLARS",
    "Pillar",
    "TOOLS",
    "Tool",
    "VISUALIZER_SCENES",
    "breadcrumb",
    "default_item_key",
    "legacy_redirects",
    "nav_groups",
    "nav_item_href",
    "nav_items",
    "pillar_for_route",
    "pillar_of",
    "redirect_location",
    "route_of",
    "tool_by_id",
    "tool_by_route",
    "visible_tools",
]
