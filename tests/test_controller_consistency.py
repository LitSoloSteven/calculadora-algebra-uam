import json
from fractions import Fraction

from src.frontend.controllers.linear_systems.controller_gauss import MatrixController
from src.frontend.controllers.linear_systems.controller_gauss_jordan import GaussJordanController


def _call_gauss(payload):
    return json.loads(MatrixController.process_system(json.dumps(payload)))


def _call_gj(payload):
    return json.loads(GaussJordanController.process_system(json.dumps(payload)))


# --- B6.1: JSON válido pero no dict ---

def test_gauss_list_payload_is_rejected():
    r = json.loads(MatrixController.process_system("[1, 2, 3]"))
    assert r["status"] == "error"
    assert "objeto JSON" in r["message"]


def test_gj_list_payload_is_rejected():
    r = json.loads(GaussJordanController.process_system("[1, 2, 3]"))
    assert r["status"] == "error"
    assert "objeto JSON" in r["message"]


def test_gauss_string_payload_is_rejected():
    r = json.loads(MatrixController.process_system('"hello"'))
    assert r["status"] == "error"
    assert "objeto JSON" in r["message"]


# --- B6.2: GJ verifica por status, no por mensaje ---

def test_gj_verification_runs_for_unique_solution():
    """La verificación debe ejecutarse cuando status == UNIQUE_SOLUTION."""
    payload = {"matrix_A": [["2", "1"], ["1", "-1"]], "vector_b": ["5", "1"], "variables": None}
    r = _call_gj(payload)
    assert r["status"] == "UNIQUE_SOLUTION"
    assert len(r["verification_steps_latex"]) > 0


def test_gj_verification_absent_for_no_solution():
    payload = {"matrix_A": [["1", "1"], ["1", "1"]], "vector_b": ["1", "2"], "variables": None}
    r = _call_gj(payload)
    assert r["status"] == "NO_SOLUTION"
    assert r["verification_steps_latex"] == []


# --- B6.3: Gauss no convierte solución a float ---

def test_gauss_verification_uses_exact_fractions():
    """Con solución fraccionaria 9/7, -15/14, 2/7, Gauss debe verificar
    con esos strings exactos, no con floats aproximados."""
    payload = {
        "matrix_A": [["1", "2", "3"], ["3", "2", "1"], ["-1", "-2", "4"]],
        "vector_b": ["0", "2", "2"],
        "variables": None,
    }
    r = _call_gauss(payload)
    assert r["status"] == "UNIQUE_SOLUTION"
    # El reporte debe contener fracciones exactas, no decimales aproximados
    joined = " ".join(r["verification_steps_latex"])
    assert r"\frac{9}{7}" in joined
    assert "1.2857" not in joined
    assert "Correcto" in joined or r"\text{Correcto}" in joined