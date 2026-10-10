"""Contratos estáticos de escala para el Hub de Scalaris (H9)."""
from decimal import Decimal
from pathlib import Path
import re


THEME_CSS_PATH = Path("src/frontend/assets/css/theme.css")
VIEW_HUB_PATH = Path("src/frontend/views/hub/view_hub.py")


def hub_css_block() -> str:
    content = THEME_CSS_PATH.read_text(encoding="utf-8")
    start = content.index("/* === HUB: Matriz de áreas y popovers === */")
    end = content.index("/* === F4: Glosa === */", start)
    return content[start:end]


def rule_body(css: str, selector: str) -> str:
    match = re.search(
        rf"(?m)^{re.escape(selector)}\s*\{{([^{{}}]*)\}}",
        css,
    )
    assert match is not None, f"No se encontró la regla {selector}"
    return match.group(1)


def clamp_min_rem(css: str, selector: str) -> Decimal:
    body = rule_body(css, selector)
    match = re.search(r"font-size:\s*clamp\(\s*([\d.]+)rem\s*,", body)
    assert match is not None, f"{selector} no declara un font-size clamp en rem"
    return Decimal(match.group(1))


def test_hub_scale_and_static_safety_contract():
    view = VIEW_HUB_PATH.read_text(encoding="utf-8")
    full_css = THEME_CSS_PATH.read_text(encoding="utf-8")
    css = hub_css_block()

    assert "hub-theme" not in view
    assert "render_theme_button" not in view
    assert ".hub-theme" not in full_css
    assert "width: min(100%, 72rem)" in rule_body(css, ".hub-matrix")

    assert clamp_min_rem(css, ".hub-title") >= Decimal("2.5")
    assert clamp_min_rem(css, ".hub-row-title") >= Decimal("1.4")
    assert clamp_min_rem(css, ".hub-row-blurb") >= Decimal("0.9375")

    assert "100vh" not in css
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)
    assert not re.search(r"\b(?:rgb|rgba|hsl|hsla)\s*\(", css)
