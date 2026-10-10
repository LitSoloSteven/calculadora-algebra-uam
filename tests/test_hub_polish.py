"""Guardrails estáticos para el ajuste estrecho del Hub en H8."""
from pathlib import Path

from tests.test_hub_matrix import matching_brace


THEME_CSS_PATH = Path("src/frontend/assets/css/theme.css")


def narrow_hub_block() -> str:
    css = THEME_CSS_PATH.read_text(encoding="utf-8")
    start = css.index("@media (max-width: 359px) {")
    open_index = css.index("{", start)
    return css[start:matching_brace(css, open_index) + 1]


def test_hub_narrow_layout_prevents_tile_and_popover_header_overflow():
    css = narrow_hub_block()

    assert ".hub-pop-head" in css
    assert '"title close"' in css
    assert '"count count"' in css
    assert ".hub-pop-icon" in css
    assert "display: none" in css
    assert ".hub-tile" in css
    assert '"icon name"' in css
    assert '"icon desc"' in css
    assert '"mark mark"' in css
    assert ".hub-tile-mark" in css
    assert "min-width: 0" in css


def test_hub_narrow_row_mark_reserves_two_lines_before_featured_state():
    css = narrow_hub_block()

    assert ".hub-row-mark" in css
    assert "min-height: 2.4em" in css
