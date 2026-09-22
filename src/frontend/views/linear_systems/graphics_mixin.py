"""Mixin de visualización gráfica 2D y 3D (Plotly) para Sistemas Lineales."""
import logging
from nicegui import ui
from src.frontend.helpers import to_float
from src.frontend.theme import (
    CHART_PALETTE,
    CHART_MARKER_LIGHT,
    CHART_MARKER_BORDER,
    CHART_GRID_COLOR,
    CHART_ZERO_COLOR,
    CHART_FONT_COLOR,
)

logger = logging.getLogger(__name__)


class LinearSystemsGraphicsMixin:
    """Renderiza planos, rectas e intersecciones de soluciones en 2D y 3D con Plotly."""

    async def _tema_actual(self) -> str:
        try:
            return await ui.run_javascript(
                "document.documentElement.getAttribute('data-theme') || 'papel'",
                timeout=3.0,
            ) or 'papel'
        except Exception:
            return 'papel'

    async def render_graphics(self, matrix_A, vector_b, respuesta):
        m = len(matrix_A)
        n = len(matrix_A[0]) if m > 0 else 0

        if n < 2 or n > 3:
            ui.label(f'Visualización gráfica no disponible para {n} dimensiones.').classes('text-sec text-sm italic mt-4')
            return

        with ui.expansion('Visualización Gráfica', icon='insights').classes('w-full panel-card mt-4').props('header-class="font-bold text-main" default-opened'):
            try:
                import plotly.graph_objects as go
            except ImportError as e:
                logger.warning("No se pudo cargar el módulo de gráficos (plotly)", exc_info=e)
                ui.label('No se pudo cargar el módulo de gráficos (plotly). Contactá al administrador o instalá la dependencia con "pip install plotly".').classes('text-warning')
                return

            def _linspace(start, stop, num):
                if num == 1:
                    return [start]
                step = (stop - start) / (num - 1)
                return [start + i * step for i in range(num)]

            def _meshgrid(x, y):
                X = [[x_val for x_val in x] for _ in y]
                Y = [[y_val for _ in x] for y_val in y]
                return X, Y

            fig = go.Figure()
            colors = CHART_PALETTE
            omitidas = 0

            if n == 2:
                x_vals = _linspace(-10, 10, 100)
                for i in range(m):
                    try:
                        a, b, c = to_float(matrix_A[i][0]), to_float(matrix_A[i][1]), to_float(vector_b[i])
                    except ValueError:
                        omitidas += 1
                        continue

                    if abs(b) > 1e-6:
                        y_vals = [(c - a * x) / b for x in x_vals]
                        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name=f'Eq {i+1}', line=dict(color=colors[i % len(colors)], width=3)))
                    elif abs(a) > 1e-6:
                        x_line = [c / a, c / a]
                        y_line = [-10, 10]
                        fig.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines', name=f'Eq {i+1}', line=dict(color=colors[i % len(colors)], width=3)))

                if respuesta.get("status") == "UNIQUE_SOLUTION" and respuesta.get("solution"):
                    try:
                        sol_f = [to_float(s) for s in respuesta["solution"]]
                        fig.add_trace(go.Scatter(
                            x=[sol_f[0]], y=[sol_f[1]], mode='markers', name='Solución',
                            marker=dict(color=CHART_MARKER_LIGHT, size=12, line=dict(color=CHART_MARKER_BORDER, width=2))
                        ))
                    except ValueError:
                        pass

                theme = await self._tema_actual()
                font_color = CHART_FONT_COLOR.get(theme, '#23262E')

                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=font_color),
                    margin=dict(l=20, r=20, t=20, b=20),
                    xaxis=dict(gridcolor=CHART_GRID_COLOR, zerolinecolor=CHART_ZERO_COLOR),
                    yaxis=dict(gridcolor=CHART_GRID_COLOR, zerolinecolor=CHART_ZERO_COLOR)
                )

            elif n == 3:
                x = _linspace(-10, 10, 10)
                y = _linspace(-10, 10, 10)
                X, Y = _meshgrid(x, y)

                for i in range(m):
                    try:
                        a, b, c_z, d = to_float(matrix_A[i][0]), to_float(matrix_A[i][1]), to_float(matrix_A[i][2]), to_float(vector_b[i])
                    except ValueError:
                        omitidas += 1
                        continue

                    if abs(c_z) > 1e-6:
                        Z = [[(d - a * X[r][c] - b * Y[r][c]) / c_z for c in range(len(X[0]))] for r in range(len(X))]
                        fig.add_trace(go.Surface(z=Z, x=X, y=Y, name=f'Eq {i+1}', showscale=False, opacity=0.7, colorscale=[[0, colors[i % len(colors)]], [1, colors[i % len(colors)]]]))
                    elif abs(b) > 1e-6:
                        Z_mesh = _linspace(-10, 10, 10)
                        X_mesh, Z_grid = _meshgrid(x, Z_mesh)
                        Y_grid = [[(d - a * X_mesh[r][c]) / b for c in range(len(X_mesh[0]))] for r in range(len(X_mesh))]
                        fig.add_trace(go.Surface(z=Z_grid, x=X_mesh, y=Y_grid, name=f'Eq {i+1}', showscale=False, opacity=0.7, colorscale=[[0, colors[i % len(colors)]], [1, colors[i % len(colors)]]]))
                    elif abs(a) > 1e-6:
                        Z_mesh = _linspace(-10, 10, 10)
                        Y_mesh, Z_grid = _meshgrid(y, Z_mesh)
                        X_grid = [[(d - b * Y_mesh[r][c]) / a for c in range(len(Y_mesh[0]))] for r in range(len(Y_mesh))]
                        fig.add_trace(go.Surface(z=Z_grid, x=X_grid, y=Y_mesh, name=f'Eq {i+1}', showscale=False, opacity=0.7, colorscale=[[0, colors[i % len(colors)]], [1, colors[i % len(colors)]]]))

                if respuesta.get("status") == "UNIQUE_SOLUTION" and respuesta.get("solution"):
                    try:
                        sol_f = [to_float(s) for s in respuesta["solution"]]
                        fig.add_trace(go.Scatter3d(
                            x=[sol_f[0]], y=[sol_f[1]], z=[sol_f[2]], mode='markers', name='Solución',
                            marker=dict(color=CHART_MARKER_LIGHT, size=8, line=dict(color=CHART_MARKER_BORDER, width=2))
                        ))
                    except ValueError:
                        pass

                theme = await self._tema_actual()
                font_color = CHART_FONT_COLOR.get(theme, '#23262E')

                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=font_color),
                    margin=dict(l=0, r=0, t=0, b=0),
                    scene=dict(
                        xaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor=CHART_GRID_COLOR),
                        yaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor=CHART_GRID_COLOR),
                        zaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor=CHART_GRID_COLOR)
                    )
                )

            ui.plotly(fig).classes('w-full h-[400px]')
            if omitidas > 0:
                ui.label(f'{omitidas} ecuación(es) no se pudieron graficar por tener valores no numéricos.').classes('text-warning text-sm')
            ui.run_javascript("window.updatePlotlyThemeWhenReady(5000);")
