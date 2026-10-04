"""Mixin de escenas Plotly para el Visualizador Geométrico."""
from __future__ import annotations

import json
import logging
from nicegui import ui

logger = logging.getLogger(__name__)


class GeometryScenesMixin:
    """Renderiza figuras Plotly para las tres escenas del Visualizador."""

    def _js(self, code: str) -> None:
        """Ejecuta código JavaScript de forma segura sobre el cliente NiceGUI."""
        client = getattr(self, '_client', None)
        if client is None or getattr(client, 'is_deleted', False):
            return
        try:
            client.run_javascript(code)
        except Exception as e:
            logger.debug("Error ejecutando JS en GeometryScenesMixin: %s", e)

    async def _tema_actual(self) -> str:
        client = getattr(self, '_client', None)
        if client is None or getattr(client, 'is_deleted', False):
            return 'papel'
        try:
            res = await client.run_javascript(
                "document.documentElement.getAttribute('data-theme') || 'papel'",
                timeout=3.0,
            )
            return res or 'papel'
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
                return build_vectors_figure(result, theme=theme)
            elif scene == 'combinacion':
                from ._scenes import build_combination_figure
                theme = await self._tema_actual()
                return build_combination_figure(result, theme=theme)
        except ImportError:
            raise
        except Exception:
            logger.exception("Error al construir figura en _get_figure_only")
            return None

    async def _build_figure(self, result: dict, scene: str) -> bool:
        """Build and display the Plotly figure for the given scene."""
        try:
            fig = await self._get_figure_only(result, scene)
            if fig is None:
                if hasattr(self, '_render_error'):
                    self._render_error({"code": "render_failed", "message": "No pudimos dibujar la figura. Revisa los valores e inténtalo de nuevo."})
                self._js("""
                    var c = document.querySelector('.geo-figure');
                    if (c) c.style.opacity = '1';
                """)
                return False

            if self.figure_container:
                self.figure_container.clear()
                with self.figure_container:
                    wrap_id = f"geo-fig-{id(self)}"
                    sol_desc = (result.get("set") or {}).get("description")
                    aria_desc = sol_desc if sol_desc else f"Visualización geométrica: {scene}"
                    with ui.element('div').props(f'id="{wrap_id}" role="img" aria-label="{aria_desc}"').classes('geo-figure w-full'):
                        self._plotly_element = ui.plotly(fig).classes('w-full h-full')

                    # Register frames for vectors scene
                    if scene == 'vectores' and result.get("frames"):
                        frames_json = json.dumps(result["frames"])
                        self._js(f'scalarisGeo.register("{wrap_id}", {frames_json});')
            return True
        except ImportError:
            if self.figure_container:
                self.figure_container.clear()
                with self.figure_container:
                    with ui.row().classes('items-center gap-2 px-4 py-2 badge-error w-fit'):
                        ui.icon('close', size='sm')
                        ui.label('No se pudo cargar el módulo de gráficos (plotly).').classes('font-bold')
            return False
        except Exception:
            logger.exception("Error al dibujar la figura en _build_figure")
            if hasattr(self, '_render_error'):
                self._render_error({"code": "render_failed", "message": "No pudimos dibujar la figura. Revisa los valores e inténtalo de nuevo."})
            return False

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

            if result.get("out_of_range"):
                with ui.element('div').classes('geo-notice mt-2'):
                    ui.label("Algunos elementos quedan fuera del rango visible").classes('text-sm text-sec')

            sol_set = result.get("set")
            if sol_set and sol_set.get("segment_visible") is False:
                with ui.element('div').classes('geo-notice mt-2'):
                    ui.label("La recta solución queda fuera del rango visible").classes('text-sm text-sec')

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
                    latex = eq.get("latex", "")
                    ui.html(f'<div id="{eq_id}" class="math-label text-sm mb-1">$$ {latex} $$</div>')

            if eq_ids:
                self._js(f"typesetMathWhenReady({json.dumps(eq_ids)});")

        # Solution status
        # Orden de ramas: pending primero (pending_param con set is None)
        if pending and sol_set is None:
            with ui.element('div').classes('geo-notice mt-2'):
                ui.label("No pudimos dibujar el conjunto solución. Las ecuaciones sí se grafican.").classes('text-sm text-sec')

        elif sol_status == "UNIQUE_SOLUTION" and sol_set and sol_set.get("point_exact"):
            exact = sol_set["point_exact"]
            point_str = ", ".join(exact)
            with ui.element('div').classes('geo-summary mt-2').style('overflow-wrap: anywhere;'):
                ui.label(f"Única solución en ({point_str})").classes('badge-success px-4 py-2 w-fit')
                p_latex = sol_set.get("point_latex")
                if p_latex:
                    eq_id = f"geo-sol-{id(sol_set)}"
                    with ui.element('div').classes('math-scroll-container mt-2 mb-1'):
                        ui.html(f'<div id="{eq_id}" class="math-label">$$ \\mathbf{{x}} = {p_latex} $$</div>')
                    self._js(f"typesetMathWhenReady(['{eq_id}']);")

        elif sol_status == "NO_SOLUTION":
            msg = "El sistema no tiene solución"
            if "parallel" in flags and n == 2:
                msg = "Las rectas son paralelas y no se intersectan"
            with ui.element('div').classes('geo-summary mt-2').style('overflow-wrap: anywhere;'):
                ui.label(msg).classes('badge-error px-4 py-2 w-fit')

        elif sol_status == "INFINITE_SOLUTIONS" and sol_set:
            if sol_set.get("whole_space"):
                espacio = "R²" if n == 2 else "R³"
                with ui.element('div').classes('geo-summary mt-2').style('overflow-wrap: anywhere;'):
                    ui.label(f"Todos los puntos de {espacio} son solución").classes('badge-success px-4 py-2 w-fit')
            else:
                dim = sol_set.get("dimension", 0)
                with ui.element('div').classes('geo-summary mt-2').style('overflow-wrap: anywhere;'):
                    ui.label(f"Solución paramétrica (d={dim})").classes('badge-warning px-4 py-2 w-fit')

                    if sol_set.get("description"):
                        ui.label(sol_set["description"]).classes('text-sm text-sec mt-1').style('overflow-wrap: anywhere;')

                    if sol_set.get("param_latex"):
                        latex = sol_set["param_latex"]
                        eq_id = f"geo-sol-{id(sol_set)}"
                        with ui.element('div').classes('math-scroll-container mt-2 mb-1'):
                            ui.html(f'<div id="{eq_id}" class="math-label">$$ {latex} $$</div>')
                        self._js(f"typesetMathWhenReady(['{eq_id}']);")

                    if sol_set.get("free_vars"):
                        vars_str = ", ".join(sol_set["free_vars"])
                        ui.label(f"Variables libres: {vars_str}").classes('text-sm text-sec mt-1').style('overflow-wrap: anywhere;')

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
            self._js(f'typesetMathWhenReady(["{summary_id}"]);')

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
            self._js(f'typesetMathWhenReady(["{summary_id}"]);')

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
