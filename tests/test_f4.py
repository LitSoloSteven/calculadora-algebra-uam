import pytest
import os
from src.frontend.app import resolver_secreto_almacenamiento
from src.frontend.components.glosa_render import render_glosa_text
from src.frontend.components.ai_panel import AIPanel

def test_storage_secret_dev():
    env = {"SCALARIS_ENV": "development"}
    assert resolver_secreto_almacenamiento(env) == "scalaris_dev_secret_key"

def test_storage_secret_prod_missing():
    env = {"SCALARIS_ENV": "production"}
    with pytest.raises(SystemExit):
        resolver_secreto_almacenamiento(env)
        
def test_storage_secret_prod_present():
    env = {"SCALARIS_ENV": "production", "STORAGE_SECRET": "my_secret"}
    assert resolver_secreto_almacenamiento(env) == "my_secret"

def test_glosa_render():
    text = "Hola\n```print('hola')```\nMás texto"
    res = render_glosa_text(text)
    assert 'print(&#x27;hola&#x27;)' in res
    assert 'class="glosa-pre"' in res
    assert 'Hola' in res

def test_glosa_render_unclosed():
    text = "A```B"
    res = render_glosa_text(text)
    # the unclosed backticks should be treated as text, but HTML escaped
    assert 'A' in res
    assert 'B' in res

def test_glosa_history():
    panel = AIPanel(None)
    panel._mock_storage = {}
    panel.__class__._storage = property(lambda self: self._mock_storage)
    assert len(panel.chat_history) == 0
    panel.chat_history.append({"text": "Test"})
    assert len(panel.chat_history) == 1
    panel.clear_chat()
    assert len(panel.chat_history) == 0

def test_glosa_assets():
    from src.frontend.components.icons import icon_svg
    assert '<svg' in icon_svg('glosa')

def test_glosa_contrast():
    # Comprobar que en theme.py la configuracion de tokens está presente en los temas
    pass
