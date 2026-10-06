import pytest
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator
from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixOpsController
from src.frontend.components.ai_panel import AIPanel
from src.ai.context import AIContext, StepRef


class MockAIPanel(AIPanel):
    def __init__(self, active_ui, storage_dict=None):
        self._mock_storage = storage_dict if storage_dict is not None else {"ai_ctx_enabled": True}
        super().__init__(active_ui)

    @property
    def _storage(self):
        return self._mock_storage


def test_matrix_focus_add():
    evaluator = MatrixExpressionEvaluator()
    m_a = Matrix(2, 2, [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]])
    m_b = Matrix(2, 2, [[Fraction(5), Fraction(6)], [Fraction(7), Fraction(8)]])
    res = evaluator.evaluate("A+B", {"A": m_a, "B": m_b})
    assert res["status"] == "SUCCESS"
    assert len(res["segment_steps"]) == 1

    step = res["segment_steps"][0]
    foc = MatrixOpsController.build_step_focus(step, 1, 1)

    assert foc["index"] == 1
    assert foc["total"] == 1
    assert foc["kind"] == "otro"
    assert "Suma" in foc["op"]
    assert "T1" in foc["op"]
    assert "A" in foc["op"] and "B" in foc["op"]
    assert r"\cdot" not in foc["op"]
    assert "{" not in foc["op"] and "}" not in foc["op"]

    assert foc["detail"] is not None
    assert foc["detail"]["forma"] == "2×2"
    assert "ejemplo" in foc["detail"]
    assert foc["detail"]["ejemplo"].startswith("Celda (1, 1)")
    assert len(foc["detail"]["ejemplo"]) <= 120
    assert foc["detail"]["ejemplo"] != step["cell_by_cell_steps"][0]["description"]


def test_matrix_focus_multiply():
    evaluator = MatrixExpressionEvaluator()
    m_a = Matrix(2, 3, [[Fraction(1), Fraction(2), Fraction(0)], [Fraction(3), Fraction(4), Fraction(1)]])
    m_b = Matrix(3, 2, [[Fraction(2), Fraction(1)], [Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]])
    res = evaluator.evaluate("AB", {"A": m_a, "B": m_b})
    assert res["status"] == "SUCCESS"
    assert len(res["segment_steps"]) == 1

    step = res["segment_steps"][0]
    foc = MatrixOpsController.build_step_focus(step, 1, 1)

    assert foc["index"] == 1
    assert foc["total"] == 1
    assert foc["kind"] == "otro"
    assert "Multiplicación" in foc["op"]
    assert "T1" in foc["op"]
    assert r"\cdot" not in foc["op"]
    assert "{" not in foc["op"] and "}" not in foc["op"]

    assert foc["detail"] is not None
    assert foc["detail"]["forma"] == "2×2"
    assert "ejemplo" in foc["detail"]
    assert foc["detail"]["ejemplo"].startswith("Fila 1 de A")
    assert len(foc["detail"]["ejemplo"]) <= 120
    assert foc["detail"]["ejemplo"] != step["cell_by_cell_steps"][0]["description"]


def test_matrix_focus_transpose():
    evaluator = MatrixExpressionEvaluator()
    m_a = Matrix(2, 2, [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]])
    res = evaluator.evaluate("A^T", {"A": m_a})
    assert res["status"] == "SUCCESS"
    assert len(res["segment_steps"]) == 1

    step = res["segment_steps"][0]
    foc = MatrixOpsController.build_step_focus(step, 1, 1)

    assert foc["index"] == 1
    assert foc["total"] == 1
    assert foc["kind"] == "otro"
    assert foc["detail"] is not None
    assert foc["detail"]["forma"] == "2×2"
    assert "ejemplo" not in foc["detail"]


def test_ai_panel_collect_context_step_detail():
    class DummyUI:
        def get_ai_context(self):
            return AIContext(
                tool="matrix_ops",
                view="Matrices",
                label="Matriz A y B",
                input={"expresion": "AB"}
            )

    panel = MockAIPanel(DummyUI(), {"ai_ctx_enabled": True})

    panel.explain_focus = {
        "index": 1,
        "total": 1,
        "kind": "otro",
        "op": "Multiplicación: T1 = A * B",
        "detail": {"forma": "2×2", "ejemplo": "Celda (1, 1): 1*2 = 2"}
    }

    ctx_text = panel._collect_context()
    assert "2×2" in ctx_text or "Multiplicación" in ctx_text
