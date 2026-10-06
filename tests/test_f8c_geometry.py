import json
import pytest

from src.frontend.controllers.geometry.controller_geometry import GeometryController
from src.frontend.controllers.vector_ops.controller_vector_ops import VectorOpsController
from src.frontend.controllers.inverse_ops.controller_inverse_ops import InverseOpsController
from src.frontend.navigation import LegacyRedirect, redirect_location
from src.frontend.components import handoff

def test_process_lines_planes_exact_fractions():
    payload = json.dumps({
        "matrix_A": [["1001/1000", "1"], ["0", "1"]],
        "vector_b": ["1001/1000", "2"]
    })
    res = GeometryController.process_lines_planes(payload)
    assert res["status"] == "OK"
    eq0 = res["equations"][0]
    assert eq0["coeffs_exact"][0] == "1001/1000"
    assert eq0["b_exact"] == "1001/1000"

def test_infinite_2d_segment():
    payload = json.dumps({
        "matrix_A": [["1", "1"], ["2", "2"]],
        "vector_b": ["2", "4"]
    })
    res = GeometryController.process_lines_planes(payload)
    assert res["status"] == "OK"
    sol_set = res["set"]
    assert sol_set is not None
    assert sol_set["kind"] == "LINE"
    assert sol_set["dimension"] == 1
    
    seg = sol_set["segment"]
    assert seg is not None and len(seg) == 2
    h = res["range"][1]
    
    for pt in seg:
        x, y = pt[0], pt[1]
        assert -h <= x <= h
        assert -h <= y <= h
        # Debe satisfacer x + y = 2 con tolerancia 1e-9
        assert abs(x + y - 2.0) < 1e-9

def test_process_vectors_default_frame():
    payload = json.dumps({
        "vectors": [
            {"data": ["1", "2"], "orientation": "column"},
            {"data": ["3", "4"], "orientation": "column"}
        ]
    })
    res = GeometryController.process_vectors(payload)
    assert res["status"] == "OK"
    df = res["default_frame"]
    assert res["frames"][df]["k_exact"] == "1"

def test_handoff_store_eviction_and_max_chars(monkeypatch):
    handoff._STORE.clear()
    
    counter = 1000.0
    def mock_now():
        nonlocal counter
        counter += 1.0
        return counter
        
    monkeypatch.setattr(handoff, "_now", mock_now)
    
    tokens = []
    for _ in range(65):
        t = handoff.put_matrix("test", [["1"]])
        tokens.append(t)
        
    assert len(handoff._STORE) <= 64
    # El más antiguo (tokens[0]) debió ser descartado por la evicción
    res0 = handoff.consume_matrix(tokens[0], max_n=5)
    assert res0.status == 'missing'
    
    # Celda de 65 caracteres produce 'invalid' en las tres funciones consume
    long_cell = "1" * 65
    t_mat = handoff.put_matrix("test", [[long_cell]])
    assert handoff.consume_matrix(t_mat, max_n=5).status == 'invalid'
    
    t_sys = handoff.put_system("test", [[long_cell]], ["1"])
    assert handoff.consume_system(t_sys, max_m=5, allowed_n={1, 2, 3}).status == 'invalid'
    
    t_vec = handoff.put_vectors("test", "vectores", [[long_cell, "1"]])
    assert handoff.consume_vectors(t_vec, allowed_n={2, 3}).status == 'invalid'

def test_redirect_location():
    rule = LegacyRedirect(path="/old", target_route="/new", fixed_query=(("fixed_key", "val_fixed"),))
    incoming = [
        ("a", "1"),
        ("a", "2"),
        ("x", ""),
        ("fixed_key", "override_ignored")
    ]
    loc = redirect_location(rule, incoming)
    # fixed_key debe prevalecer sobre el entrante
    assert "fixed_key=val_fixed" in loc
    assert "override_ignored" not in loc
    # Conserva pares duplicados a=1 y a=2
    assert "a=1" in loc
    assert "a=2" in loc
    # Conserva vacíos x=
    assert "x=" in loc

def test_geometry_out_of_range_and_segment_invisible():
    # Intercepto enorme -> out_of_range True
    p1 = json.dumps({"matrix_A": [["1", "0"], ["0", "1"]], "vector_b": ["10000000000", "1"]})
    r1 = GeometryController.process_lines_planes(p1)
    assert r1["out_of_range"] is True
    
    # Recta fuera de la caja visual -> segment_visible False
    p2 = json.dumps({"matrix_A": [["1", "1"], ["2", "2"]], "vector_b": ["10000000000", "20000000000"]})
    r2 = GeometryController.process_lines_planes(p2)
    assert r2["set"]["segment_visible"] is False

def test_vector_linear_combination_steps_meta():
    payload = json.dumps({
        "b": {"data": ["5", "6"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"}
        ]
    })
    res_json = VectorOpsController.process_linear_combination(payload)
    res = json.loads(res_json)
    meta = res["steps_meta"]
    gauss_steps = res["gauss_steps"]
    
    assert len(meta) == len(gauss_steps)
    for i, m in enumerate(meta):
        assert m["index"] == i + 1
        
    for s in res.get("setup_steps", []):
        assert "matrix" not in s
    for s in res.get("gauss_steps", []):
        assert "matrix" not in s
    for s in res.get("steps", []):
        assert "matrix" not in s

def test_inverse_build_focus_12x12():
    n = 12
    # Matriz triangular superior invertible
    data = [["2" if i == j else ("1" if i < j else "0") for j in range(n)] for i in range(n)]
    payload = json.dumps({"n": n, "data": data})
    res = InverseOpsController.process_inverse(payload)
    assert res["status"] == "SUCCESS"
    
    # Encontrar paso de eliminación
    elim_indices = [i for i, s in enumerate(res["steps"]) if s["kind"] == "eliminacion"]
    assert len(elim_indices) > 0
    idx = elim_indices[0]
    
    focus = InverseOpsController.build_focus_for_step(res["steps"], idx)
    assert len(focus["rows_before"]) > 0
    assert len(focus["rows_after"]) > 0
    # Augmented matrix 12x24 -> 24 cols > 12 -> cols is not None
    assert focus["cols"] is not None
