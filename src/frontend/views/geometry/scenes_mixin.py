"""Mixin de escenas Plotly para el Visualizador Geométrico."""
from __future__ import annotations

import json
import logging
from nicegui import ui

logger = logging.getLogger(__name__)


class GeometryScenesMixin:
    """Renderiza figuras Plotly para las tres escenas del Visualizador."""

    async def _tema_actual(self) -> str:
        try:
            return await ui.run_javascript(
                "document.documentElement.getAttribute('data-theme') || 'papel'",
                timeout=3.0,
            ) or 'papel'
        except Exception:
            return 'papel'

    async def _build_figure(self, result: dict, scene: str):
        """Build and display the Plotly figure for the given scene."""
        try:
            if scene == 'rectas-planos':
                from ._scenes import build_lines_planes_figure
                theme = await self._tema_actual()
                fig = build_lines_planes_figure(result, theme=theme)
            elif scene == 'vectores':
                from ._scenes import build_vectors_figure
                theme = await self._tema_actual()
                frame_idx = getattr(self, '_current_frame_index', None)
                fig = build_vectors_figure(result, theme=theme, frame_index=frame_idx)
            elif scene == 'combinacion':
                from ._scenes import build_combination_figure
                theme = await self._tema_actual()
                fig = build_combination_figure(result, theme=theme)
            else:
                return
        except ImportError:
            with self.figure_container:
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-error w-fit'):
                    ui.icon('close', size='sm')
                    ui.label('No se pudo cargar el módulo de gráficos (plotly).').classes('font-bold')
            return

        if self.figure_container:
            self.figure_container.clear()
            with self.figure_container:
                wrap_id = f"geo-fig-{id(self)}"
                with ui.element('div').props(f'id="{wrap_id}"').classes('geo-figure w-full'):
                    self._plotly_element = ui.plotly(fig).classes('w-full h-full')

                # Register frames for vectors scene
                if scene == 'vectores' and result.get("frames"):
                    frames_json = json.dumps(result["frames"])
                    ui.run_javascript(f'scalarisGeo.register("{wrap_id}", {frames_json});')

    def _render_summary(self, result: dict, scene: str):
        """Render textual summary below the figure."""
        if not self.summary_container:
            return

        self.summary_container.clear()

        with self.summary_container:
            if scene == 'rectas-planos':
                self._render_lines_summary(result)
            elif scene == 'vectores':
                self._render_vectors_summary(result)
            elif scene == 'combinacion':
                self._render_combination_summary(result)

    def _render_lines_summary(self, result: dict):
        """Render summary for lines/planes scene."""
        sol_status = result.get("solution_status", "")
        sol_set = result.get("set")
        pending = result.get("pending_param", False)
        n = result.get("n", 2)
        equations = result.get("equations", [])
        flags = result.get("flags", [])

        # Equations in MathJax
        if equations:
            eq_ids = []
            with ui.element('div').classes('math-scroll-container').props('role="img" aria-label="Ecuaciones del sistema"'):
                for eq in equations:
                    eq_id = f"geo-eq-{id(eq)}"
                    eq_ids.append(eq_id)
                    coeffs = eq.get("coeffs_exact", [])
                    b_val = eq.get("b_exact", "0")
                    var_names = ["x", "y", "z"][:n]

                    # Build LaTeX
                    terms = []
                    for j, (c, v) in enumerate(zip(coeffs, var_names)):
                        if c == "0":
                            continue
                        if c == "1":
                            terms.append(v)
                        elif c == "-1":
                            terms.append(f"-{v}")
                        else:
                            terms.append(f"{c}{v}")
                    lhs = " + ".join(terms).replace("+ -", "- ") if terms else "0"
                    latex = f"{lhs} = {b_val}"
                    ui.html(f'<div id="{eq_id}" class="math-label text-sm mb-1">$$ {latex} $$</div>')

            if eq_ids:
                ui.run_javascript(f"typesetMathWhenReady({json.dumps(eq_ids)});")

        # Solution status
        if sol_status == "UNIQUE_SOLUTION" and sol_set and sol_set.get("point_exact"):
            exact = sol_set["point_exact"]
            point_str = ", ".join(exact)
            with ui.element('div').classes('geo-summary mt-2').style('overflow-wrap: anywhere;'):
                ui.label(f"Solución: ({point_str})").classes('font-bold text-sm text-main')

        elif sol_status == "NO_SOLUTION":
            msg = "El sistema no tiene solución"
            if "parallel" in flags and n == 2:
                msg = "Las rectas son paralelas y no se intersectan"
            with ui.element('div').classes('geo-summary mt-2'):
                ui.label(msg).classes('font-bold text-sm text-main')

        elif sol_status == "INFINITE_SOLUTIONS":
            with ui.element('div').classes('geo-notice mt-2'):
                ui.label("Este sistema tiene infinitas soluciones. Por ahora solo dibujamos las ecuaciones.").classes('text-sm text-sec')

    def _render_vectors_summary(self, result: dict):
        """Render summary for vectors scene."""
        u_data = result.get("u", {})
        v_data = result.get("v", {})
        u_exact = u_data.get("exact", [])
        v_exact = v_data.get("exact", [])

        with ui.element('div').classes('math-scroll-container').props('role="img" aria-label="Vectores u y v"'):
            u_str = ", ".join(u_exact)
            v_str = ", ".join(v_exact)
            summary_id = f"geo-vec-summary-{id(self)}"
            ui.html(f'<div id="{summary_id}" class="math-label text-sm">$$ \\mathbf{{u}} = ({u_str}), \\quad \\mathbf{{v}} = ({v_str}) $$</div>')
            ui.run_javascript(f'typesetMathWhenReady(["{summary_id}"]);')

    def _render_combination_summary(self, result: dict):
        """Render summary for combination scene."""
        b_data = result.get("b", {})
        b_exact = b_data.get("exact", [])
        vectors = result.get("vectors", [])
        sol_status = result.get("solution_status", "")

        parts = []
        for vi, vec in enumerate(vectors):
            ve = vec.get("exact", [])
            parts.append(f"\\mathbf{{v}}_{vi+1} = ({', '.join(ve)})")

        with ui.element('div').classes('math-scroll-container').props('role="img" aria-label="Combinación lineal"'):
            b_str = ", ".join(b_exact)
            summary_id = f"geo-comb-summary-{id(self)}"
            vecs_tex = ", \\quad ".join(parts)
            ui.html(f'<div id="{summary_id}" class="math-label text-sm">$$ \\mathbf{{b}} = ({b_str}), \\quad {vecs_tex} $$</div>')
            ui.run_javascript(f'typesetMathWhenReady(["{summary_id}"]);')

        if sol_status == "UNIQUE":
            chain = result.get("chain", [])
            if chain:
                last = chain[-1]
                point_str = ", ".join(last.get("exact", []))
                with ui.element('div').classes('geo-summary mt-2').style('overflow-wrap: anywhere;'):
                    ui.label(f"b se alcanza en ({point_str})").classes('font-bold text-sm text-main')
        elif sol_status == "INFINITE":
            with ui.element('div').classes('geo-notice mt-2'):
                ui.label("b es combinación lineal de los vectores, pero la representación no es única.").classes('text-sm text-sec')
        elif sol_status == "NO_SOLUTION":
            with ui.element('div').classes('geo-notice mt-2'):
                ui.label("b no pertenece al span de los vectores dados.").classes('text-sm text-sec')
