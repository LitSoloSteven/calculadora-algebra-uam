"""Tests for geometry figures (_scenes.py)."""
import pytest

plotly = pytest.importorskip("plotly")


def test_build_lines_planes_2d():
    from src.frontend.views.geometry._scenes import build_lines_planes_figure
    result = {
        "n": 2,
        "equations": [
            {"index": 0, "kind": "line", "coeffs": [1.0, 1.0], "coeffs_exact": ["1", "1"], "b": 3.0, "b_exact": "3"},
            {"index": 1, "kind": "line", "coeffs": [1.0, -1.0], "coeffs_exact": ["1", "-1"], "b": 1.0, "b_exact": "1"},
        ],
        "set": {"kind": "POINT", "dimension": 0, "point": [2.0, 1.0], "point_exact": ["2", "1"]},
        "range": [-5.0, 5.0],
    }
    fig = build_lines_planes_figure(result)
    # Should produce valid JSON
    fig.to_json()


def test_build_lines_planes_3d():
    from src.frontend.views.geometry._scenes import build_lines_planes_figure
    result = {
        "n": 3,
        "equations": [
            {"index": 0, "kind": "plane", "coeffs": [1.0, 0.0, 0.0], "coeffs_exact": ["1", "0", "0"], "b": 1.0, "b_exact": "1"},
        ],
        "set": None,
        "range": [-5.0, 5.0],
    }
    fig = build_lines_planes_figure(result)
    fig.to_json()


def test_build_vectors_figure():
    from src.frontend.views.geometry._scenes import build_vectors_figure
    result = {
        "n": 2,
        "static": {"u": [1.0, 0.0], "v": [0.0, 1.0], "u_plus_v": [1.0, 1.0]},
        "frames": [{"k": 0.0, "k_exact": "0", "ku": [0.0, 0.0], "ku_plus_v": [0.0, 1.0]}],
        "range": [-5.0, 5.0],
    }
    fig = build_vectors_figure(result)
    fig.to_json()


def test_build_combination_figure():
    from src.frontend.views.geometry._scenes import build_combination_figure
    result = {
        "n": 2,
        "b": {"float": [3.0, 3.0], "exact": ["3", "3"]},
        "vectors": [{"float": [1.0, 0.0], "exact": ["1", "0"]}, {"float": [0.0, 1.0], "exact": ["0", "1"]}],
        "chain": [
            {"float": [3.0, 0.0], "exact": ["3", "0"], "label": "c_1·v_1"},
            {"float": [3.0, 3.0], "exact": ["3", "3"], "label": "+ c_2·v_2"},
        ],
        "b_outside_span": False,
        "range": [-5.0, 5.0],
    }
    fig = build_combination_figure(result)
    fig.to_json()


def test_figures_have_fixed_ranges():
    from src.frontend.views.geometry._scenes import build_lines_planes_figure
    result = {
        "n": 2,
        "equations": [
            {"index": 0, "kind": "line", "coeffs": [1.0, 0.0], "coeffs_exact": ["1", "0"], "b": 10.0, "b_exact": "10"},
        ],
        "set": None,
        "range": [-20.0, 20.0],
    }
    fig = build_lines_planes_figure(result)
    layout = fig.layout
    assert list(layout.xaxis.range) == [-20.0, 20.0]
    assert list(layout.yaxis.range) == [-20.0, 20.0]


def test_no_frames_dependency():
    """Figures don't rely on fig.frames."""
    from src.frontend.views.geometry._scenes import build_vectors_figure
    result = {
        "n": 2,
        "static": {"u": [1.0, 0.0], "v": [0.0, 1.0], "u_plus_v": [1.0, 1.0]},
        "frames": [],
        "range": [-5.0, 5.0],
    }
    fig = build_vectors_figure(result)
    assert not fig.frames  # No plotly frames used
