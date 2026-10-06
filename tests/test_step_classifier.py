import pytest
from src.frontend.controllers._step_classifier import classify_step

def test_classify_pivote():
    res = classify_step("Pivote seleccionado en Fila 2, Columna 2")
    assert res["kind"] == "pivote"
    assert res["row1"] == 1
    assert res["col"] == 1

def test_classify_eliminacion():
    res = classify_step("Fila 3 = Fila 3 − (2) · Fila 1")
    assert res["kind"] == "eliminacion"
    assert res["row1"] == 2
    assert res["row2"] == 0
    assert res["val_str"] == "2"

def test_classify_intercambio():
    res = classify_step("Intercambio: Fila 1 ↔ Fila 3")
    assert res["kind"] == "intercambio"
    assert res["row1"] == 0
    assert res["row2"] == 2

