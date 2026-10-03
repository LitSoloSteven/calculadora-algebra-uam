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

    async def _get_figure_only(self, result: dict, scene: str):
        try:
            if scene == 'rectas-planos':
                from ._scenes import build_lines_planes_figure
                theme = await self._tema_actual()
                return build_lines_planes_figure(result, theme=theme)
            elif scene == 'vectores':
                from ._scenes import build_vectors_figure
                theme = await self._tema_actual()
                frame_idx = getattr(self, '_current_frame_index', None)
                return build_vectors_figure(result, theme=theme, frame_idx=frame_idx)
            elif scene == 'combinacion':
                from ._scenes import build_combination_figure
                theme = await self._tema_actual()
                return build_combination_figure(result, theme=theme)
        except Exception:
            pass
        return None

    async def _build_figure(self, result: dict, scene: str):
        """Build and display the Plotly figure for the given scene."""
        try:
            fig = await self._get_figure_only(result, scene)
            if fig is None:
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

                    latex = eq.get("latex", f"0 = {b_val}")
                    ui.html(f'<div id="{eq_id}" class="math-label text-sm mb-1">$$ {latex} $$</div>')

            if eq_ids:
                ui.run_javascript(f"typesetMathWhenReady({json.dumps(eq_ids)});")

        # Solution status
        if sol_status == "UNIQUE_SOLUTION" and sol_set and sol_set.get("point_exact"):
            exact = sol_set["point_exact"]
            point_str = ", ".join(exact)
            with ui.element('div').classes('geo-summary mt-2').style('overflow-wrap: anywhere;'):
                ui.label(f"Única solución en ({point_str})").classes('badge-info')
                
                # Render \mathbf{x} = [pt]
                from src.backend.solvers.vector_ops.formatters import vector_to_latex
                from src.backend.models.matrix import Matrix
                p_latex = vector_to_latex(Matrix(len(exact), 1, exact))
                eq_id = f"geo-sol-{id(sol_set)}"
                ui.html(f'<div id="{eq_id}" class="math-label mt-2 mb-1">$$ \\mathbf{{x}} = {p_latex} $$</div>')
                ui.run_javascript(f"typesetMathWhenReady(['{eq_id}']);")

        elif sol_status == "NO_SOLUTION":
            msg = "El sistema no tiene solución"
            if "parallel" in flags and n == 2:
                msg = "Las rectas son paralelas y no se intersectan"
            with ui.element('div').classes('geo-summary mt-2'):
                ui.label(msg).classes('badge-error')

        elif sol_status == "INFINITE_SOLUTIONS":
            if sol_set and sol_set.get("whole_space"):
                ui.label(f"Todo el espacio R^{n}").classes('badge-success mt-2')
            else:
                dim = sol_set.get("dimension", 0) if sol_set else 0
                ui.label(f"Solución paramétrica (d={dim})").classes('badge-warning mt-2')
                
                if sol_set and sol_set.get("param_latex"):
                    latex = sol_set["param_latex"]
                    eq_id = f"geo-sol-{id(sol_set)}"
                    ui.html(f'<div id="{eq_id}" class="math-label mt-2 mb-1">$$ {latex} $$</div>')
                    ui.run_javascript(f"typesetMathWhenReady(['{eq_id}']);")
                    
                if sol_set and sol_set.get("description"):
                    ui.label(sol_set["description"]).classes('text-sm text-sub mt-1')

        elif pending:
            ui.label("Ecuaciones linealmente dependientes. Resuelve el sistema para ver los parámetros.").classes('text-sm text-sub mt-2 italic')

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
