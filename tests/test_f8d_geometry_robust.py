import json
import pytest
from src.frontend.controllers.geometry.controller_geometry import GeometryController


def test_lines_planes_not_finite():
    # Matriz con un valor numérico gigantesco (overflow en float)
    huge_num = "1" + "0" * 400
    payload = {
        "matrix_A": [
            [huge_num, "2"],
            ["1", "1"]
        ],
        "vector_b": ["1", "2"]
    }
    res = GeometryController.process_lines_planes(json.dumps(payload))
    assert res["status"] == "ERROR"
    assert res.get("code") == "not_finite"
    assert "demasiado grande" in res.get("message", "")
    assert res.get("n") == 2


def test_lines_planes_not_finite_in_b():
    huge_num = "1" + "0" * 400
    payload = {
        "matrix_A": [
            ["1", "2"],
            ["1", "1"]
        ],
        "vector_b": [huge_num, "2"]
    }
    res = GeometryController.process_lines_planes(json.dumps(payload))
    assert res["status"] == "ERROR"
    assert res.get("code") == "not_finite"
    assert "demasiado grande" in res.get("message", "")


def test_combination_with_big_b_no_exception():
    huge_num = "1" + "0" * 400
    payload = {
        "b": {"data": [huge_num, "2"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"}
        ]
    }
    # No debe lanzar excepción
    res = GeometryController.process_combination(json.dumps(payload))
    assert res["status"] == "ERROR"
    assert res.get("code") == "not_finite"
    assert "demasiado grande" in res.get("message", "")


def test_combination_with_big_vector_no_exception():
    huge_num = "1" + "0" * 400
    payload = {
        "b": {"data": ["1", "2"], "orientation": "column"},
        "vectors": [
            {"data": [huge_num, "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"}
        ]
    }
    res = GeometryController.process_combination(json.dumps(payload))
    assert res["status"] == "ERROR"
    assert res.get("code") == "not_finite"
    assert "demasiado grande" in res.get("message", "")
