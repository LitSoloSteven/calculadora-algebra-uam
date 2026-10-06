"""Pruebas unitarias de NavItem, VISUALIZER_SCENES y nav_items (Fase P2a)."""
import pytest

from src.frontend.components.icons import icon_svg
from src.frontend.navigation import (
    VISUALIZER_SCENES,
    NavItem,
    default_item_key,
    nav_item_href,
    nav_items,
    visible_tools,
)
from src.frontend.views.geometry.view_geometry import VALID_SCENES


def test_visualizer_scenes_match_view_geometry_valid_scenes():
    """Garantiza que las escenas del registro coincidan exactamente con VALID_SCENES."""
    scene_keys = tuple(item[0] for item in VISUALIZER_SCENES)
    assert scene_keys == VALID_SCENES, (
        f"Desfase en escenas: VISUALIZER_SCENES={scene_keys} vs VALID_SCENES={VALID_SCENES}"
    )


def test_nav_items_by_pillar_and_order():
    """Verifica la lista de items y su orden estricto para cada pilar."""
    algebra_items = nav_items("algebra")
    assert [item.key for item in algebra_items] == ["sistemas", "vectores", "matrices", "inversa"]

    vis_items = nav_items("visualizador")
    assert [item.key for item in vis_items] == ["vis:rectas-planos", "vis:vectores", "vis:combinacion"]

    util_items = nav_items("utilidades")
    assert [item.key for item in util_items] == ["bases", "romanos"]

    # Pilar desconocido devuelve tupla vacia
    assert nav_items("desconocido") == ()


def test_nav_items_unique_keys():
    """Verifica que no existan colisiones entre las claves de navegacion de los pilares."""
    all_keys = []
    for pid in ("algebra", "visualizador", "utilidades"):
        for item in nav_items(pid):
            all_keys.append(item.key)

    assert len(all_keys) == 9
    assert len(set(all_keys)) == 9


def test_nav_items_valid_hrefs_and_non_empty_short_labels():
    """Verifica que cada NavItem tenga un href valido que empiece con '/' y short_label poblado."""
    for pid in ("algebra", "visualizador", "utilidades"):
        for item in nav_items(pid):
            assert isinstance(item, NavItem)
            assert item.short_label.strip() != "", f"short_label vacio en {item.key}"
            assert item.label.strip() != "", f"label vacio en {item.key}"
            assert item.descriptor.strip() != "", f"descriptor vacio en {item.key}"

            href = nav_item_href(item)
            assert href.startswith("/"), f"href invalido para {item.key}: {href}"


def test_default_item_key_for_all_tools_and_invalid_route():
    """Verifica default_item_key para cada ruta del catalogo y None para rutas inexistentes."""
    assert default_item_key("/algebra-lineal/sistemas") == "sistemas"
    assert default_item_key("/algebra-lineal/vectores") == "vectores"
    assert default_item_key("/algebra-lineal/matrices") == "matrices"
    assert default_item_key("/algebra-lineal/inversa") == "inversa"
    assert default_item_key("/utilidades/bases") == "bases"
    assert default_item_key("/utilidades/romanos") == "romanos"
    assert default_item_key("/visualizador") == "vis:rectas-planos"

    # Ruta inexistente
    assert default_item_key("/ruta/inexistente") is None
    assert default_item_key("") is None


def test_nav_item_icons_render_svg():
    """Verifica que el icono de cada NavItem produzca un SVG valido."""
    for pid in ("algebra", "visualizador", "utilidades"):
        for item in nav_items(pid):
            svg = icon_svg(item.icon)
            assert svg.startswith("<svg"), f"Icono invalido o vacio para {item.key}: '{item.icon}'"
            assert "</svg>" in svg


def test_app_shell_hub_route_no_navbar():
    """Verifica que create_app_shell omita la creacion de navbar en HUB_ROUTE."""
    from unittest.mock import patch
    from src.frontend.components.app_shell import create_app_shell
    from src.frontend.navigation import HUB_ROUTE

    with patch("src.frontend.components.app_shell.create_navbar") as mock_navbar:
        create_app_shell(active_route=HUB_ROUTE)
        mock_navbar.assert_not_called()

        create_app_shell(active_route="/algebra-lineal/sistemas", active_key="sistemas")
        mock_navbar.assert_called_once_with(None, active_route="/algebra-lineal/sistemas", active_key="sistemas")


def test_create_navbar_execution():
    """Verifica ejecucion de create_navbar con ruta de pilar, ruta desconocida y active_key explicito."""
    from src.frontend.components.navbar import create_navbar

    # Ruta de pilar deduciendo active_key
    create_navbar(active_route="/algebra-lineal/sistemas")
    # Con active_key explicito
    create_navbar(active_route="/visualizador", active_key="vis:vectores")
    # Ruta desconocida (solo inicio y tema)
    create_navbar(active_route="/ruta-desconocida")

