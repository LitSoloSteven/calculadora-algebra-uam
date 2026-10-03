import pytest
from src.ai.prompts import build_explain_step_question

def test_build_explain_step_question():
    q = build_explain_step_question("eliminacion", 2, 5, "Fila 2 = Fila 2 - (3)·Fila 1")
    assert "Paso 2 de 5" in q
    assert "Fila 2 = Fila 2 - (3)·Fila 1" in q
    assert "qué se busca" in q.lower() or "por qué" in q.lower() or "qué cambia" in q.lower()
