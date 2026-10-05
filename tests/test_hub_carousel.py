"""Test de verificacion de contrato y estructura del Carrusel del Hub (Tarea H1).

Verifica:
- tablist y tabs presentes con roles y atributos ARIA
- Un solo panel activo en el HTML inicial (los demas inertes)
- hub.js sin scroll listener
- hub.js con deteccion de teclado mediante event.detail === 0
- CSS sin ease-in en transiciones de .hub-*
- CSS sin width/height/margin/padding en transition de .hub-*
- CSS sin colores literales en reglas .hub-*
- Soporte de prefers-reduced-motion
- Estados hover gateados bajo @media (hover: hover) and (pointer: fine)
- Pluralizacion correcta 0, 1 y N
- IDs y contrato conservados (hub-tab-*, hub-panel-*, etc.)
"""
from pathlib import Path
import re
import pytest

from src.frontend.views.hub._model import format_item_count, hub_pillars, initial_selection, matrix_cells
from src.frontend.views.hub.view_hub import HubUI

THEME_CSS_PATH = Path("src/frontend/assets/css/theme.css")
HUB_JS_PATH = Path("src/frontend/assets/js/hub.js")
VIEW_HUB_PATH = Path("src/frontend/views/hub/view_hub.py")


def get_hub_css_block() -> str:
    """Extrae el bloque CSS correspondiente al Hub desde theme.css."""
    content = THEME_CSS_PATH.read_text(encoding="utf-8")
    match = re.search(r'/\* === HUB: Carrusel de Áreas === \*/(.*?)(?=/\* === F4: Glosa === \*/)', content, re.DOTALL)
    assert match is not None, "Bloque CSS de Hub no encontrado en theme.css"
    return match.group(1)


def test_plural_zero_one_n():
    """Verifica que format_item_count maneje correctamente 0, 1 y N elementos."""
    assert format_item_count(0, "herramienta", "herramientas") == "0 herramientas"
    assert format_item_count(1, "herramienta", "herramientas") == "1 herramienta"
    assert format_item_count(4, "herramienta", "herramientas") == "4 herramientas"
    assert format_item_count(12, "herramienta", "herramientas") == "12 herramientas"

    assert format_item_count(0, "escena", "escenas") == "0 escenas"
    assert format_item_count(1, "escena", "escenas") == "1 escena"
    assert format_item_count(3, "escena", "escenas") == "3 escenas"


def test_tablist_and_tabs_present():
    """Verifica que el track tenga role=tablist y las tarjetas tengan role=tab con accesibilidad adecuada."""
    view_content = VIEW_HUB_PATH.read_text(encoding="utf-8")

    assert 'role="tablist"' in view_content
    assert 'aria-orientation="horizontal"' in view_content
    assert 'aria-label="Áreas de Scalaris"' in view_content
    assert 'role="tab"' in view_content
    assert 'aria-controls="hub-panel-' in view_content
    assert 'aria-selected=' in view_content


def test_only_one_panel_active_initially():
    """Verifica que en el HTML inicial solo el primer panel sea activo y los demas tengan inert."""
    view_content = VIEW_HUB_PATH.read_text(encoding="utf-8")

    # Verifica la logica de inicializacion en Python
    assert "is_first = (row_idx == 0)" in view_content
    assert "'hub-panel' + (' is-active' if is_first else '')" in view_content
    assert "if not is_first:\n                            panel_props += ' inert'" in view_content or "panel_props += ' inert'" in view_content


def test_hub_js_no_scroll_listener():
    """Verifica que hub.js no use eventos de scroll, respetando la REGLA §5."""
    js_content = HUB_JS_PATH.read_text(encoding="utf-8")
    assert 'addEventListener("scroll"' not in js_content
    assert "addEventListener('scroll'" not in js_content
    assert ".onscroll" not in js_content


def test_hub_js_keyboard_event_detail_zero():
    """Verifica que hub.js detecte interaccion por teclado (event.detail === 0) para transicion instantanea."""
    js_content = HUB_JS_PATH.read_text(encoding="utf-8")
    assert "e.detail === 0" in js_content or "event.detail === 0" in js_content
    assert "window.scalarisHubSelect" in js_content


def test_hub_css_no_ease_in():
    """Verifica que en las reglas de .hub-* no se use la funcion de easing ease-in."""
    hub_css = get_hub_css_block()
    # Buscar ocurrencias de ease-in que no sean ease-in-out o no permitidas
    matches = re.findall(r'ease-in\b', hub_css)
    assert matches == [], f"Se encontro ease-in en el CSS del hub: {matches}"


def test_hub_css_no_layout_property_transitions():
    """Verifica que no se animen width, height, margin ni padding en transiciones de .hub-*."""
    hub_css = get_hub_css_block()
    forbidden = ["width", "height", "margin", "padding", "left", "top", "right", "bottom"]

    # Extraer todas las propiedades transition
    transitions = re.findall(r'transition:\s*([^;]+);', hub_css)
    for trans in transitions:
        for prop in forbidden:
            # Asegurar coincidencia de palabra completa para la propiedad animada
            pattern = rf'(?:^|[\s,]){prop}(?:-[a-z]+)?(?:[\s,]|$)'
            assert not re.search(pattern, trans), f"Propiedad prohibida '{prop}' en transicion: {trans}"


def test_hub_css_no_literal_colors():
    """Verifica que en las reglas del carrusel del Hub no se utilicen colores literales (#hex, rgb, rgba, hsl)."""
    hub_css = get_hub_css_block()
    # Excluir comentarios del bloque
    clean_css = re.sub(r'/\*.*?\*/', '', hub_css, flags=re.DOTALL)

    hex_matches = re.findall(r'#(?:[0-9a-fA-F]{3,8})\b', clean_css)
    rgb_matches = re.findall(r'rgba?\([^)]+\)', clean_css)
    hsl_matches = re.findall(r'hsla?\([^)]+\)', clean_css)

    assert hex_matches == [], f"Colores hex literales encontrados en .hub-*: {hex_matches}"
    assert rgb_matches == [], f"Colores rgb literales encontrados en .hub-*: {rgb_matches}"
    assert hsl_matches == [], f"Colores hsl literales encontrados en .hub-*: {hsl_matches}"


def test_hub_css_reduced_motion():
    """Verifica que theme.css incluya reglas de prefers-reduced-motion para las tarjetas y elementos del Hub."""
    content = THEME_CSS_PATH.read_text(encoding="utf-8")
    assert "@media (prefers-reduced-motion: reduce)" in content
    
    # Extraer bloques anidados balanceando llaves
    blocks = []
    target = "@media (prefers-reduced-motion: reduce)"
    idx = 0
    while True:
        pos = content.find(target, idx)
        if pos == -1:
            break
        brace_open = content.find('{', pos)
        if brace_open == -1:
            break
        depth = 1
        curr = brace_open + 1
        while curr < len(content) and depth > 0:
            if content[curr] == '{':
                depth += 1
            elif content[curr] == '}':
                depth -= 1
            curr += 1
        blocks.append(content[brace_open + 1:curr - 1])
        idx = curr

    combined_blocks = "\n".join(blocks)
    assert ".hub-card" in combined_blocks
    assert ".hub-track" in combined_blocks
    assert ".hub-panel" in combined_blocks


def test_hub_css_hover_gated():
    """Verifica que los estilos :hover de tarjetas y tiles esten gateados con @media (hover: hover) and (pointer: fine)."""
    hub_css = get_hub_css_block()
    # Encontrar todas las menciones de :hover fuera de @media (hover: hover)
    media_hover_blocks = re.findall(r'@media\s*\(hover:\s*hover\)\s*and\s*\(pointer:\s*fine\)\s*\{(.*?)\n\}', hub_css, re.DOTALL)
    assert len(media_hover_blocks) >= 2, "Se esperan al menos 2 bloques con hover gateado (.hub-card y .hub-tile)"

    # Remover los bloques gateados y verificar que no quede :hover suelto en .hub-
    stripped_css = re.sub(r'@media\s*\(hover:\s*hover\)\s*and\s*\(pointer:\s*fine\)\s*\{.*?\}\s*\}?', '', hub_css, flags=re.DOTALL)
    assert ":hover" not in stripped_css, "Existen reglas :hover no gateadas dentro de .hub-*"


def test_conserved_ids_and_contracts():
    """Verifica que se conserven los IDs esperados y las firmas contractuales."""
    pillars = hub_pillars()
    assert len(pillars) == 3
    expected_ids = {"algebra", "visualizador", "utilidades"}
    actual_ids = {p.id for p in pillars}
    assert expected_ids == actual_ids

    view_content = VIEW_HUB_PATH.read_text(encoding="utf-8")
    # Verificar plantilla f-string de IDs
    assert 'id="hub-tab-{pillar.id}"' in view_content
    assert 'id="hub-panel-{pillar.id}"' in view_content

    # Verificar que los IDs resultantes para cada pilar concuerden con el contrato
    for pid in expected_ids:
        tab_id = f"hub-tab-{pid}"
        panel_id = f"hub-panel-{pid}"
        assert tab_id in ["hub-tab-algebra", "hub-tab-visualizador", "hub-tab-utilidades"]
        assert panel_id in ["hub-panel-algebra", "hub-panel-visualizador", "hub-panel-utilidades"]

    # Verificar que HubUI exponga __init__ y build
    hub_ui = HubUI(glosa_open=False)
    assert hasattr(hub_ui, "__init__")
    assert hasattr(hub_ui, "build")
    assert hasattr(hub_ui, "_apply_featured")

    # Verificar funciones de modelo conservadas
    assert callable(initial_selection)
    assert callable(hub_pillars)
    assert callable(matrix_cells)
    assert matrix_cells(3) == (
        ("1", "0", "0"),
        ("0", "1", "0"),
        ("0", "0", "1"),
    )
