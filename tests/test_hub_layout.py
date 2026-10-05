"""Geometria de la escalera del Hub y contratos estaticos de la fase H1."""
import re
from pathlib import Path

import pytest

from src.frontend.navigation import nav_groups
from src.frontend.views.hub import _layout
from src.frontend.views.hub._layout import (
    BOARD_COLUMNS,
    board_classes,
    board_fits,
    step_class,
    step_offset,
    step_span,
)

CSS_PATH = Path("src/frontend/assets/css/theme.css")
VIEW_PATH = Path("src/frontend/views/hub/view_hub.py")


def test_board_has_four_columns():
    assert BOARD_COLUMNS == 4


@pytest.mark.parametrize(
    "index,offset,span",
    [(0, 0, 4), (1, 1, 3), (2, 2, 2), (3, 3, 1), (4, 3, 1), (9, 3, 1)],
)
def test_offset_and_span(index, offset, span):
    assert step_offset(index) == offset
    assert step_span(index) == span
    assert step_offset(index) + step_span(index) == BOARD_COLUMNS


def test_negative_index_is_rejected():
    with pytest.raises(ValueError):
        step_offset(-1)


def test_board_fits_synthetic_cases():
    assert board_fits([4, 3, 2, 1]) is True
    assert board_fits([4, 1, 2]) is True
    assert board_fits([5]) is False
    assert board_fits([4, 4]) is False


def test_real_catalog_closes_the_staircase():
    counts = [len(tools) for _, tools in nav_groups()]
    assert board_fits(counts), (
        f"El catalogo {counts} ya no cabe en la escalera de {BOARD_COLUMNS} columnas: "
        "revisa HUB_STAIRCASE o el layout del Hub."
    )


def test_step_class_names():
    assert step_class(0) == "hub-step hub-step-0"
    assert step_class(2) == "hub-step hub-step-2"
    assert step_class(7) == "hub-step hub-step-3"


def test_board_classes_modifiers(monkeypatch):
    assert board_classes() == "hub-board"
    monkeypatch.setattr(_layout, "HUB_STAIRCASE", False)
    assert board_classes() == "hub-board hub-board-flat"
    monkeypatch.setattr(_layout, "HUB_BRACKETS", False)
    assert board_classes() == "hub-board hub-board-flat hub-board-bare"


def test_css_old_hub_selectors_are_gone():
    css = CSS_PATH.read_text(encoding="utf-8")
    for old in (
        r"\.hub-section-title",
        r"\.hub-cols",
        r"\.hub-col\b",
        r"\.hub-pillar",
        r"\.hub-row",
        r"\.hub-recent",
        r"\.hub-empty",
    ):
        assert re.search(old, css) is None, f"Selector viejo aun presente: {old}"


def test_css_new_hub_contract():
    css = CSS_PATH.read_text(encoding="utf-8")
    for needed in (
        ".hub-head",
        ".hub-title",
        ".hub-lead",
        ".hub-board",
        ".hub-step-list",
        ".hub-tile",
        ".hub-tile-mark",
        ".hub-tile.is-featured::before",
        ".hub-tile:focus-visible",
        "@container (min-width: 860px)",
        "@container (min-width: 480px)",
    ):
        assert needed in css, f"Falta en theme.css: {needed}"
    assert ".hub-root { container-type: inline-size; }" in css


def test_view_source_contract():
    src = VIEW_PATH.read_text(encoding="utf-8")
    assert "view-root" in src
    assert "typesetMathWhenReady" not in src
    assert "Continuar" not in src
    assert "ui.skeleton" not in src
    assert "example_latex" not in src
    for needed in ("h1", "h2", "hub-tile", "hub-step-list", "aria-label"):
        assert needed in src
