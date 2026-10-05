"""Registro de rutas y páginas públicas de Scalaris."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui, Client

from src.frontend import navigation
from src.frontend.navigation import (
    legacy_redirects,
    redirect_location,
    route_of,
    tool_by_id,
    HUB_ROUTE,
    HUB_PAGE_TITLE,
)
from src.frontend.theme import setup_theme


def register_legacy_redirects(target_app) -> None:
    """Registra los manejadores HTTP GET para las rutas legacy de Scalaris.

    Acepta una instancia de FastAPI o el objeto `app` de NiceGUI.
    Cada ruta calcula la redirección con preservación de parámetros query
    y devuelve un estado HTTP 301 o 302 explícito según LegacyRedirect.permanent.
    """
    for rule in legacy_redirects():
        def _make_handler(current_rule):
            async def _handler(request: Request) -> RedirectResponse:
                incoming_items = request.query_params.multi_items()
                target_url = redirect_location(current_rule, incoming_items)
                status_code = 301 if current_rule.permanent else 302
                return RedirectResponse(target_url, status_code=status_code)
            return _handler

        target_app.get(rule.path)(_make_handler(rule))


def register_routes() -> None:
    """Registra todas las redirecciones legacy y páginas canónicas de la aplicación."""
    register_legacy_redirects(app)

    @ui.page(route_of("sistemas"), title=tool_by_id("sistemas").page_title)
    def linear_systems_page(method: str = "gauss", handoff: str = ""):
        if method not in ("gauss", "gauss-jordan"):
            method = "gauss"
        from src.frontend.views.linear_systems.view_linear_systems import LinearSystemsUI
        setup_theme()
        app_ui = LinearSystemsUI(initial_method=method)
        app_ui.build(handoff_token=handoff)

    @ui.page(route_of("vectores"), title=tool_by_id("vectores").page_title)
    def vector_ops_page():
        from src.frontend.views.vector_ops.view_vector_ops import VectorOpsUI
        setup_theme()
        app_ui = VectorOpsUI()
        app_ui.build()

    @ui.page(route_of("matrices"), title=tool_by_id("matrices").page_title)
    def matrix_ops_page():
        from src.frontend.views.matrix_ops.view_matrix_ops import MatrixOpsUI
        setup_theme()
        app_ui = MatrixOpsUI()
        app_ui.build()

    @ui.page(route_of("inversa"), title=tool_by_id("inversa").page_title)
    def matrix_inverse_page(handoff: str = ""):
        from src.frontend.views.inverse_ops.view_inverse_ops import InverseOpsUI
        setup_theme()
        app_ui = InverseOpsUI()
        app_ui.build(handoff_token=handoff)

    @ui.page(route_of("visualizador"), title=tool_by_id("visualizador").page_title)
    def geometry_page(escena: str = "rectas-planos", handoff: str = ""):
        from src.frontend.views.geometry.view_geometry import GeometryUI
        setup_theme()
        app_ui = GeometryUI()
        app_ui.build(escena=escena, handoff_token=handoff)

    @ui.page(route_of("bases"), title=tool_by_id("bases").page_title)
    def conversor_page():
        from src.frontend.views.numeric_systems.view_numeric_systems import NumericSystemsUI
        setup_theme()
        app_ui = NumericSystemsUI()
        app_ui.build()

    @ui.page(route_of("romanos"), title=tool_by_id("romanos").page_title)
    def roman_calculator_page():
        from src.frontend.views.numeric_systems.view_roman_calculator import RomanCalculatorUI
        setup_theme()
        app_ui = RomanCalculatorUI()
        app_ui.build()

    if navigation.HUB_ENABLED:
        @ui.page(HUB_ROUTE, title=HUB_PAGE_TITLE)
        async def hub_page(client: Client, glosa: str = ''):
            from src.frontend.views.hub.view_hub import HubUI
            setup_theme()
            app_ui = HubUI(glosa_open=(glosa == '1'))
            await app_ui.build(client)