"""Pruebas estáticas de contrato para activos del Dock de Glosa (T6 / F8d-bis).

INFERIDO: Estas pruebas verifican el contrato estático en los archivos de código (JS, Python, CSS),
no el comportamiento en un navegador en vivo.
"""
from pathlib import Path
import re
import pytest


def test_glosa_dock_js_contract():
    """Verifica contratos en glosa_dock.js."""
    js_path = Path("src/frontend/assets/js/glosa_dock.js")
    assert js_path.exists()
    content = js_path.read_text(encoding="utf-8")

    # Contiene html.hasAttribute('data-glosa-instant') en el cálculo de instant
    assert "html.hasAttribute('data-glosa-instant')" in content
    instant_match = re.search(r"const instant\s*=\s*([^;]+);", content)
    assert instant_match is not None
    assert "html.hasAttribute('data-glosa-instant')" in instant_match.group(1)

    # No contiene documentElement.style.setProperty('--glosa-kb'
    assert "documentElement.style.setProperty('--glosa-kb'" not in content

    # Contiene reset a '0px' sobre el dock
    assert "dock.style.setProperty('--glosa-kb', '0px')" in content


def test_glosa_dock_py_contract():
    """Verifica contratos de accesibilidad en glosa_dock.py."""
    py_path = Path("src/frontend/components/glosa_dock.py")
    assert py_path.exists()
    content = py_path.read_text(encoding="utf-8")

    # El FAB incluye aria-controls="glosa-dock" y aria-expanded="false"
    fab_match = re.search(r"classes\(['\"]glosa-fab['\"]\)\.props\(([^)]+)\)", content)
    assert fab_match is not None
    fab_props = fab_match.group(1)
    assert 'aria-controls="glosa-dock"' in fab_props
    assert 'aria-expanded="false"' in fab_props

    # El <aside> no incluye aria-expanded
    aside_match = re.search(r"ui\.element\(['\"]aside['\"]\)[^;]+?props\(([^)]+)\)", content)
    assert aside_match is not None
    aside_props = aside_match.group(1)
    assert "aria-expanded" not in aside_props


def test_theme_css_dock_and_layout_contract():
    """Verifica contratos en theme.css sobre FAB, transiciones del dock y tokens de layout."""
    css_path = Path("src/frontend/assets/css/theme.css")
    assert css_path.exists()
    content = css_path.read_text(encoding="utf-8")

    # html[data-glosa="open"] .glosa-fab incluye visibility: hidden
    assert 'html[data-glosa="open"] .glosa-fab' in content
    fab_open_css = content.split('html[data-glosa="open"] .glosa-fab')[1].split("}")[0]
    assert "visibility: hidden" in fab_open_css

    # Transiciones de cierre del dock (push >=1024px, overlay 768-1023px y sheet <=767px)
    # Cada una debe incluir transform 200ms y visibility 0s linear 200ms
    assert content.count("transform 200ms") >= 3
    assert content.count("visibility 0s linear 200ms") >= 3

    # Layout tokens
    assert "100vh" not in content
    assert content.count("container-type: inline-size") == 2
    assert content.count("--fab-reserve:") >= 4
