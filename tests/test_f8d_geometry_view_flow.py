import asyncio
from unittest.mock import MagicMock, AsyncMock
from nicegui import ui, run
from src.frontend.views.geometry.view_geometry import GeometryUI


def test_update_figure_scratch_failure(monkeypatch):
    async def _test():
        view = GeometryUI()
        view.scene = 'rectas-planos'
        mock_ai_panel = MagicMock()
        view.ai_panel = mock_ai_panel

        # Mock payload
        monkeypatch.setattr(view, "_build_payload", lambda: {"matrix_A": [["1", "0"], ["0", "1"]], "vector_b": ["1", "2"]})

        # Mock ui.run_javascript and run.io_bound
        monkeypatch.setattr(ui, "run_javascript", lambda *args, **kwargs: None)
        
        async def mock_io_bound(fn, *args, **kwargs):
            return fn(*args, **kwargs)
        monkeypatch.setattr(run, "io_bound", mock_io_bound)

        # Mock _get_figure_only to return None (failure)
        monkeypatch.setattr(view, "_get_figure_only", AsyncMock(return_value=None))

        render_summary_mock = MagicMock()
        monkeypatch.setattr(view, "_render_summary", render_summary_mock)
        build_slider_mock = MagicMock()
        monkeypatch.setattr(view, "_build_slider", build_slider_mock)
        render_error_mock = MagicMock()
        monkeypatch.setattr(view, "_render_error", render_error_mock)

        await view._update_figure()

        assert view.last_result is None
        assert view.last_payload_hash is None
        assert view._fig_key is None
        assert view._plotly_element is None
        assert view._first_draw is True
        render_summary_mock.assert_not_called()
        build_slider_mock.assert_not_called()
        render_error_mock.assert_called_once()
        mock_ai_panel.schedule_context_refresh.assert_called_once()

    asyncio.run(_test())


def test_update_figure_reuse_failure(monkeypatch):
    async def _test():
        view = GeometryUI()
        view.scene = 'rectas-planos'
        view._first_draw = False
        mock_plotly = MagicMock()
        view._plotly_element = mock_plotly
        view._fig_key = ('rectas-planos', 2)
        view.last_payload_hash = 9999
        view.last_result = {'status': 'SUCCESS', 'n': 2}
        mock_ai_panel = MagicMock()
        view.ai_panel = mock_ai_panel

        # Mock payload with new data
        monkeypatch.setattr(view, "_build_payload", lambda: {"matrix_A": [["2", "0"], ["0", "2"]], "vector_b": ["2", "4"]})

        monkeypatch.setattr(ui, "run_javascript", lambda *args, **kwargs: None)
        
        async def mock_io_bound(fn, *args, **kwargs):
            return fn(*args, **kwargs)
        monkeypatch.setattr(run, "io_bound", mock_io_bound)

        # Mock _get_figure_only to return None on update
        monkeypatch.setattr(view, "_get_figure_only", AsyncMock(return_value=None))

        render_summary_mock = MagicMock()
        monkeypatch.setattr(view, "_render_summary", render_summary_mock)
        build_slider_mock = MagicMock()
        monkeypatch.setattr(view, "_build_slider", build_slider_mock)
        render_error_mock = MagicMock()
        monkeypatch.setattr(view, "_render_error", render_error_mock)

        await view._update_figure()

        assert view.last_result is None
        assert view.last_payload_hash is None
        assert view._fig_key is None
        assert view._plotly_element is None
        assert view._first_draw is True
        render_summary_mock.assert_not_called()
        build_slider_mock.assert_not_called()
        render_error_mock.assert_called_once()
        mock_ai_panel.schedule_context_refresh.assert_called_once()

    asyncio.run(_test())


def test_build_figure_return_bool(monkeypatch):
    async def _test():
        view = GeometryUI()
        view.figure_container = MagicMock()

        # Case 1: fig is None -> returns False
        monkeypatch.setattr(view, "_get_figure_only", AsyncMock(return_value=None))
        monkeypatch.setattr(ui, "run_javascript", lambda *args, **kwargs: None)
        render_error_mock = MagicMock()
        monkeypatch.setattr(view, "_render_error", render_error_mock)

        res = await view._build_figure({}, "rectas-planos")
        assert res is False
        render_error_mock.assert_called_once()

        # Case 2: fig is valid -> returns True
        mock_fig = MagicMock()
        monkeypatch.setattr(view, "_get_figure_only", AsyncMock(return_value=mock_fig))
        monkeypatch.setattr(ui, "plotly", lambda fig: MagicMock())
        monkeypatch.setattr(ui, "element", lambda *args, **kwargs: MagicMock())

        res2 = await view._build_figure({}, "rectas-planos")
        assert res2 is True

    asyncio.run(_test())
