import pytest
from src.frontend.controllers.linear_systems._shared import build_steps_meta

class MockMatrix:
    def __init__(self, data):
        self.data = data
        self.rows = len(data)
        self.cols = len(data[0])
    def get(self, r, c):
        return self.data[r][c]

def test_build_steps_meta():
    steps = [
        {"description": "Intercambio: Fila 1 ↔ Fila 2", "matrix": MockMatrix([[1,2],[3,4]])},
        {"description": "Fila 2 = Fila 2 − (3) · Fila 1", "matrix": MockMatrix([[1,2],[0,-2]])}
    ]
    meta = build_steps_meta(steps)
    assert len(meta) == 2
    assert meta[0]["kind"] == "intercambio"
    assert meta[1]["kind"] == "eliminacion"
    assert meta[1]["index"] == 2
    assert meta[1]["total"] == 2
