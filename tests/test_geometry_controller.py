"""Tests for GeometryController."""
import json
import copy
from fractions import Fraction

from src.frontend.controllers.geometry.controller_geometry import (
    GeometryController,
    auto_range,
    clip_line_to_box,
    error_cell_selector,
)


# ---- auto_range ----

def test_auto_range_symmetric():
    r = auto_range([3.0, -2.0])
    assert r[0] == -r[1]
    assert r[1] >= 3.0


def test_auto_range_minimum():
    r = auto_range([0.5])
    assert r[1] >= 5.0


def test_auto_range_125_scale():
    r = auto_range([7.0])
    # 7 * 1.35 = 9.45 => rounds to 10
    assert r == [-10.0, 10.0]


def test_auto_range_no_finite():
    r = auto_range([float('inf'), float('-inf'), float('nan')])
    assert r == [-5.0, 5.0]


def test_auto_range_empty():
    r = auto_range([])
    assert r == [-5.0, 5.0]


def test_auto_range_none_values():
    r = auto_range([None, 3.0, None])
    assert r[0] == -r[1]

# ---- clip_line_to_box ----

def test_clip_line_to_box_inside():
    # p=(0,0), d=(1,0), half=5 -> t in [-5, 5]
    res = clip_line_to_box([0.0, 0.0], [1.0, 0.0], 5.0)
    assert res is not None
    assert abs(res[0] - (-5.0)) < 1e-6
    assert abs(res[1] - 5.0) < 1e-6

def test_clip_line_to_box_outside():
    # p=(10,0), d=(1,0), half=5 -> outside because y matches but x starts at 10 and we want to see if it crosses... wait, d=(1,0) -> y=0 which is inside.
    # The x bound would be -15 to -5.
    res = clip_line_to_box([10.0, 0.0], [1.0, 0.0], 5.0)
    assert res is not None
    assert abs(res[0] - (-15.0)) < 1e-6
    assert abs(res[1] - (-5.0)) < 1e-6

def test_clip_line_to_box_parallel_outside():
    # p=(0,10), d=(1,0), half=5 -> y is out of bounds
    res = clip_line_to_box([0.0, 10.0], [1.0, 0.0], 5.0)
    assert res is None

def test_clip_line_to_box_zero_dir():
    # p=(0,0), d=(0,0)
    res = clip_line_to_box([0.0, 0.0], [0.0, 0.0], 5.0)
    assert res is None

# ---- error_cell_selector ----

def test_error_cell_selector_A():
    res = error_cell_selector({"kind": "A", "row": 1, "col": 2}, scene="rectas-planos", grid_n=2)
    assert res == 'input[data-row="1"][data-col="2"]'

def test_error_cell_selector_b():
    res = error_cell_selector({"kind": "b", "row": 1}, scene="rectas-planos", grid_n=2)
    assert res == 'input[data-row="1"][data-col="2"]'

def test_error_cell_selector_vec():
    res = error_cell_selector({"kind": "vec", "name": "v_1", "index": 0}, scene="vectores", grid_n=2)
    assert res == 'input[data-vec-id="geo_vec_v_1"][data-vec-idx="0"]'

def test_error_cell_selector_comb():
    res = error_cell_selector({"kind": "vec", "name": "b", "index": 1}, scene="combinacion", grid_n=2)
    assert res == 'input[data-vec-id="geo_comb_b"][data-vec-idx="1"]'


def test_auto_range_large_tope():
    r = auto_range([1e15])
    assert r[1] <= 1e6


# ---- process_lines_planes ----

def test_lines_malformed_payload():
    result = GeometryController.process_lines_planes("not json")
    assert result["status"] == "ERROR"


def test_lines_2x2_unique_intersection():
    payload = json.dumps({
        "matrix_A": [["1", "1"], ["1", "-1"]],
        "vector_b": ["3", "1"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["n"] == 2
    assert result["solution_status"] == "UNIQUE_SOLUTION"
    assert result["set"]["kind"] == "POINT"
    assert result["set"]["point"] == [2.0, 1.0]
    assert result["set"]["point_exact"] == ["2", "1"]
    assert not result["pending_param"]
    # JSON serializable
    json.dumps(result)


def test_lines_parallel_flag():
    payload = json.dumps({
        "matrix_A": [["1", "1"], ["1", "1"]],
        "vector_b": ["1", "2"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["solution_status"] == "NO_SOLUTION"
    assert "parallel" in result["flags"]


def test_lines_degenerate_0eq0():
    payload = json.dumps({
        "matrix_A": [["0", "0"], ["1", "1"]],
        "vector_b": ["0", "2"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    eqs = result["equations"]
    assert eqs[0]["kind"] == "trivial"


def test_lines_degenerate_0eq5():
    payload = json.dumps({
        "matrix_A": [["0", "0"], ["1", "1"]],
        "vector_b": ["5", "2"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    eqs = result["equations"]
    assert eqs[0]["kind"] == "contradiction"


def test_lines_n4_bad_dimension():
    payload = json.dumps({
        "matrix_A": [["1", "0", "0", "0"]],
        "vector_b": ["1"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "ERROR"
    assert result.get("code") == "bad_dimension"


def test_lines_n10_bad_dimension():
    row = ["1"] * 10
    payload = json.dumps({
        "matrix_A": [row],
        "vector_b": ["1"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "ERROR"
    assert result.get("code") == "bad_dimension"


def test_lines_long_fractions():
    payload = json.dumps({
        "matrix_A": [["1001/1000", "1"], ["1", "-123456789012/987654321"]],
        "vector_b": ["3", "1"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    json.dumps(result)


def test_lines_m10_equations():
    """10 equations with 2 variables."""
    rows = [["1", str(i)] for i in range(10)]
    b = [str(i) for i in range(10)]
    payload = json.dumps({"matrix_A": rows, "vector_b": b})
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["m"] == 10


def test_lines_error_cell():
    payload = json.dumps({
        "matrix_A": [["1", "abc"], ["1", "1"]],
        "vector_b": ["1", "2"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "ERROR"
    assert result["error_cell"] is not None
    assert result["error_cell"]["kind"] == "A"


def test_lines_json_serializable():
    payload = json.dumps({
        "matrix_A": [["1", "2"], ["3", "4"]],
        "vector_b": ["5", "6"],
    })
    result = GeometryController.process_lines_planes(payload)
    serialized = json.dumps(result)
    assert isinstance(serialized, str)


def test_lines_no_mutation():
    payload_dict = {
        "matrix_A": [["1", "1"], ["1", "-1"]],
        "vector_b": ["3", "1"],
    }
    payload_str = json.dumps(payload_dict)
    original = copy.deepcopy(payload_dict)
    GeometryController.process_lines_planes(payload_str)
    assert payload_dict == original


def test_lines_3x3_unique():
    payload = json.dumps({
        "matrix_A": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        "vector_b": ["1", "2", "3"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["n"] == 3
    assert result["solution_status"] == "UNIQUE_SOLUTION"
    assert result["set"]["point"] == [1.0, 2.0, 3.0]


def test_lines_infinite_pending():
    payload = json.dumps({
        "matrix_A": [["1", "1"]],
        "vector_b": ["1"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["pending_param"]
    assert result["set"] is None


# ---- process_vectors ----

def test_vectors_basic_2d():
    payload = json.dumps({
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"},
        ],
    })
    result = GeometryController.process_vectors(payload)
    assert result["status"] == "OK"
    assert result["n"] == 2
    assert len(result["frames"]) == 25


def test_vectors_default_frame_k1():
    payload = json.dumps({
        "vectors": [
            {"data": ["2", "3"], "orientation": "column"},
            {"data": ["1", "1"], "orientation": "column"},
        ],
    })
    result = GeometryController.process_vectors(payload)
    assert result["status"] == "OK"
    default = result["default_frame"]
    frame = result["frames"][default]
    # k=1: ku = u, ku+v = u+v
    u = result["u"]["float"]
    v = result["v"]["float"]
    assert frame["ku"] == u
    assert frame["ku_plus_v"] == [u[0] + v[0], u[1] + v[1]]


def test_vectors_range_covers_all_frames():
    payload = json.dumps({
        "vectors": [
            {"data": ["10", "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"},
        ],
    })
    result = GeometryController.process_vectors(payload)
    r = result["range"]
    # k goes from -3 to 3, so k*10 ranges from -30 to 30
    assert r[1] >= 30


def test_vectors_dimension_4():
    payload = json.dumps({
        "vectors": [
            {"data": ["1", "0", "0", "0"], "orientation": "column"},
            {"data": ["0", "1", "0", "0"], "orientation": "column"},
        ],
    })
    result = GeometryController.process_vectors(payload)
    assert result["status"] == "ERROR"
    assert result.get("code") == "bad_dimension"


# ---- process_combination ----

def test_combination_unique_chain():
    # b = [3, 3], v1 = [1, 0], v2 = [0, 1]
    # => c1 = 3, c2 = 3 => chain: (3,0), (3,3) = b
    payload = json.dumps({
        "b": {"data": ["3", "3"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"},
        ],
    })
    result = GeometryController.process_combination(payload)
    assert result["status"] == "OK"
    assert result["solution_status"] == "UNIQUE"
    chain = result["chain"]
    assert chain is not None
    # Last point of chain == b in Fraction
    last = chain[-1]
    b_exact = result["b"]["exact"]
    assert last["exact"] == b_exact


def test_combination_infinite_no_chain():
    # b = [0, 0], v1 = [1, 0], v2 = [2, 0]
    # underdetermined
    payload = json.dumps({
        "b": {"data": ["0", "0"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
            {"data": ["2", "0"], "orientation": "column"},
        ],
    })
    result = GeometryController.process_combination(payload)
    assert result["status"] == "OK"
    if result["solution_status"] == "INFINITE":
        assert result["chain"] is None
        assert result["representation"] == "non_unique"


def test_combination_no_solution():
    # b = [0, 1], v1 = [1, 0] => can't reach
    payload = json.dumps({
        "b": {"data": ["0", "1"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
        ],
    })
    result = GeometryController.process_combination(payload)
    assert result["status"] == "OK"
    assert result["solution_status"] == "NO_SOLUTION"
    assert result["b_outside_span"]
    assert result["chain"] is None


def test_combination_dimension_4():
    payload = json.dumps({
        "b": {"data": ["1", "2", "3", "4"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0", "0", "0"], "orientation": "column"},
        ],
    })
    result = GeometryController.process_combination(payload)
    assert result["status"] == "ERROR"
    assert result.get("code") == "bad_dimension"
