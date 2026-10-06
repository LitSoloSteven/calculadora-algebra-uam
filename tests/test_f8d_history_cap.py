import asyncio
from unittest.mock import AsyncMock
from src.frontend.components.ai_panel import AIPanel, MAX_HISTORY
from src.frontend.components.glosa_dock import MAX_HISTORY as DOCK_MAX_HISTORY


class MockAIPanel(AIPanel):
    def __init__(self, storage_dict):
        self._mock_storage = storage_dict
        super().__init__(None)

    @property
    def _storage(self):
        return self._mock_storage


def test_constants():
    assert MAX_HISTORY == 60
    assert DOCK_MAX_HISTORY == 60


def test_init_history_cap_exceeded():
    # Inicialización con 80 mensajes preexistentes en storage
    mock_storage = {
        'ai_chat_history': [{'text': f'msg {i}', 'sent': (i % 2 == 0)} for i in range(80)],
        'ai_ctx_enabled': True
    }
    panel = MockAIPanel(mock_storage)

    assert len(panel.chat_history) == 60
    # Verifica que se conservaron los últimos 60 (de 20 a 79)
    assert panel.chat_history[0]['text'] == 'msg 20'
    assert panel.chat_history[-1]['text'] == 'msg 79'


def test_init_history_under_cap():
    mock_storage = {
        'ai_chat_history': [{'text': f'msg {i}', 'sent': True} for i in range(30)],
        'ai_ctx_enabled': True
    }
    panel = MockAIPanel(mock_storage)

    assert len(panel.chat_history) == 30
    assert panel.chat_history[0]['text'] == 'msg 0'


def test_manual_append_cap_logic():
    mock_storage = {
        'ai_chat_history': [{'text': f'msg {i}', 'sent': True} for i in range(60)],
        'ai_ctx_enabled': True
    }
    panel = MockAIPanel(mock_storage)

    # Simular agregado con lógica de capping de glosa_dock
    msg = {"text": "msg 60", "sent": True}
    panel.chat_history.append(msg)
    if len(panel.chat_history) > MAX_HISTORY:
        panel.chat_history = panel.chat_history[-MAX_HISTORY:]

    assert len(panel.chat_history) == 60
    assert panel.chat_history[0]['text'] == 'msg 1'
    assert panel.chat_history[-1]['text'] == 'msg 60'
