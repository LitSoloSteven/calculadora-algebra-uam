"""Constructores puros de figuras Plotly para el Visualizador Geométrico.

Cada función recibe datos ya procesados por el controller y devuelve
un go.Figure listo para ui.plotly(). Importan plotly dentro de la función
para que la vista pueda atrapar ImportError.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from src.frontend.theme import (
    CHART_PALETTE,
    CHART_MARKER_LIGHT,
    CHART_MARKER_BORDER,
    CHART_GRID_COLOR,
    CHART_ZERO_COLOR,
    CHART_FONT_COLOR,
)


def _layout_common_2d(fig, *, axis_range: list[float], font_color: str, uirevision: str = "lines"):
    """Apply common 2D layout settings."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=font_color, family='Space Grotesk, sans-serif'),
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(
            gridcolor=CHART_GRID_COLOR,
            zerolinecolor=CHART_ZERO_COLOR,
            range=axis_range,
            scaleanchor='y',
            scaleratio=1,
            constrain='domain',
        ),
        yaxis=dict(
            gridcolor=CHART_GRID_COLOR,
            zerolinecolor=CHART_ZERO_COLOR,
            range=axis_range,
        ),
        uirevision=uirevision,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
        ),
    )


def _layout_common_3d(fig, *, axis_range: list[float], font_color: str, uirevision: str = "planes"):
    """Apply common 3D layout settings."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=font_color, family='Space Grotesk, sans-serif'),
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor=CHART_GRID_COLOR, range=axis_range),
            yaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor=CHART_GRID_COLOR, range=axis_range),
            zaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor=CHART_GRID_COLOR, range=axis_range),
            aspectmode='cube',
        ),
        uirevision=uirevision,
    )


def build_lines_planes_figure(result: dict, *, theme: str = 'papel') -> Any:
    """Build a Plotly figure for lines/planes visualization.

    Args:
        result: dict from GeometryController.process_lines_planes()
        theme: current theme name
    """
    import plotly.graph_objects as go

    fig = go.Figure()
    equations = result.get("equations", [])
    n = result.get("n", 2)
    axis_range = result.get("range", [-5, 5])
    sol_set = result.get("set")
    colors = CHART_PALETTE
    font_color = CHART_FONT_COLOR.get(theme, '#23262E')

    if n == 2:
        # Draw lines
        for eq in equations:
            idx = eq["index"]
            kind = eq["kind"]
            coeffs = eq["coeffs"]
            b_val = eq["b"]
            color = colors[idx % len(colors)]
            name = f"Ecuación {idx + 1}"

            if kind in ("trivial", "contradiction"):
                continue

            a, b_coeff = coeffs[0], coeffs[1]
            if b_coeff is not None and abs(b_coeff) > 1e-12:
                # y = (b_val - a*x) / b_coeff
                x0, x1 = axis_range
                y0 = (b_val - a * x0) / b_coeff
                y1 = (b_val - a * x1) / b_coeff
                fig.add_trace(go.Scatter(
                    x=[x0, x1], y=[y0, y1],
                    mode='lines', name=name,
                    line=dict(color=color, width=3),
                ))
            elif a is not None and abs(a) > 1e-12:
                # Vertical line x = b_val / a
                x_line = b_val / a
                fig.add_trace(go.Scatter(
                    x=[x_line, x_line], y=axis_range,
                    mode='lines', name=name,
                    line=dict(color=color, width=3),
                ))

        # Draw solution point
        if sol_set and sol_set.get("kind") == "POINT" and sol_set.get("point"):
            pt = sol_set["point"]
            exact = sol_set.get("point_exact", [])
            hover_text = f"({', '.join(exact)})" if exact else f"({pt[0]}, {pt[1]})"
            fig.add_trace(go.Scatter(
                x=[pt[0]], y=[pt[1]],
                mode='markers', name='Solución',
                marker=dict(
                    color=CHART_MARKER_LIGHT, size=12,
                    line=dict(color=CHART_MARKER_BORDER, width=2),
                ),
                hovertext=hover_text,
                hoverinfo='text',
            ))

        _layout_common_2d(fig, axis_range=axis_range, font_color=font_color, uirevision="lines")

    elif n == 3:
        # Draw planes
        def _linspace(start, stop, num):
            if num == 1:
                return [start]
            step = (stop - start) / (num - 1)
            return [start + i * step for i in range(num)]

        def _meshgrid(x, y):
            X = [[x_val for x_val in x] for _ in y]
            Y = [[y_val for _ in x] for y_val in y]
            return X, Y

        grid_size = 12
        x_vals = _linspace(axis_range[0], axis_range[1], grid_size)
        y_vals = _linspace(axis_range[0], axis_range[1], grid_size)

        for eq in equations:
            idx = eq["index"]
            kind = eq["kind"]
            if kind in ("trivial", "contradiction"):
                continue

            coeffs = eq["coeffs"]
            b_val = eq["b"]
            color = colors[idx % len(colors)]
            name = f"Ecuación {idx + 1}"

            a, b_coeff, c_coeff = coeffs[0], coeffs[1], coeffs[2]

            # Resolve by the axis with largest |coefficient|
            abs_coeffs = [abs(c) if c is not None else 0 for c in [a, b_coeff, c_coeff]]
            max_idx = abs_coeffs.index(max(abs_coeffs))

            if max_idx == 2 and abs(c_coeff) > 1e-12:
                X, Y = _meshgrid(x_vals, y_vals)
                Z = [[(b_val - a * X[r][c] - b_coeff * Y[r][c]) / c_coeff
                      for c in range(grid_size)] for r in range(grid_size)]
                fig.add_trace(go.Surface(
                    z=Z, x=X, y=Y, name=name, showscale=False, opacity=0.7,
                    colorscale=[[0, color], [1, color]],
                ))
            elif max_idx == 1 and abs(b_coeff) > 1e-12:
                z_vals = _linspace(axis_range[0], axis_range[1], grid_size)
                X, Z = _meshgrid(x_vals, z_vals)
                Y = [[(b_val - a * X[r][c] - c_coeff * Z[r][c]) / b_coeff
                      for c in range(grid_size)] for r in range(grid_size)]
                fig.add_trace(go.Surface(
                    z=Z, x=X, y=Y, name=name, showscale=False, opacity=0.7,
                    colorscale=[[0, color], [1, color]],
                ))
            elif abs(a) > 1e-12:
                z_vals = _linspace(axis_range[0], axis_range[1], grid_size)
                Y, Z = _meshgrid(y_vals, z_vals)
                X = [[(b_val - b_coeff * Y[r][c] - c_coeff * Z[r][c]) / a
                      for c in range(grid_size)] for r in range(grid_size)]
                fig.add_trace(go.Surface(
                    z=Z, x=X, y=Y, name=name, showscale=False, opacity=0.7,
                    colorscale=[[0, color], [1, color]],
                ))

        # Draw solution point 3D
        if sol_set and sol_set.get("kind") == "POINT" and sol_set.get("point"):
            pt = sol_set["point"]
            exact = sol_set.get("point_exact", [])
            hover_text = f"({', '.join(exact)})" if exact else f"({pt[0]}, {pt[1]}, {pt[2]})"
            fig.add_trace(go.Scatter3d(
                x=[pt[0]], y=[pt[1]], z=[pt[2]],
                mode='markers', name='Solución',
                marker=dict(
                    color=CHART_MARKER_LIGHT, size=8,
                    line=dict(color=CHART_MARKER_BORDER, width=2),
                ),
                hovertext=hover_text,
                hoverinfo='text',
            ))

        _layout_common_3d(fig, axis_range=axis_range, font_color=font_color, uirevision="planes")

    return fig


def build_vectors_figure(result: dict, *, theme: str = 'papel', frame_index: int | None = None) -> Any:
    """Build a Plotly figure for vectors visualization (u, v, u+v).

    Args:
        result: dict from GeometryController.process_vectors()
        theme: current theme name
        frame_index: if given, use this frame's data instead of static
    """
    import plotly.graph_objects as go

    fig = go.Figure()
    n = result.get("n", 2)
    static = result.get("static", {})
    axis_range = result.get("range", [-5, 5])
    font_color = CHART_FONT_COLOR.get(theme, '#23262E')
    colors = CHART_PALETTE

    u = static.get("u", [])
    v = static.get("v", [])
    u_plus_v = static.get("u_plus_v", [])

    # Get frame data if specified
    frames = result.get("frames", [])
    if frame_index is not None and 0 <= frame_index < len(frames):
        frame = frames[frame_index]
        ku = frame.get("ku", u)
        ku_plus_v = frame.get("ku_plus_v", u_plus_v)
        k_label = frame.get("k_exact", "k")
    else:
        ku = u
        ku_plus_v = u_plus_v
        k_label = "1"

    origin = [0] * n

    if n == 2:
        # Arrow: u
        fig.add_trace(go.Scatter(
            x=[0, ku[0]], y=[0, ku[1]],
            mode='lines+markers', name=f'k·u (k={k_label})',
            line=dict(color=colors[0], width=3),
            marker=dict(size=[0, 10], symbol=['circle', 'arrow'], angleref='previous'),
        ))
        # Arrow: v (from origin)
        fig.add_trace(go.Scatter(
            x=[0, v[0]], y=[0, v[1]],
            mode='lines+markers', name='v',
            line=dict(color=colors[1], width=3),
            marker=dict(size=[0, 10], symbol=['circle', 'arrow'], angleref='previous'),
        ))
        # Arrow: k·u + v
        fig.add_trace(go.Scatter(
            x=[0, ku_plus_v[0]], y=[0, ku_plus_v[1]],
            mode='lines+markers', name=f'k·u + v',
            line=dict(color=colors[2], width=3, dash='dash'),
            marker=dict(size=[0, 10], symbol=['circle', 'arrow'], angleref='previous'),
        ))

        _layout_common_2d(fig, axis_range=axis_range, font_color=font_color, uirevision="vectors")

    elif n == 3:
        def _arrow_3d(start, end, name, color, dash=None):
            line_kwargs = dict(color=color, width=4)
            if dash:
                line_kwargs['dash'] = dash
            fig.add_trace(go.Scatter3d(
                x=[start[0], end[0]], y=[start[1], end[1]], z=[start[2], end[2]],
                mode='lines', name=name,
                line=line_kwargs,
            ))
            fig.add_trace(go.Scatter3d(
                x=[end[0]], y=[end[1]], z=[end[2]],
                mode='markers', name=name, showlegend=False,
                marker=dict(size=5, color=color),
            ))

        _arrow_3d(origin, ku, f'k·u (k={k_label})', colors[0])
        _arrow_3d(origin, v, 'v', colors[1])
        _arrow_3d(origin, ku_plus_v, 'k·u + v', colors[2], dash='dash')

        _layout_common_3d(fig, axis_range=axis_range, font_color=font_color, uirevision="vectors")

    return fig


def build_combination_figure(result: dict, *, theme: str = 'papel') -> Any:
    """Build a Plotly figure for linear combination visualization.

    Args:
        result: dict from GeometryController.process_combination()
        theme: current theme name
    """
    import plotly.graph_objects as go

    fig = go.Figure()
    n = result.get("n", 2)
    axis_range = result.get("range", [-5, 5])
    font_color = CHART_FONT_COLOR.get(theme, '#23262E')
    colors = CHART_PALETTE

    b_data = result.get("b", {})
    b = b_data.get("float", [])
    vectors = result.get("vectors", [])
    chain = result.get("chain")
    b_outside = result.get("b_outside_span", False)
    origin = [0] * n

    if n == 2:
        # Draw each vector from origin
        for vi, vec in enumerate(vectors):
            vf = vec.get("float", [])
            fig.add_trace(go.Scatter(
                x=[0, vf[0]], y=[0, vf[1]],
                mode='lines+markers', name=f'v_{vi+1}',
                line=dict(color=colors[vi % len(colors)], width=2, dash='dot'),
                marker=dict(size=[0, 8], symbol=['circle', 'arrow'], angleref='previous'),
            ))

        # Draw b
        marker_color = CHART_MARKER_LIGHT if not b_outside else colors[len(vectors) % len(colors)]
        fig.add_trace(go.Scatter(
            x=[b[0]], y=[b[1]],
            mode='markers', name='b',
            marker=dict(color=marker_color, size=12, line=dict(color=CHART_MARKER_BORDER, width=2)),
        ))

        # Draw chain if UNIQUE
        if chain:
            prev = [0, 0]
            for ci, cp in enumerate(chain):
                pt = cp.get("float", [])
                fig.add_trace(go.Scatter(
                    x=[prev[0], pt[0]], y=[prev[1], pt[1]],
                    mode='lines', name=cp.get("label", ""),
                    line=dict(color=colors[ci % len(colors)], width=3),
                ))
                prev = pt

        _layout_common_2d(fig, axis_range=axis_range, font_color=font_color, uirevision="combination")

    elif n == 3:
        for vi, vec in enumerate(vectors):
            vf = vec.get("float", [])
            fig.add_trace(go.Scatter3d(
                x=[0, vf[0]], y=[0, vf[1]], z=[0, vf[2]],
                mode='lines', name=f'v_{vi+1}',
                line=dict(color=colors[vi % len(colors)], width=3, dash='dot'),
            ))

        fig.add_trace(go.Scatter3d(
            x=[b[0]], y=[b[1]], z=[b[2]],
            mode='markers', name='b',
            marker=dict(color=CHART_MARKER_LIGHT, size=6, line=dict(color=CHART_MARKER_BORDER, width=2)),
        ))

        if chain:
            prev = [0, 0, 0]
            for ci, cp in enumerate(chain):
                pt = cp.get("float", [])
                fig.add_trace(go.Scatter3d(
                    x=[prev[0], pt[0]], y=[prev[1], pt[1]], z=[prev[2], pt[2]],
                    mode='lines', name=cp.get("label", ""),
                    line=dict(color=colors[ci % len(colors)], width=4),
                ))
                prev = pt

        _layout_common_3d(fig, axis_range=axis_range, font_color=font_color, uirevision="combination")

    return fig
