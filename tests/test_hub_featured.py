"""pick_featured: eleccion pura del punto focal del Hub."""
import dataclasses

import pytest

from src.frontend.views.hub import _recent
from src.frontend.views.hub._recent import pick_featured


def test_valid_history_picks_first_id():
    tool, has_history = pick_featured(["inversa", "romanos"])
    assert tool.id == "inversa"
    assert has_history is True


def test_empty_list_falls_back_to_sistemas():
    tool, has_history = pick_featured([])
    assert tool.id == "sistemas"
    assert has_history is False


@pytest.mark.parametrize("raw", [None, "inversa", 42, {"a": 1}, (), 3.5])
def test_non_list_values_fall_back(raw):
    tool, has_history = pick_featured(raw)
    assert tool.id == "sistemas"
    assert has_history is False


def test_unknown_ids_fall_back():
    tool, has_history = pick_featured(["zzz", "nope"])
    assert tool.id == "sistemas"
    assert has_history is False


def test_invalid_entries_are_skipped():
    tool, has_history = pick_featured([1, None, "zzz", ["x"], "romanos"])
    assert tool.id == "romanos"
    assert has_history is True


def test_duplicates_collapse_to_first():
    tool, has_history = pick_featured(["bases", "bases", "bases"])
    assert tool.id == "bases"
    assert has_history is True


def test_disabled_tool_is_skipped(monkeypatch):
    real = _recent.tool_by_id

    def fake(tool_id):
        tool = real(tool_id)
        if tool_id == "inversa":
            return dataclasses.replace(tool, enabled=False)
        return tool

    monkeypatch.setattr(_recent, "tool_by_id", fake)
    tool, has_history = pick_featured(["inversa", "vectores"])
    assert tool.id == "vectores"
    assert has_history is True


def test_never_raises_on_garbage():
    for raw in ([object()], [[]], [{}], ["", " "], [True, False]):
        tool, has_history = pick_featured(raw)
        assert tool.id == "sistemas"
        assert has_history is False
