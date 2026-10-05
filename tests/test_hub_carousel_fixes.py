"""Tests de verificacion para las correcciones del Carrusel del Hub (Tarea H2).

Verifica:
1. Todo var(--x) de theme.css sin fallback está definido.
2. El bloque reduced-motion no pone transform: none sobre .hub-track.
3. En hub.js, setPointerCapture aparece dentro del manejador de pointermove y no en el de pointerdown.
4. Todo .focus( lleva preventScroll.
5. .hub-viewport declara overflow: clip.
6. Existe la regla .hub-carousel.is-dragging .hub-card-body con transition: none.
7. Ninguna transition de .hub-* incluye box-shadow, width, height, margin ni padding.
8. view_hub.py define id="hub-track".
"""
from pathlib import Path
import re
import pytest

THEME_CSS_PATH = Path("src/frontend/assets/css/theme.css")
HUB_JS_PATH = Path("src/frontend/assets/js/hub.js")
VIEW_HUB_PATH = Path("src/frontend/views/hub/view_hub.py")


def get_hub_css_block() -> str:
    """Extrae el bloque CSS correspondiente al Hub desde theme.css."""
    content = THEME_CSS_PATH.read_text(encoding="utf-8")
    match = re.search(r'/\* === HUB: Carrusel de Áreas === \*/(.*?)(?=/\* === F4: Glosa === \*/)', content, re.DOTALL)
    assert match is not None, "Bloque CSS de Hub no encontrado en theme.css"
    return match.group(1)


def test_theme_css_tokens_without_fallback_defined():
    """1. Verifica que todo var(--x) de theme.css sin fallback este definido en :root o data-theme."""
    content = THEME_CSS_PATH.read_text(encoding="utf-8")
    clean_css = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    # Tokens definidos (--nombre:)
    defined_tokens = set(re.findall(r'(--[a-zA-Z0-9_-]+)\s*:', clean_css))

    # Usos var(--token) sin fallback
    var_calls = re.findall(r'var\(\s*(--[a-zA-Z0-9_-]+)(?:\s*,\s*([^)]+))?\)', clean_css)

    undefined_no_fallback = []
    for token, fallback in var_calls:
        if not fallback or not fallback.strip():
            if token not in defined_tokens:
                undefined_no_fallback.append(token)

    assert undefined_no_fallback == [], f"Tokens usados sin fallback y no definidos: {undefined_no_fallback}"


def test_reduced_motion_preserves_track_transform():
    """2. Verifica que el bloque reduced-motion no ponga transform: none sobre .hub-track."""
    content = THEME_CSS_PATH.read_text(encoding="utf-8")

    # Extraer bloques @media (prefers-reduced-motion: reduce) balanceando llaves
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

    hub_reduced_block = None
    for b in blocks:
        if ".hub-card" in b or ".hub-track" in b:
            hub_reduced_block = b
            break

    assert hub_reduced_block is not None, "Bloque reduced-motion del Hub no encontrado"

    # Buscar reglas que asignen transform: none
    rules = re.findall(r'([^{}]+)\{\s*([^}]*transform\s*:\s*none[^}]*)\}', hub_reduced_block, re.DOTALL)
    for selectors, body in rules:
        sel_list = [s.strip() for s in selectors.split(',')]
        assert ".hub-track" not in sel_list, (
            f".hub-track encontrado en regla de transform: none: {selectors}"
        )

    # Verificar que .hub-track si tenga transition: none
    trans_rules = re.findall(r'([^{}]+)\{\s*([^}]*transition\s*:\s*none[^}]*)\}', hub_reduced_block, re.DOTALL)
    track_has_no_trans = any(".hub-track" in [s.strip() for s in sel.split(',')] for sel, _ in trans_rules)
    assert track_has_no_trans, ".hub-track debe tener transition: none en reduced-motion"

    # Selectores obsoletos no deben figurar
    assert ".hub-row" not in hub_reduced_block, ".hub-row obsoleto encontrado en bloque reduced-motion"


def test_hub_js_pointer_capture_in_pointermove_not_down():
    """3. En hub.js, setPointerCapture aparece dentro del manejador de pointermove y no en el de pointerdown."""
    js_content = HUB_JS_PATH.read_text(encoding="utf-8")

    # Extraer funcion onPointerDown
    down_match = re.search(r'function onPointerDown\s*\([^)]*\)\s*\{(.*?)(?=function\s+onPointerMove)', js_content, re.DOTALL)
    assert down_match is not None, "Funcion onPointerDown no encontrada"
    down_body = down_match.group(1)
    assert "setPointerCapture" not in down_body, "setPointerCapture no debe ejecutarse en onPointerDown"

    # Extraer funcion onPointerMove
    move_match = re.search(r'function onPointerMove\s*\([^)]*\)\s*\{(.*?)(?=function\s+onPointerUp)', js_content, re.DOTALL)
    assert move_match is not None, "Funcion onPointerMove no encontrada"
    move_body = move_match.group(1)
    assert "setPointerCapture" in move_body, "setPointerCapture debe ejecutarse en onPointerMove al iniciar arrastre"


def test_hub_js_all_focus_calls_prevent_scroll():
    """4. Verifica que todo .focus( en hub.js lleve preventScroll: true."""
    js_content = HUB_JS_PATH.read_text(encoding="utf-8")

    # Encontrar todas las llamadas .focus(...)
    focus_calls = re.findall(r'\.focus\((.*?)\)', js_content)
    assert len(focus_calls) > 0, "No se encontraron llamadas a .focus() en hub.js"

    for arg in focus_calls:
        assert "preventScroll" in arg and "true" in arg, (
            f"Llamada a .focus({arg}) no incluye preventScroll: true"
        )


def test_hub_viewport_declares_overflow_clip():
    """5. .hub-viewport declara overflow: clip con fallback overflow: hidden."""
    hub_css = get_hub_css_block()

    vp_match = re.search(r'\.hub-viewport\s*\{([^}]+)\}', hub_css)
    assert vp_match is not None, "Regla .hub-viewport no encontrada"
    vp_body = vp_match.group(1)

    assert "overflow: clip;" in vp_body or "overflow: clip" in vp_body
    assert "overflow: hidden;" in vp_body or "overflow: hidden" in vp_body
    assert "padding-block: var(--space-6);" in vp_body or "padding-block: var(--space-6)" in vp_body
    assert "touch-action: pan-y;" in vp_body or "touch-action: pan-y" in vp_body


def test_hub_carousel_is_dragging_transition_none():
    """6. Existe la regla .hub-carousel.is-dragging .hub-card-body con transition: none."""
    hub_css = get_hub_css_block()

    dragging_match = re.search(
        r'\.hub-carousel\.is-dragging\s+\.hub-card-body\s*\{([^}]+)\}',
        hub_css,
    )
    assert dragging_match is not None, "Regla .hub-carousel.is-dragging .hub-card-body no encontrada"
    assert "transition: none" in dragging_match.group(1), "Debe declarar transition: none"


def test_hub_transitions_no_forbidden_properties():
    """7. Ninguna transition de .hub-* incluye box-shadow, width, height, margin ni padding."""
    hub_css = get_hub_css_block()
    forbidden = ["box-shadow", "width", "height", "margin", "padding", "left", "top", "right", "bottom"]

    transitions = re.findall(r'transition:\s*([^;]+);', hub_css)
    assert len(transitions) > 0, "No se encontraron propiedades transition en .hub-*"

    for trans in transitions:
        for prop in forbidden:
            pattern = rf'(?:^|[\s,]){prop}(?:-[a-z]+)?(?:[\s,]|$)'
            assert not re.search(pattern, trans), f"Propiedad prohibida '{prop}' en transition: {trans}"


def test_view_hub_defines_track_id():
    """8. view_hub.py define id="hub-track" en la pista."""
    view_content = VIEW_HUB_PATH.read_text(encoding="utf-8")
    assert 'id="hub-track"' in view_content
    # Tambien verificar que title este presente en titulo y blurb
    assert 'title=pillar.short_name' in view_content
    assert 'title=pillar.blurb' in view_content
    assert "matrix_cells" not in view_content
