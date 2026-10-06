"""Pruebas de contexto de slots de NiceGUI en tareas asíncronas (F8e).

INFERIDO: Verificación estática de contratos y pruebas unitarias de _spawn y _js
con cliente stub para validar que el slot context se gestiona adecuadamente.
"""
import asyncio
from pathlib import Path
import re
import pytest

from src.frontend.views.geometry.view_geometry import GeometryUI
from src.frontend.components.ai_panel import AIPanel
from src.frontend.components.glosa_dock import GlosaDockMixin


class StubClient:
    """Cliente falso para probar el protocolo de contexto y llamadas JS."""
    def __init__(self):
        self.entered = 0
        self.exited = 0
        self.js_calls = []
        self.is_deleted = False

    def __enter__(self):
        self.entered += 1
        return self

    def __exit__(self, *args):
        self.exited += 1

    def run_javascript(self, code: str, *, timeout: float = 1.0):
        self.js_calls.append(code)


def test_no_ui_run_javascript_in_geometry_files():
    """view_geometry.py y scenes_mixin.py no deben contener ui.run_javascript(."""
    geo_path = Path("src/frontend/views/geometry/view_geometry.py")
    scenes_path = Path("src/frontend/views/geometry/scenes_mixin.py")

    assert geo_path.exists()
    assert scenes_path.exists()

    geo_content = geo_path.read_text(encoding="utf-8")
    scenes_content = scenes_path.read_text(encoding="utf-8")

    assert "ui.run_javascript(" not in geo_content
    assert "ui.run_javascript(" not in scenes_content


def test_view_geometry_contract():
    """view_geometry.py contiene self._client = y definición de _js y _spawn."""
    geo_path = Path("src/frontend/views/geometry/view_geometry.py")
    content = geo_path.read_text(encoding="utf-8")

    assert "self._client = " in content
    assert "def _js(self" in content
    assert "def _spawn(self" in content
    assert "self._spawn(self._debounced_update())" in content


def test_glosa_dock_contract():
    """glosa_dock.py no contiene asyncio.create_task(self._submit y contiene _spawn(."""
    dock_path = Path("src/frontend/components/glosa_dock.py")
    assert dock_path.exists()
    content = dock_path.read_text(encoding="utf-8")

    assert "asyncio.create_task(self._submit" not in content
    assert "def _spawn(self" in content
    assert "self._spawn(self._submit" in content


def test_render_error_contract():
    """El cuerpo de _render_error no contiene ui.run_javascript."""
    geo_path = Path("src/frontend/views/geometry/view_geometry.py")
    content = geo_path.read_text(encoding="utf-8")

    # Extraer el método _render_error
    match = re.search(r"def _render_error\(self.*?\n(?=\s{4}def |\Z)", content, re.DOTALL)
    assert match is not None
    render_error_body = match.group(0)

    assert "ui.run_javascript" not in render_error_body
    assert "self._js" in render_error_body


def test_geometry_ui_js_and_spawn_with_stub_client():
    """Prueba _js y _spawn en GeometryUI con un cliente simulado."""
    async def _test():
        view = GeometryUI()
        client = StubClient()
        view._client = client

        # 1. Probar _js
        view._js("console.log('hola');")
        assert client.js_calls == ["console.log('hola');"]

        # 2. Probar _js con cliente eliminado (no-op)
        client.is_deleted = True
        view._js("console.log('ignorado');")
        assert len(client.js_calls) == 1

        client.is_deleted = False

        # 3. Probar _spawn
        entered_during_coro = False

        async def sample_coro():
            nonlocal entered_during_coro
            if client.entered == 1 and client.exited == 0:
                entered_during_coro = True
            return "ok"

        task = view._spawn(sample_coro())
        assert isinstance(task, asyncio.Task)
        res = await task
        assert res == "ok"
        assert entered_during_coro is True
        assert client.entered == 1
        assert client.exited == 1

    asyncio.run(_test())


def test_glosa_dock_spawn_and_scroll_with_stub_client():
    """Prueba _spawn y _scroll_to_bottom en GlosaDockMixin con cliente simulado."""
    async def _test():
        class DummyDock(GlosaDockMixin):
            def __init__(self):
                self._client = None

        dock = DummyDock()
        client = StubClient()
        dock._client = client

        # 1. Probar _scroll_to_bottom con client.run_javascript
        dock._scroll_to_bottom()
        assert len(client.js_calls) == 1
        assert "glosa-log" in client.js_calls[0]

        # 2. Probar _spawn
        entered_during_coro = False

        async def sample_coro():
            nonlocal entered_during_coro
            if client.entered == 1 and client.exited == 0:
                entered_during_coro = True
            return 42

        task = dock._spawn(sample_coro())
        assert isinstance(task, asyncio.Task)
        res = await task
        assert res == 42
        assert entered_during_coro is True
        assert client.entered == 1
        assert client.exited == 1

    asyncio.run(_test())
