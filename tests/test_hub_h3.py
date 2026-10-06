"""Tests para la fase H3: Correcciones de hover y tamaño del carrusel del Hub y ocultación de Glosa."""
from pathlib import Path
import re
import pytest

THEME_CSS_PATH = Path("src/frontend/assets/css/theme.css")
HUB_JS_PATH = Path("src/frontend/assets/js/hub.js")
VIEW_HUB_PATH = Path("src/frontend/views/hub/view_hub.py")
VIEWS_DIR = Path("src/frontend/views")


def get_hub_css_block() -> str:
    """Extrae el bloque CSS correspondiente al Hub desde theme.css."""
    content = THEME_CSS_PATH.read_text(encoding="utf-8")
    match = re.search(r'/\* === HUB: Carrusel de Áreas === \*/(.*?)(?=/\* === F4: Glosa === \*/)', content, re.DOTALL)
    assert match is not None, "Bloque CSS de Hub no encontrado en theme.css"
    return match.group(1)


def test_hub_js_no_hover_involuntary_movement():
    """Verifica que pointermove/hover en hub.js esté protegido con isPointerDown."""
    content = HUB_JS_PATH.read_text(encoding="utf-8")

    # onPointerMove debe verificar isPointerDown antes de alterar transform/posicion
    move_match = re.search(r'function onPointerMove\s*\([^)]*\)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', content)
    assert move_match is not None, "onPointerMove no encontrada en hub.js"
    move_body = move_match.group(1)

    assert "isPointerDown" in move_body, "onPointerMove debe consultar isPointerDown"
    assert "!isPointerDown" in move_body, "onPointerMove debe retornar temprano si !isPointerDown"

    # No debe haber listeners de hover que llamen a scrollBy/scrollTo/scrollIntoView/select
    for hover_event in ['pointerenter', 'pointerover', 'mouseenter', 'mouseover']:
        assert f"addEventListener('{hover_event}'" not in content
        assert f'addEventListener("{hover_event}"' not in content

    # Ninguna llamada a scrollBy o scrollTo en hub.js
    assert "scrollBy" not in content
    assert "scrollTo" not in content
    assert "scrollLeft" not in content


def test_hub_carousel_alignment_and_sizing():
    """Verifica que el carrusel se alinee al inicio y que las tarjetas tengan mayor escala."""
    hub_css = get_hub_css_block()
    js_content = HUB_JS_PATH.read_text(encoding="utf-8")

    # .hub-track debe tener padding-inline: 0 (o no centrar con 50% - card_w / 2)
    track_match = re.search(r'\.hub-track\s*\{([^}]+)\}', hub_css)
    assert track_match is not None
    track_body = track_match.group(1)
    assert "calc(50% - var(--hub-card-w) / 2)" not in track_body, "El track ya no debe usar padding-inline centrado"

    # getTargetTranslateX en hub.js debe alinear la tarjeta al inicio (-card.offsetLeft)
    get_target_match = re.search(r'function getTargetTranslateX\s*\([^)]*\)\s*\{(.*?)\}', js_content, re.DOTALL)
    assert get_target_match is not None
    target_body = get_target_match.group(1)
    assert "vpWidth / 2" not in target_body, "getTargetTranslateX no debe centrar en la mitad del viewport"
    assert "card.offsetLeft" in target_body
    assert "-card.offsetLeft" in target_body or "- card.offsetLeft" in target_body

    # Tarjetas más grandes: min-height con clamp() y dvh en .hub-card-body
    body_match = re.search(r'(?m)^\.hub-card-body\s*\{([^}]+)\}', hub_css)
    assert body_match is not None
    card_body = body_match.group(1)
    assert "min-height:" in card_body
    assert "clamp(" in card_body
    assert "dvh" in card_body
    assert "100vh" not in card_body

    # Escala tipográfica mayor con clamp()
    title_match = re.search(r'\.hub-card-title\s*\{([^}]+)\}', hub_css)
    assert title_match is not None
    assert "clamp(" in title_match.group(1)

    blurb_match = re.search(r'\.hub-card-blurb\s*\{([^}]+)\}', hub_css)
    assert blurb_match is not None
    assert "-webkit-line-clamp: 2" in blurb_match.group(1)

    # Icono más grande
    icon_match = re.search(r'\.hub-card-icon\s*\{([^}]+)\}', hub_css)
    assert icon_match is not None
    assert "clamp(" in icon_match.group(1)


def test_hub_css_no_100vh_and_no_literal_colors():
    """Verifica que en .hub-* no haya 100vh ni colores literales (hex, rgb, hsl)."""
    hub_css = get_hub_css_block()

    assert "100vh" not in hub_css, "No se permite 100vh en el Hub; usa 100dvh o dvh"

    # Comprobar que no haya colores literales fuera de comentarios
    clean_css = re.sub(r'/\*.*?\*/', '', hub_css, flags=re.DOTALL)
    # Hex: #fff, #123456, etc.
    hex_matches = re.findall(r'#[0-9a-fA-F]{3,8}\b', clean_css)
    assert hex_matches == [], f"Colores hex literales encontrados en .hub-*: {hex_matches}"

    # rgb / hsl
    fn_matches = re.findall(r'\b(?:rgb|rgba|hsl|hsla)\([^)]+\)', clean_css)
    assert fn_matches == [], f"Funciones de color literales encontradas en .hub-*: {fn_matches}"


def test_hub_hover_media_query_and_reduced_motion():
    """Verifica que todo :hover esté bajo @media (hover: hover) and (pointer: fine) y que reduced-motion cubra lo nuevo."""
    hub_css = get_hub_css_block()
    css_full = THEME_CSS_PATH.read_text(encoding="utf-8")

    # Extraer todas las reglas :hover dentro del Hub
    hover_matches = [m.start() for m in re.finditer(r':hover', hub_css)]
    for pos in hover_matches:
        preceding = hub_css[:pos]
        media_pos = preceding.rfind('@media (hover: hover) and (pointer: fine)')
        assert media_pos != -1, f":hover encontrado fuera de @media (hover: hover) and (pointer: fine) en el Hub: pos {pos}"

    # Reduced motion debe cubrir .hub-card-body, .hub-card, .hub-track, .hub-tile, .hub-nav-btn
    assert "@media (prefers-reduced-motion: reduce)" in css_full
    red_match = re.search(r'@media \(prefers-reduced-motion:\s*reduce\)\s*\{(.*?)(?=\n/\* === F4: Glosa)', css_full, re.DOTALL)
    assert red_match is not None
    red_body = red_match.group(1)
    for sel in ['.hub-card', '.hub-card-body', '.hub-track', '.hub-tile', '.hub-nav-btn']:
        assert sel in red_body, f"Selector {sel} debe estar cubierto en prefers-reduced-motion"


def test_glosa_hidden_in_hub_only():
    """Verifica que Glosa se oculte únicamente en el Hub mediante la clase semántica .hub-page."""
    css_content = THEME_CSS_PATH.read_text(encoding="utf-8")
    view_hub_content = VIEW_HUB_PATH.read_text(encoding="utf-8")

    # 1. Regla en theme.css
    assert ".hub-page .glosa-fab" in css_content
    fab_rule = re.search(r'\.hub-page\s+\.glosa-fab\s*\{([^}]+)\}', css_content)
    assert fab_rule is not None, "Regla .hub-page .glosa-fab no encontrada en theme.css"
    assert "display: none" in fab_rule.group(1)

    # 2. view_hub.py debe marcar .hub-page en body
    assert "hub-page" in view_hub_content

    # 3. Ninguna otra vista debe aplicar .hub-page
    for py_file in VIEWS_DIR.rglob("view_*.py"):
        if py_file.name == "view_hub.py":
            continue
        code = py_file.read_text(encoding="utf-8")
        assert "hub-page" not in code, f"La vista {py_file} no debe contener 'hub-page'"

    # 4. En el Hub, self.ai_panel no se abre automáticamente
    assert "self.ai_panel.open()" not in view_hub_content


def test_break_ui_pillars_and_long_text():
    """Pruebas de Break-UI: títulos largos, estado vacío y robustez con 1 o más pilares."""
    hub_css = get_hub_css_block()
    view_content = VIEW_HUB_PATH.read_text(encoding="utf-8")

    # Textos largos no se desbordan (min-width: 0, overflow-wrap: anywhere o text-overflow: ellipsis)
    assert "overflow-wrap: anywhere" in hub_css
    assert "text-overflow: ellipsis" in hub_css
    assert "min-width: 0" in hub_css

    # Flechas flex-shrink: 0
    btn_match = re.search(r'\.hub-nav-btn\s*\{([^}]+)\}', hub_css)
    assert btn_match is not None
    assert "flex-shrink: 0" in btn_match.group(1)

    # Estado vacio
    assert ".hub-empty-area" in hub_css
    assert "Esta área aún no tiene herramientas." in view_content


def test_tokens_used_are_valid():
    """Verifica que todos los tokens usados en .hub-* pertenezcan al sistema semántico de Scalaris."""
    hub_css = get_hub_css_block()
    used_tokens = set(re.findall(r'var\(\s*(--[a-zA-Z0-9_-]+)', hub_css))

    css_full = THEME_CSS_PATH.read_text(encoding="utf-8")
    clean_css = re.sub(r'/\*.*?\*/', '', css_full, flags=re.DOTALL)
    defined_tokens = set(re.findall(r'(--[a-zA-Z0-9_-]+)\s*:', clean_css))

    for token in used_tokens:
        assert token in defined_tokens, f"Token no definido usado en Hub CSS: {token}"

