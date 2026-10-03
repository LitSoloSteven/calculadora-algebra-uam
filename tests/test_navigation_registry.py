"""Pruebas unitarias para el registro central de taxonomía y navegación (Fase 1)."""
import pytest

from src.frontend.components.icons import icon_svg
from src.frontend.navigation import (
    NAV_FLAT_ORDER,
    PILLARS,
    TOOLS,
    breadcrumb,
    legacy_redirects,
    pillar_of,
    route_of,
    tool_by_id,
    tool_by_route,
    visible_tools,
)


def test_unique_identifiers_and_paths():
    """Verifica la unicidad de IDs de pilares, herramientas y rutas legacy."""
    pillar_ids = [p.id for p in PILLARS]
    assert len(pillar_ids) == len(set(pillar_ids)), "Existen IDs duplicados en PILLARS"

    tool_ids = [t.id for t in TOOLS]
    assert len(tool_ids) == len(set(tool_ids)), "Existen IDs duplicados en TOOLS"

    tool_routes = [t.route for t in TOOLS]
    assert len(tool_routes) == len(set(tool_routes)), "Existen rutas canónicas duplicadas en TOOLS"

    legacy_paths = [r.path for r in legacy_redirects()]
    assert len(legacy_paths) == len(set(legacy_paths)), "Existen paths duplicados en legacy_redirects"


def test_routes_format():
    """Verifica que las rutas inicien con '/' y no terminen con barra final."""
    for tool in TOOLS:
        assert tool.route.startswith("/"), f"Ruta {tool.route} debe iniciar con '/'"
        if tool.route != "/":
            assert not tool.route.endswith("/"), f"Ruta {tool.route} no debe terminar con '/'"

    for redirect in legacy_redirects():
        assert redirect.path.startswith("/"), f"Path legacy {redirect.path} debe iniciar con '/'"
        if redirect.path != "/":
            assert not redirect.path.endswith("/"), f"Path legacy {redirect.path} no debe terminar con '/'"
        assert redirect.target_route.startswith("/"), f"Destino {redirect.target_route} debe iniciar con '/'"
        if redirect.target_route != "/":
            assert not redirect.target_route.endswith("/"), f"Destino {redirect.target_route} no debe terminar con '/'"


def test_legacy_routes_do_not_collide_with_current_routes():
    """Garantiza que ninguna ruta legacy coincida con una ruta canónica actual."""
    current_routes = {t.route for t in TOOLS}
    legacy_paths = {r.path for r in legacy_redirects()}
    overlap = current_routes.intersection(legacy_paths)
    assert not overlap, f"Colisión detectada entre rutas canónicas y legacy: {overlap}"


def test_all_referenced_pillars_exist():
    """Confirma que todo pilar referenciado por una herramienta exista en PILLARS."""
    pillar_map = {p.id: p for p in PILLARS}
    for tool in TOOLS:
        assert tool.pillar_id in pillar_map, f"Herramienta '{tool.id}' referencia pilar inexistente '{tool.pillar_id}'"
        resolved_pillar = pillar_of(tool.id)
        assert resolved_pillar.id == tool.pillar_id


def test_enabled_tools_have_non_empty_icons():
    """Verifica que cada herramienta habilitada devuelva un SVG válido y no vacío."""
    for tool in visible_tools():
        svg = icon_svg(tool.icon)
        assert isinstance(svg, str) and svg.strip().startswith("<svg"), (
            f"Herramienta '{tool.id}' con icono '{tool.icon}' no genera un SVG válido"
        )


def test_page_titles_format():
    """Confirma que todo título de página termine con el sufijo oficial '| Scalaris'."""
    for tool in TOOLS:
        assert tool.page_title.endswith("| Scalaris"), (
            f"El page_title de '{tool.id}' ('{tool.page_title}') no termina con '| Scalaris'"
        )


def test_tool_by_route_normalization():
    """Verifica que tool_by_route ignore query parameters y barras finales."""
    sistemas = tool_by_route("/algebra-lineal/sistemas/?method=gauss-jordan&x=1")
    assert sistemas is not None and sistemas.id == "sistemas"

    inversa = tool_by_route("/algebra-lineal/inversa/")
    assert inversa is not None and inversa.id == "inversa"

    assert tool_by_route("/ruta-completamente-inexistente") is None
    assert tool_by_route("/algebra-lineal/inexistente") is None


def test_visualizador_excluded_from_visible_tools():
    """Valida que el visualizador geométrico esté deshabilitado y fuera de visible_tools."""
    vis = tool_by_id("visualizador")
    assert not vis.enabled, "Visualizador debe estar registrado con enabled=False"
    visible_ids = {t.id for t in visible_tools()}
    assert "visualizador" not in visible_ids, "Visualizador no debe figurar en visible_tools()"


def test_nav_flat_order_matches_visible_tools():
    """Comprueba que NAV_FLAT_ORDER cubra exactamente el conjunto de herramientas visibles."""
    visible_ids = {t.id for t in visible_tools()}
    assert set(NAV_FLAT_ORDER) == visible_ids, (
        f"NAV_FLAT_ORDER {set(NAV_FLAT_ORDER)} difiere del set de visible_tools {visible_ids}"
    )


def test_breadcrumb_structure():
    """Valida la generación de migas de pan y el comportamiento ante rutas inexistentes."""
    bc = breadcrumb("/algebra-lineal/inversa")
    assert bc == (("Álgebra lineal", None), ("Matriz inversa", "/algebra-lineal/inversa"))

    bc_query = breadcrumb("/algebra-lineal/sistemas?method=gauss")
    assert bc_query == (("Álgebra lineal", None), ("Sistemas de ecuaciones", "/algebra-lineal/sistemas"))

    bc_inexistente = breadcrumb("/ruta/falsa/123")
    assert bc_inexistente == ()
