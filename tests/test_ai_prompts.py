import pytest
from src.ai.prompts import build_messages, trim_history

def test_trim_history():
    hist = [
        {"text": "1", "sent": True},
        {"text": "2", "error": True},
        {"text": "3", "sent": False}
    ]
    trimmed = trim_history(hist)
    assert len(trimmed) == 2
    assert trimmed[0]["content"] == "1"
    assert trimmed[1]["content"] == "3"

def test_build_messages():
    hist = [{"text": "hola", "sent": True}]
    msgs = build_messages(hist, "adios", "[CONTEXTO]123[/CONTEXTO]", simpler=True)
    
    assert len(msgs) == 3
    assert msgs[0]["role"] == "system"
    assert msgs[1]["content"] == "hola"
    assert msgs[2]["role"] == "user"
    assert "[CONTEXTO]123[/CONTEXTO]" in msgs[2]["content"]
    assert "adios" in msgs[2]["content"]
    assert "más simple" in msgs[2]["content"]
