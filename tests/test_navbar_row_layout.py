"""Tests para verificar el layout en una sola fila, CSS semantico, container queries,
movimiento y tokens de la barra de navegacion contextual (Paso 2.8)."""
from pathlib import Path
import re
import pytest

CSS_PATH = Path("src/frontend/assets/css/theme.css")


def get_nav_css_block() -> str:
    content = CSS_PATH.read_text(encoding="utf-8")
    # Extraer el bloque que va desde .nav-header hasta .hub-root
    match = re.search(r'(\.nav-header\s*\{.*?)\.hub-root', content, re.DOTALL)
    assert match, "No se encontro el bloque .nav-* en theme.css"
    return match.group(1)


def test_navbar_grid_one_row():
    """Verifica que .nav-pill este configurado como grid de una sola fila y .nav-header centrado."""
    css = get_nav_css_block()

    # .nav-header centrado, flex, fondo transparente, color con token
    assert ".nav-header" in css
    header_block = re.search(r'\.nav-header\s*\{(.*?)\}', css, re.DOTALL).group(1)
    assert "display: flex;" in header_block
    assert "align-items: center;" in header_block
    assert "justify-content: center;" in header_block
    assert "background: transparent" in header_block or "background-color: transparent" in header_block
    assert "color: var(--text-main)" in header_block

    # Altura en rango 64 a 72 px
    assert re.search(r'height:\s*(?:6[4-9]|7[0-2])px', header_block) or re.search(r'min-height:\s*(?:6[4-9]|7[0-2])px', header_block)

    # .nav-pill como grid auto | minmax(0,1fr) | auto
    pill_block = re.search(r'\.nav-pill\s*\{(.*?)\}', css, re.DOTALL).group(1)
    assert "display: grid;" in pill_block
    assert "grid-template-columns: auto minmax(0, 1fr) auto;" in pill_block or "grid-template-columns: auto minmax(0,1fr) auto;" in pill_block
    assert "grid-template-rows: 1fr;" in pill_block

    # Altura en rango 64 a 72 px
    assert re.search(r'height:\s*(?:6[4-9]|7[0-2])px', pill_block) or re.search(r'min-height:\s*(?:6[4-9]|7[0-2])px', pill_block)


def test_navbar_central_zone_min_width_and_overflow():
    """Verifica min-width: 0, overflow-x: auto, scrollbar oculta y mask-image en la zona central."""
    css = get_nav_css_block()

    assert ".nav-center" in css
    center_block = re.search(r'\.nav-center\s*\{(.*?)\}', css, re.DOTALL).group(1)
    assert "min-width: 0;" in center_block
    assert "overflow-x: auto;" in center_block
    assert "scrollbar-width: none;" in center_block
    assert "mask-image:" in center_block

    # Scrollbar webkit oculta
    assert ".nav-center::-webkit-scrollbar" in css
    webkit_scrollbar_block = re.search(r'\.nav-center::-webkit-scrollbar\s*\{(.*?)\}', css, re.DOTALL).group(1)
    assert "display: none;" in webkit_scrollbar_block


def test_navbar_flex_shrink_home_and_theme():
    """Verifica que el icono de inicio y el selector de tema tengan flex-shrink: 0."""
    css = get_nav_css_block()

    shrink_match = re.search(r'([^\{\}]*nav-home[^\{\}]*)\{(.*?)\}', css, re.DOTALL)
    assert shrink_match, "No se encontro regla para .nav-home"
    assert "flex-shrink: 0;" in shrink_match.group(2)
    # Verifica que tema este en el mismo selector o con flex-shrink: 0
    assert "theme-switcher-btn" in shrink_match.group(1) or "nav-theme" in shrink_match.group(1)


def test_navbar_single_label_visible():
    """Verifica que nunca esten visibles la etiqueta completa y corta a la vez."""
    css = get_nav_css_block()

    # Por defecto ambas estan ocultas
    full_default = re.search(r'\n\.nav-label-full\s*\{(.*?)\}', css, re.DOTALL).group(1)
    short_default = re.search(r'\n\.nav-label-short\s*\{(.*?)\}', css, re.DOTALL).group(1)
    assert "display: none;" in full_default
    assert "display: none;" in short_default

    # En 700px: corta visible, completa oculta
    mq_700 = re.search(r'@container\s+navbar\s*\(\s*min-width:\s*700px\s*\)\s*\{(.*?)\n\}', css, re.DOTALL).group(1)
    assert ".nav-label-short" in mq_700
    assert "display: inline;" in mq_700
    assert ".nav-label-full" in mq_700
    assert "display: none;" in mq_700

    # En 960px: completa visible, corta oculta
    mq_960 = re.search(r'@container\s+navbar\s*\(\s*min-width:\s*960px\s*\)\s*\{(.*?)\n\}', css, re.DOTALL).group(1)
    assert ".nav-label-full" in mq_960
    assert "display: inline;" in mq_960
    assert ".nav-label-short" in mq_960
    assert "display: none;" in mq_960


def test_navbar_no_literal_colors():
    """Verifica que el bloque de reglas .nav-* no contenga colores hexadecimales o rgb literales."""
    css = get_nav_css_block()

    # Buscar literales #fff, #123456, etc.
    hex_literals = re.findall(r'#[0-9a-fA-F]{3,8}\b', css)
    assert hex_literals == [], f"Se encontraron colores hexadecimales literales en .nav-*: {hex_literals}"

    # Buscar rgb/rgba literales que no usen var()
    rgb_matches = re.findall(r'rgba?\([^\)]*\)', css)
    for rgb in rgb_matches:
        assert "var(" in rgb, f"Color rgb literal sin token en .nav-*: {rgb}"


def test_navbar_reduced_motion_and_no_ease_in():
    """Verifica que no haya transiciones con ease-in y que reduced-motion anule transformaciones."""
    css = get_nav_css_block()

    # Prohibido ease-in
    assert not re.search(r'transition:[^;]*\bease-in\b', css)

    # Bloque de reduced-motion para navbar
    assert "@media (prefers-reduced-motion: reduce)" in css
    rm_match = re.search(r'@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{(.*?)\n\}', css, re.DOTALL)
    assert rm_match, "No se encontro bloque prefers-reduced-motion en .nav-*"
    rm_css = rm_match.group(1)
    assert "transform: none !important;" in rm_css
    assert "transition: none !important;" in rm_css
    assert ".nav-trigger" in rm_css
    assert ".nav-pill" in rm_css
