"""Tests for geometry navigation integration."""
from src.frontend.navigation import (
    nav_groups,
    route_of,
    breadcrumb,
    tool_by_id,
    visible_tools,
    TOOLS,
    NAV_FLAT_ORDER,
)
from src.frontend.views.hub._recent import normalize_recent


def test_visualizador_in_nav_groups():
    """Visualizador appears in nav_groups."""
    all_tool_ids = set()
    for pillar, tools in nav_groups():
        for tool in tools:
            all_tool_ids.add(tool.id)
    assert "visualizador" in all_tool_ids


def test_visualizador_route_of():
    assert route_of("visualizador") == "/visualizador"


def test_visualizador_breadcrumb():
    bc = breadcrumb("/visualizador")
    assert len(bc) == 2
    assert bc[0][0] == "Visualizador geométrico"  # pillar name
    assert bc[1][0] == "Rectas, planos y vectores"  # tool name
    assert bc[1][1] == "/visualizador"


def test_normalize_recent_accepts_visualizador():
    """normalize_recent doesn't reject visualizador."""
    result = normalize_recent(["visualizador", "sistemas", "bases"])
    tool_ids = [t.id for t in result]
    assert "visualizador" in tool_ids


def test_registry_unique_routes():
    """All routes remain unique after adding visualizador."""
    routes = [t.route for t in TOOLS]
    assert len(routes) == len(set(routes))


def test_registry_unique_ids():
    """All IDs remain unique."""
    ids = [t.id for t in TOOLS]
    assert len(ids) == len(set(ids))


def test_nav_flat_order_includes_visualizador():
    assert "visualizador" in NAV_FLAT_ORDER


def test_visualizador_enabled():
    vis = tool_by_id("visualizador")
    assert vis.enabled
