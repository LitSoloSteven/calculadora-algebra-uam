"""Tests para la fase H4: Carrusel centrado, botones fuera del viewport, cabecera centrada y centrado vertical."""
from pathlib import Path
import re
import pytest

THEME_CSS_PATH = Path("src/frontend/assets/css/theme.css")
HUB_JS_PATH = Path("src/frontend/assets/js/hub.js")


def get_hub_css_block() -> str:
    """Extrae el tramo CSS correspondiente al Hub desde theme.css."""
    content = THEME_CSS_PATH.read_text(encoding="utf-8")
    match = re.search(r'/\* === HUB: Carrusel de Áreas === \*/(.*?)(?=/\* === F4: Glosa === \*/)', content, re.DOTALL)
    assert match is not None, "Bloque CSS de Hub no encontrado en theme.css"
    return match.group(1)


def test_hub_carousel_grid_and_nav_outside_viewport():
    """Verifica que el carrusel use CSS Grid con columnas para los botones y que estos queden fuera del viewport."""
    hub_css = get_hub_css_block()

    # Base: .hub-carousel con grid de 1 columna y nav oculto
    carousel_match = re.search(r'\.hub-carousel\s*\{([^}]+)\}', hub_css)
    assert carousel_match is not None
    carousel_body = carousel_match.group(1)
    assert "display: grid" in carousel_body
    assert "grid-template-columns: minmax(0, 1fr)" in carousel_body

    nav_match = re.search(r'\.hub-carousel-nav\s*\{([^}]+)\}', hub_css)
    assert nav_match is not None
    assert "display: none" in nav_match.group(1)
    assert "position: absolute" not in nav_match.group(1), ".hub-carousel-nav no debe tener position: absolute"

    # Desde 768px: columnas auto minmax(0, 1fr) auto y nav contents
    media_768_match = re.search(r'@media\s*\(min-width:\s*768px\)\s*\{(.*?)\n\}', hub_css, re.DOTALL)
    assert media_768_match is not None, "@media (min-width: 768px) no encontrado en Hub CSS"
    media_body = media_768_match.group(1)

    assert "grid-template-columns: auto minmax(0, 1fr) auto" in media_body
    assert "display: contents" in media_body
    assert "position: absolute" not in media_body

    # Asignación de grid-column
    assert "grid-column: 2" in media_body  # viewport
    assert "grid-column: 1" in media_body  # prev
    assert "grid-column: 3" in media_body  # next


def test_hub_head_centered_and_theme_button_absolute():
    """Verifica que cabecera, marca y subtítulo estén centrados y que el selector de tema sea absoluto."""
    hub_css = get_hub_css_block()

    head_match = re.search(r'\.hub-head\s*\{([^}]+)\}', hub_css)
    assert head_match is not None
    head_body = head_match.group(1)
    assert "align-items: center" in head_body
    assert "justify-content: center" in head_body
    assert "text-align: center" in head_body
    assert "padding-inline: var(--space-12)" in head_body
    assert "position: relative" in head_body

    brand_match = re.search(r'\.hub-brand\s*\{([^}]+)\}', hub_css)
    assert brand_match is not None
    brand_body = brand_match.group(1)
    assert "justify-content: center" in brand_body
    assert "flex-wrap: wrap" in brand_body

    lead_match = re.search(r'\.hub-lead\s*\{([^}]+)\}', hub_css)
    assert lead_match is not None
    lead_body = lead_match.group(1)
    assert "text-align: center" in lead_body
    assert "max-width: 55ch" in lead_body

    theme_match = re.search(r'\.hub-theme\s*\{([^}]+)\}', hub_css)
    assert theme_match is not None
    theme_body = theme_match.group(1)
    assert "position: absolute" in theme_body
    assert "inset-block-start: 0" in theme_body
    assert "inset-inline-end: 0" in theme_body


def test_hub_root_vertical_centering_and_fab_reserve():
    """Verifica el centrado vertical de .hub-root y la neutralización de reserva del FAB."""
    full_css = THEME_CSS_PATH.read_text(encoding="utf-8")
    hub_css = get_hub_css_block()

    root_match = re.search(r'\.hub-root\s*\{([^}]+)\}', hub_css)
    assert root_match is not None
    root_body = root_match.group(1)
    assert "justify-content: center" in root_body
    assert "display: flex" in root_body
    assert "flex-direction: column" in root_body
    assert "min-height:" in root_body
    assert "dvh" in root_body
    assert "100vh" not in root_body

    # .hub-root::after debe neutralizar la reserva declarada en .view-root::after
    view_after_pos = full_css.find(".view-root::after")
    assert view_after_pos != -1
    hub_after_pos = full_css.find(".hub-root::after", view_after_pos)
    assert hub_after_pos != -1, ".hub-root::after debe declararse DESPUÉS de .view-root::after"

    hub_after_match = re.search(r'\.hub-root::after\s*\{([^}]+)\}', full_css[hub_after_pos:])
    assert hub_after_match is not None
    assert "content: none" in hub_after_match.group(1)


def test_hub_card_sizing_and_scale_focus():
    """Verifica dimensiones clamp/cqi, escala por foco con --hub-scale-rest y --hub-focus sin opacidad."""
    hub_css = get_hub_css_block()

    # --hub-card-w en .hub-carousel
    carousel_match = re.search(r'\.hub-carousel\s*\{([^}]+)\}', hub_css)
    assert carousel_match is not None
    carousel_body = carousel_match.group(1)
    assert "--hub-card-w:" in carousel_body
    assert "clamp(" in carousel_body
    assert "cqi" in carousel_body
    assert "--hub-scale-rest: 0.86" in carousel_body

    # @container (min-width: 944px)
    assert "@container (min-width: 944px)" in hub_css

    # .hub-card-body usa --hub-focus
    body_match = re.search(r'(?m)^\.hub-card-body\s*\{([^}]+)\}', hub_css)
    assert body_match is not None
    card_body = body_match.group(1)
    assert "--hub-focus: 0" in card_body
    assert "--hub-scale-rest" in card_body
    assert "transform: scale(calc(" in card_body
    assert "+ 36px" not in card_body, "El padding compensatorio de 36px para flechas debe ser eliminado"

    # .hub-card.is-active define --hub-focus: 1
    active_body_match = re.search(r'\.hub-card\.is-active\s+\.hub-card-body\s*\{([^}]+)\}', hub_css)
    assert active_body_match is not None
    assert "--hub-focus: 1" in active_body_match.group(1)

    # Ninguna regla directa sobre .hub-card-body define opacity (atenuación eliminada)
    card_body_opacity_rules = re.findall(r'(?m)^[^{}]*\.hub-card-body[^{}]*\{([^}]+)\}', hub_css)
    for rule in card_body_opacity_rules:
        # Excluir pseudo-elementos ::after
        pass
    # Verificar específicamente las reglas de cuerpo
    assert "opacity" not in card_body
    assert "opacity" not in active_body_match.group(1)
    assert not re.search(r'\.hub-card:not\(\.is-active\):hover\s+\.hub-card-body\s*\{[^}]*opacity', hub_css)


def test_hub_js_centering_and_depth_no_parallax():
    """Verifica getCenterGap, centrado en getTargetTranslateX, --hub-focus en applyCardsDepth y ausencia de parallax."""
    js_content = HUB_JS_PATH.read_text(encoding="utf-8")

    # getCenterGap
    assert "function getCenterGap" in js_content
    gap_match = re.search(r'function getCenterGap\s*\([^)]*\)\s*\{(.*?)\}', js_content, re.DOTALL)
    assert gap_match is not None
    gap_body = gap_match.group(1)
    assert "viewport.clientWidth - card.offsetWidth" in gap_body

    # getTargetTranslateX
    target_match = re.search(r'function getTargetTranslateX\s*\([^)]*\)\s*\{(.*?)\}', js_content, re.DOTALL)
    assert target_match is not None
    target_body = target_match.group(1)
    assert "-card.offsetLeft" in target_body or "- card.offsetLeft" in target_body
    assert "getCenterGap" in target_body
    assert "vpWidth / 2" not in target_body

    # applyCardsDepth escribe --hub-focus
    depth_match = re.search(r'function applyCardsDepth\s*\([^)]*\)\s*\{(.*?)(?=function\s+clearCardsDepth)', js_content, re.DOTALL)
    assert depth_match is not None
    depth_body = depth_match.group(1)
    assert "--hub-focus" in depth_body
    assert "body.style.transform" not in depth_body, "applyCardsDepth no debe escribir transform en línea"
    assert "body.style.opacity" not in depth_body, "applyCardsDepth no debe escribir opacity en línea"
    assert "icon.style.transform" not in depth_body, "Parallax de icono debe estar eliminado"

    # clearCardsDepth
    clear_match = re.search(r'function clearCardsDepth\s*\([^)]*\)\s*\{(.*?)(?=function\s+updateCarouselPosition)', js_content, re.DOTALL)
    assert clear_match is not None
    clear_body = clear_match.group(1)
    assert "removeProperty('--hub-focus')" in clear_body or 'removeProperty("--hub-focus")' in clear_body
