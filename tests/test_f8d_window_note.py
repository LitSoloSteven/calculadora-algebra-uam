from src.ai.context import describir_matriz, window_note_from, AIContext


def test_nota_ventana_matriz_pequena():
    # Matriz 3x3 no debe generar ventana
    rows = [[str(i * 3 + j + 1) for j in range(3)] for i in range(3)]
    desc = describir_matriz(rows)
    assert "window" not in desc
    assert window_note_from(desc) is None


def test_nota_ventana_matriz_50x50():
    # Matriz 50x50 debe generar ventana 6x6
    rows = [["1" for _ in range(50)] for _ in range(50)]
    desc = describir_matriz(rows)
    assert "window" in desc
    assert desc["window"] == [6, 6]
    note = window_note_from(desc)
    assert note == "ventana 6×6 de 50×50"


def test_nota_ventana_multiples_matrices_selecciona_mayor():
    # Matriz pequeña 3x3
    small = describir_matriz([["1"] * 3 for _ in range(3)])
    # Matriz 12x12
    medium = describir_matriz([["1"] * 12 for _ in range(12)])
    # Matriz 50x50
    large = describir_matriz([["1"] * 50 for _ in range(50)])

    note = window_note_from(small, medium, large)
    assert note == "ventana 6×6 de 50×50"

    note_med = window_note_from(small, medium)
    assert note_med == "ventana 6×6 de 12×12"


def test_window_note_empty():
    assert window_note_from() is None
    assert window_note_from({}) is None
    assert window_note_from(None) is None


def test_pildora_contexto_con_nota_ventana():
    ctx = AIContext(
        tool="inversa",
        view="Matriz Inversa",
        label="A (50×50)",
        input={},
        window_note="ventana 6×6 de 50×50"
    )
    assert ctx.window_note == "ventana 6×6 de 50×50"
