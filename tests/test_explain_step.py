from src.ai.prompts import construir_pregunta_explicar_paso


def test_construir_pregunta_explicar_paso():
    q = construir_pregunta_explicar_paso("eliminacion", 2, 5, "Fila 2 = Fila 2 - (3)·Fila 1")
    assert "Paso 2 de 5" in q
    assert "Fila 2 = Fila 2 - (3)·Fila 1" in q
    assert "qué se busca" in q.lower() or "por qué" in q.lower() or "qué cambia" in q.lower()
