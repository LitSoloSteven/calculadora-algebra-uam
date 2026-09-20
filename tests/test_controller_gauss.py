"""Tests del controlador de Gauss.

Cubre:
- Validación de payload (commit d243ea2)
- Rechazo de fallas silenciosas (vector_b incompleto)
- Manejo de JSON malformado
"""
import json
import pytest
from src.frontend.controllers.linear_systems.controller_gauss import MatrixController


def _process(payload):
    return json.loads(MatrixController.process_system(json.dumps(payload)))


def test_unique_solution_3x3():
    payload = {
        "matrix_A": [["2", "1", "-1"], ["-3", "-1", "2"], ["-2", "1", "2"]],
        "vector_b": ["8", "-11", "-3"],
        "variables": ["x1", "x2", "x3"],
    }
    res = _process(payload)
    assert res["status"] == "UNIQUE_SOLUTION"
    assert res["solution"] == ["2", "3", "-1"]
    assert len(res["intermediate_steps_latex"]) > 0
    assert len(res["verification_steps_latex"]) > 0
    for paso in res["verification_steps_latex"]:
        assert "Incorrecto" not in paso, f"Verificación falló: {paso}"


def test_vector_b_incomplete_is_rejected():
    """Regresión: antes se rellenaba con '0' silenciosamente."""
    payload = {
        "matrix_A": [["1", "0"], ["0", "1"], ["1", "1"]],
        "vector_b": ["5"],  # faltan 2 valores
        "variables": ["x1", "x2"],
    }
    res = _process(payload)
    assert res["status"] == "error"
    assert "1" in res["message"] and "3" in res["message"]


def test_ragged_matrix_is_rejected():
    payload = {
        "matrix_A": [["1", "2"], ["3"]],  # segunda fila tiene 1 columna
        "vector_b": ["5", "6"],
        "variables": ["x1", "x2"],
    }
    res = _process(payload)
    assert res["status"] == "error"
    assert "fila" in res["message"].lower()


def test_no_solution_system():
    payload = {
        "matrix_A": [["1", "1"], ["1", "1"]],
        "vector_b": ["3", "5"],
        "variables": ["x1", "x2"],
    }
    res = _process(payload)
    assert res["status"] == "NO_SOLUTION"
    assert res["solution"] is None
    assert "inconsistente" in res["classification"].lower()


def test_non_numeric_cell_reports_coordinates():
    payload = {
        "matrix_A": [["abc", "1"], ["1", "1"]],
        "vector_b": ["1", "1"],
        "variables": ["x1", "x2"],
    }
    res = _process(payload)
    assert res["status"] == "error"
    assert "A[1,1]" in res["message"]


def test_malformed_json_payload():
    res = json.loads(MatrixController.process_system("esto no es json {{{"))
    assert res["status"] == "error"
    assert "JSON" in res["message"] or "json" in res["message"]