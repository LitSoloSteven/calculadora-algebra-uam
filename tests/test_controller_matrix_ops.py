import json
from fractions import Fraction

from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixOpsController


def _call(expr, matrices):
    return json.loads(MatrixOpsController.process_expression(expr, json.dumps(matrices)))


# --- Precisión exacta (bug crítico del revisor) ---

def test_build_matrices_preserves_large_denominator():
    """El bug original: 1/1001 perdía precisión al pasar por el controller."""
    mats = MatrixOpsController._build_matrices({
        "A": {"rows": 1, "cols": 1, "data": [["1/1001"]]}
    })
    assert mats["A"].data[0][0] == Fraction(1, 1001)


def test_simple_expression_succeeds():
    mats = {"A": {"rows": 1, "cols": 1, "data": [["2"]]}}
    r = _call("A", mats)
    assert r["status"] == "SUCCESS"
    assert r["final_variable"] == "A"


# --- Validación explícita del payload (antipatrón "except Exception") ---

def test_missing_cols_gives_context():
    mats = {"A": {"rows": 2, "data": [[1, 2], [3, 4]]}}
    r = _call("A", mats)
    assert r["status"] == "ERROR"
    assert "cols" in r["message"]
    assert "A" in r["message"]


def test_missing_rows_gives_context():
    mats = {"A": {"cols": 2, "data": [[1, 2]]}}
    r = _call("A", mats)
    assert r["status"] == "ERROR"
    assert "rows" in r["message"]


def test_data_not_list():
    mats = {"A": {"rows": 1, "cols": 1, "data": "abc"}}
    r = _call("A", mats)
    assert r["status"] == "ERROR"
    assert "lista" in r["message"].lower()


def test_row_count_mismatch():
    mats = {"A": {"rows": 3, "cols": 1, "data": [["1"], ["2"]]}}
    r = _call("A", mats)
    assert r["status"] == "ERROR"
    assert "filas" in r["message"]


def test_row_length_mismatch():
    mats = {"A": {"rows": 2, "cols": 2, "data": [[1], [3, 4]]}}
    r = _call("A", mats)
    assert r["status"] == "ERROR"
    assert "fila" in r["message"].lower()
    assert "columnas" in r["message"].lower()


def test_non_numeric_cell_reports_coordinates():
    mats = {"A": {"rows": 1, "cols": 2, "data": [["1", "abc"]]}}
    r = _call("A", mats)
    assert r["status"] == "ERROR"
    assert "[1,2]" in r["message"]


def test_empty_matrices_dict():
    r = _call("A", {})
    assert r["status"] == "ERROR"
    assert "matriz" in r["message"].lower()


def test_malformed_json_returns_context():
    r = json.loads(MatrixOpsController.process_expression("A", "{no es json}"))
    assert r["status"] == "ERROR"
    assert "JSON malformado" in r["message"]


def test_undefined_matrix_in_expression():
    mats = {"A": {"rows": 1, "cols": 1, "data": [["1"]]}}
    r = _call("B", mats)
    assert r["status"] == "ERROR"
    assert "B" in r["message"]