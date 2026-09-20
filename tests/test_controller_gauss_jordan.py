"""Tests del controlador de Gauss-Jordan.

Cubre:
- Validación de payload (commit 4ae37f0)
- Captura de ZeroDivisionError en Fraction('1/0')
- Manejo de JSON malformado
"""
import json
from src.frontend.controllers.linear_systems.controller_gauss_jordan import GaussJordanController


def _process(payload):
    return json.loads(GaussJordanController.process_system(json.dumps(payload)))


def test_unique_solution_3x3():
    payload = {
        "matrix_A": [["2", "1", "-1"], ["-3", "-1", "2"], ["-2", "1", "2"]],
        "vector_b": ["8", "-11", "-3"],
        "variables": ["x1", "x2", "x3"],
    }
    res = _process(payload)
    assert res["status"] == "UNIQUE_SOLUTION"
    assert res["solution"] == ["2", "3", "-1"]
    for paso in res["verification_steps_latex"]:
        assert "Incorrecto" not in paso


def test_vector_b_incomplete_is_rejected():
    payload = {
        "matrix_A": [["1", "0"], ["0", "1"], ["1", "1"]],
        "vector_b": ["5"],
        "variables": ["x1", "x2"],
    }
    res = _process(payload)
    assert res["status"] == "error"
    assert "1" in res["message"] and "3" in res["message"]


def test_ragged_matrix_is_rejected():
    payload = {
        "matrix_A": [["1", "2"], ["3"]],
        "vector_b": ["5", "6"],
        "variables": ["x1", "x2"],
    }
    res = _process(payload)
    assert res["status"] == "error"
    assert "fila" in res["message"].lower()


def test_division_by_zero_in_cell_is_caught():
    """Regresión: '1/0' lanzaba ZeroDivisionError que escapaba al except ValueError."""
    payload = {
        "matrix_A": [["1/0", "1"], ["1", "1"]],
        "vector_b": ["1", "1"],
        "variables": ["x1", "x2"],
    }
    res = _process(payload)
    assert res["status"] == "error"
    # El mensaje debe mencionar el problema numérico, no un "error interno" genérico
    assert "numérico" in res["message"].lower() or "cero" in res["message"].lower()


def test_malformed_json_payload():
    res = json.loads(GaussJordanController.process_system("no es json"))
    assert res["status"] == "error"
    assert "JSON" in res["message"] or "json" in res["message"]


def test_no_solution_system():
    payload = {
        "matrix_A": [["1", "1"], ["1", "1"]],
        "vector_b": ["3", "5"],
        "variables": ["x1", "x2"],
    }
    res = _process(payload)
    assert res["status"] == "NO_SOLUTION"