import pytest
from fractions import Fraction

from src.ai.prompts import build_messages, trim_history
from src.ai.context import serialize_context, AIContext, fingerprint, is_stale, MAXIMO_CARACTERES_CONTEXTO
from src.frontend.components.glosa_chips import _is_keyboard_event
from src.backend.models.matrix import Matrix

def test_build_messages_roles_and_question():
    u = {"role": "user", "content": "¿Cómo se resuelve esto?"}
    a = {"role": "assistant", "content": "Se resuelve aplicando eliminación de Gauss."}
    q = "¿Qué hago en el paso 2?"
    
    msgs = build_messages(history=[u, a], question=q)
    roles = [m["role"] for m in msgs]
    assert roles == ["system", "user", "assistant", "user"]
    for m in msgs:
        assert m["content"].strip() != ""
    # q aparece exactamente una vez en todo el payload
    assert sum(q in m["content"] for m in msgs) == 1

def test_build_messages_empty_history():
    q = "Hola Glosa"
    msgs = build_messages(history=[], question=q)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    assert msgs[1]["content"] == q
    # Con historial vacío no hay mensajes assistant vacíos
    assert not any(m["role"] == "assistant" for m in msgs)

def test_build_messages_filters_empty_and_error():
    history = [
        {"role": "user", "content": "Mensaje válido 1"},
        {"role": "assistant", "content": "", "text": ""},
        {"role": "user", "content": "   "},
        {"role": "assistant", "content": "Error ocurrió", "error": True},
        {"role": "assistant", "content": "Respuesta válida", "text": "Respuesta válida"}
    ]
    msgs = build_messages(history=history, question="Nueva pregunta")
    # Los roles deben ser system, user (válido 1), assistant (válida), user (nueva pregunta)
    roles = [m["role"] for m in msgs]
    assert roles == ["system", "user", "assistant", "user"]
    for m in msgs:
        assert m["content"].strip() != ""
        assert not m.get("error", False)

def test_serialize_context_with_matrix_and_fraction():
    mat = Matrix(2, 2, [[Fraction(1, 2), Fraction(3, 4)], [Fraction(5, 6), Fraction(7, 8)]])
    ctx = AIContext(
        tool="inversa",
        view="inversa",
        label="Inversa 2×2",
        input={"rows": 2, "cols": 2, "data": [["1/2", "3/4"], ["5/6", "7/8"]]},
        result={"matrix": mat, "det": Fraction(1, 16), "custom": Fraction(2, 3)}
    )
    serialized = serialize_context(ctx)
    assert isinstance(serialized, str)
    assert "[CONTEXTO]" in serialized
    assert len(serialized) <= MAXIMO_CARACTERES_CONTEXTO
    assert "rows" in serialized

def test_fingerprint_and_is_stale():
    # Estabilidad ante orden de claves
    obj_a = {"alpha": 1, "beta": [1, 2, 3], "gamma": {"x": "a", "y": "b"}}
    obj_b = {"gamma": {"y": "b", "x": "a"}, "beta": [1, 2, 3], "alpha": 1}
    assert fingerprint(obj_a) == fingerprint(obj_b)
    
    fp_a = fingerprint(obj_a)
    # is_stale con None fp -> False
    assert is_stale(obj_a, None) is False
    # Igual entrada -> False
    assert is_stale(obj_b, fp_a) is False
    # Entrada distinta -> True
    obj_c = {"alpha": 2, "beta": [1, 2, 3], "gamma": {"x": "a", "y": "b"}}
    assert is_stale(obj_c, fp_a) is True

def test_keyboard_detection():
    # _is_keyboard_event({'detail': 0}) y (0) -> True; ({'detail': 1}) -> False
    assert _is_keyboard_event({"detail": 0}) is True
    assert _is_keyboard_event(0) is True
    assert _is_keyboard_event([{"detail": 0}]) is True
    assert _is_keyboard_event([0]) is True
    
    assert _is_keyboard_event({"detail": 1}) is False
    assert _is_keyboard_event(1) is False
    assert _is_keyboard_event([{"detail": 1}]) is False
    assert _is_keyboard_event([1]) is False
    assert _is_keyboard_event(None) is False
