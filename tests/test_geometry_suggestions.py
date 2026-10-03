"""Tests for geometry suggestions."""
from src.frontend.suggestions import Signals, candidates


def test_parallel_chip_appears():
    """Chip about parallel lines appears when parallel flag is set and state is no_solution."""
    signals = Signals(tool="visualizador", state="no_solution", flags=frozenset({"parallel"}))
    cands = candidates(signals)
    ids = [c.id for c in cands]
    assert "visualizador.parallel" in ids


def test_parallel_chip_absent_without_flag():
    """Chip about parallel lines does not appear without the flag."""
    signals = Signals(tool="visualizador", state="no_solution", flags=frozenset())
    cands = candidates(signals)
    ids = [c.id for c in cands]
    assert "visualizador.parallel" not in ids


def test_span_chip_appears():
    """Chip about span appears on result state in vectores scene."""
    signals = Signals(tool="visualizador", state="result", flags=frozenset())
    cands = candidates(signals)
    ids = [c.id for c in cands]
    assert "visualizador.span" in ids


def test_span_chip_absent_on_none():
    """Span chip doesn't appear when state is none."""
    signals = Signals(tool="visualizador", state="none", flags=frozenset())
    cands = candidates(signals)
    ids = [c.id for c in cands]
    assert "visualizador.span" not in ids


def test_no_chips_for_other_tools():
    """Visualizador chips don't leak to other tools."""
    signals = Signals(tool="sistemas", state="no_solution", flags=frozenset({"parallel"}))
    cands = candidates(signals)
    ids = [c.id for c in cands]
    assert "visualizador.parallel" not in ids
    assert "visualizador.span" not in ids
