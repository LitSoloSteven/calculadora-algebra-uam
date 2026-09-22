"""Registro de rutas y páginas públicas de Scalaris."""
from fastapi.responses import RedirectResponse
from nicegui import app, ui
from src.frontend.theme import setup_theme


def register_routes():
    """Registra todas las redirecciones y páginas de la aplicación."""

    @app.get('/')
    def index_redirect():
        return RedirectResponse('/sistemas-lineales')

    @app.get('/gauss')
    def redirect_gauss():
        return RedirectResponse('/sistemas-lineales?method=gauss')

    @app.get('/gauss-jordan')
    def redirect_gauss_jordan():
        return RedirectResponse('/sistemas-lineales?method=gauss-jordan')

    @app.get('/ia')
    def vista_ia_redirect():
        return RedirectResponse('/sistemas-lineales')

    @ui.page('/sistemas-lineales')
    def linear_systems_page(method: str = 'gauss'):
        if method not in ('gauss', 'gauss-jordan'):
            method = 'gauss'
        from src.frontend.views.linear_systems.view_linear_systems import LinearSystemsUI
        setup_theme()
        app_ui = LinearSystemsUI(initial_method=method)
        app_ui.build()

    @ui.page('/operaciones-matrices')
    def matrix_ops_page():
        from src.frontend.views.matrix_ops.view_matrix_ops import MatrixOpsUI
        setup_theme()
        app_ui = MatrixOpsUI()
        app_ui.build()

    @ui.page('/vectores')
    def vector_ops_page():
        from src.frontend.views.vector_ops.view_vector_ops import VectorOpsUI
        setup_theme()
        app_ui = VectorOpsUI()
        app_ui.build()

    @ui.page('/conversor')
    def conversor_page():
        from src.frontend.views.numeric_systems.view_numeric_systems import NumericSystemsUI
        setup_theme()
        app_ui = NumericSystemsUI()
        app_ui.build()
