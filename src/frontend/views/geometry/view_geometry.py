"""Vista principal del Visualizador Geométrico (F8a).

Escenas interactivas en R² y R³: rectas-planos, vectores, combinación lineal.
"""
from __future__ import annotations

import asyncio
import json
import logging
from nicegui import ui, run

from src.frontend.components.app_shell import create_app_shell
from src.frontend.components.ai_panel import AIPanel
from src.frontend.constantes import DEBOUNCE_GEOMETRIA_SEGUNDOS
from src.frontend.navigation import route_of
from src.frontend.controllers.geometry.controller_geometry import GeometryController
from .scenes_mixin import GeometryScenesMixin
from .controls_mixin import GeometryControlsMixin

logger = logging.getLogger(__name__)

VALID_SCENES = ('rectas-planos', 'vectores', 'combinacion')


class GeometryUI(GeometryControlsMixin, GeometryScenesMixin):
    """Controlador de vista del Visualizador Geométrico."""

    def __init__(self):
        self._client = None
        self.ai_panel = None
        self.scene = 'rectas-planos'
        self.last_result = None
        self.last_payload_hash = None
        self._preview_task = None
        self._first_draw = True
        self._plotly_element = None
        self._fig_key = None

        # Containers
        self.controls_container = None
        self.figure_container = None
        self.summary_container = None
        self.slider_container = None
        self.status_container = None

        # Scene-specific panels
        self.grid = None
        self.vec_panel = None
        self.comb_panel = None

    def _js(self, code: str) -> None:
        """Ejecuta código JavaScript de forma segura sobre el cliente NiceGUI."""
        client = getattr(self, '_client', None)
        if client is None or getattr(client, 'is_deleted', False):
            return
        try:
            client.run_javascript(code)
        except Exception as e:
            logger.debug("Error ejecutando JS en GeometryUI: %s", e)

    def _spawn(self, coro) -> asyncio.Task:
        """Crea una tarea async que entra al contexto del cliente antes de ejecutar la corrutina."""
        async def runner():
            client = getattr(self, '_client', None)
            if client is not None and not getattr(client, 'is_deleted', False):
                with client:
                    return await coro
            return await coro

        r = runner()
        try:
            task = asyncio.create_task(r)
            task.add_done_callback(lambda t: coro.close())
            return task
        except Exception:
            r.close()
            coro.close()
            raise

    def build(self, escena: str = 'rectas-planos', handoff_token: str = ''):
        try:
            self._client = ui.context.client
        except Exception:
            self._client = None

        self.scene = self.normalize_scene(escena)

        self.ai_panel = AIPanel(self)
        create_app_shell(
            self,
            active_route=route_of('visualizador'),
            active_key=f"vis:{self.scene}",
        )

        ui.add_head_html('<script src="/assets/js/geometry.js"></script>')

        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4 view-root'):
            with ui.element('div').classes('layout-split'):
                # Left pane: controls
                with ui.column().classes('layout-pane p-6 bg-[var(--bg-page)]').style('min-width: 0;') as left:
                    self.controls_container = ui.column().classes('w-full')

                # Right pane: figure + summary
                with ui.column().classes('layout-pane p-6 bg-[var(--bg-page)]').style('min-width: 0;') as right:
                    self.status_container = ui.column().classes('w-full')
                    self.figure_container = ui.column().classes('w-full')
                    self.slider_container = ui.column().classes('w-full')
                    self.summary_container = ui.column().classes('w-full')

        self.ai_panel.build()

        # Build initial controls
        self._build_controls(self.scene)
        self._render_empty_state()

        # Process handoff AFTER empty state
        self._process_handoff(handoff_token)

    @staticmethod
    def normalize_scene(escena: str) -> str:
        """Valida y normaliza el parametro de escena contra VALID_SCENES."""
        if escena not in VALID_SCENES:
            return 'rectas-planos'
        return escena

    def _process_handoff(self, token: str):
        """Process handoff token on page load."""
        if not token:
            return

        from src.frontend.components.handoff import (
            consume_system,
            consume_vectors,
            render_handoff_notice,
            clean_handoff_url,
        )

        if self.scene == 'rectas-planos':
            result = consume_system(token, max_m=10, allowed_n={2, 3})
            if result is None:
                return
            clean_handoff_url()
            if result.status == 'ok' and result.data:
                # Pre-fill grid with handoff data
                data = result.data
                A = data.get("matrix_A", [])
                b = data.get("vector_b", [])
                if A and self.grid:
                    m = len(A)
                    n = len(A[0]) if A else 2
                    self.grid.m = m
                    self.grid.n = n
                    self.grid._cache_A.clear()
                    self.grid._cache_b.clear()
                    for i, row in enumerate(A):
                        for j, val in enumerate(row):
                            self.grid._cache_A[(i, j)] = str(val)
                    for i, val in enumerate(b):
                        self.grid._cache_b[i] = str(val)
                    self.grid.entradas_A.clear()
                    self.grid.entradas_b.clear()
                    self.grid.generar_cuadricula()
                    self._trigger_live_preview()
                with self.status_container:
                    render_handoff_notice(result, f"Sistema cargado desde {result.source_name}")
            else:
                with self.status_container:
                    render_handoff_notice(result, "")
        else:
            result = consume_vectors(token, allowed_n={2, 3})
            if result is None:
                return
            clean_handoff_url()

            if result.status == 'ok' and result.data:
                scene_from_data = result.data.get("scene")
                if scene_from_data != self.scene:
                    from src.frontend.components.handoff import HandoffResult
                    result = HandoffResult(
                        status='invalid',
                        data=None,
                        source_name=result.source_name,
                        message="Los datos recibidos no son válidos, así que empezamos con la herramienta vacía.",
                    )
                    with self.status_container:
                        render_handoff_notice(result, "")
                    return

                vectors_data = result.data.get("data", [])

                from src.frontend.components.handoff import HandoffResult
                is_valid = True
                if self.scene == 'vectores':
                    if len(vectors_data) != 2:
                        result = HandoffResult(status='invalid', data=None, source_name=result.source_name, message="La escena de Vectores requiere exactamente 2 vectores.")
                        is_valid = False
                elif self.scene == 'combinacion':
                    if not (2 <= len(vectors_data) <= 5):
                        result = HandoffResult(status='invalid', data=None, source_name=result.source_name, message="La escena de Combinación lineal requiere entre 2 y 5 vectores (b + v1...v4).")
                        is_valid = False

                if is_valid:
                    self._build_controls(self.scene)

                    panel = self.vec_panel if self.scene == 'vectores' else self.comb_panel
                    if panel and vectors_data:
                        n = len(vectors_data[0]) if vectors_data else 2
                        panel.dim = n
                        while len(panel.vectors) < len(vectors_data):
                            panel.add_vector()

                        for vi, vec in enumerate(vectors_data):
                            name = list(panel.vectors.keys())[vi] if vi < len(panel.vectors) else None
                            if name:
                                for ci, val in enumerate(vec):
                                    panel.vectors[name]['cache'][ci] = str(val)
                        panel.render_all_vectors()
                        self._trigger_live_preview()
                    with self.status_container:
                        render_handoff_notice(result, f"Vectores cargados desde {result.source_name}")
                else:
                    with self.status_container:
                        render_handoff_notice(result, "")
            else:
                with self.status_container:
                    render_handoff_notice(result, "")

    def _render_empty_state(self):
        """Show empty orientational state."""
        self._fig_key = None
        self._plotly_element = None
        if self.figure_container:
            self.figure_container.clear()
        if self.slider_container:
            self.slider_container.clear()
        if self.summary_container:
            self.summary_container.clear()
        if self.status_container:
            self.status_container.clear()

        if self.figure_container:
            with self.figure_container:
                with ui.column().classes('w-full geo-empty justify-center items-center text-center py-12'):
                    ui.icon('insights', size='4rem').classes('text-placeholder mb-4')
                    if self.scene == 'rectas-planos':
                        ui.label('Escribe al menos una ecuación o carga un sistema desde Sistemas de ecuaciones').classes('text-sm text-sec')
                    elif self.scene == 'vectores':
                        ui.label('Ingresa dos vectores para visualizar la suma y el escalamiento').classes('text-sm text-sec')
                    elif self.scene == 'combinacion':
                        ui.label('Ingresa b y los vectores columna para ver la combinación lineal').classes('text-sm text-sec')

    def _on_data_change(self):
        """Called when input data changes (from grid or vector panels)."""
        self._trigger_live_preview()
        p = getattr(self, 'ai_panel', None)
        if p and hasattr(p, 'schedule_context_refresh'):
            p.schedule_context_refresh()

    def _trigger_live_preview(self):
        """Debounced preview: cancels previous task, waits 350ms."""
        if self._preview_task and not self._preview_task.done():
            self._preview_task.cancel()
        self._preview_task = self._spawn(self._debounced_update())

    async def _debounced_update(self):
        """Wait then update if payload changed."""
        try:
            await asyncio.sleep(DEBOUNCE_GEOMETRIA_SEGUNDOS)
            await self._update_figure()
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Error no capturado en _debounced_update")

    async def _update_figure(self):
        """Process data and update the figure."""
        try:
            payload = self._build_payload()
            if payload is None:
                self.last_payload_hash = None
                self.last_result = None
                self._first_draw = True
                self._plotly_element = None
                self._fig_key = None
                self._render_empty_state()
                return

            # Check if payload changed
            payload_hash = hash(json.dumps(payload, sort_keys=True))
            if payload_hash == self.last_payload_hash:
                return

            # Show loading state
            if self._first_draw:
                if self.figure_container:
                    self.figure_container.clear()
                    with self.figure_container:
                        ui.skeleton().classes('w-full geo-figure')
            else:
                # Dim the existing figure
                if self.figure_container:
                    self._js("""
                        var c = document.querySelector('.geo-figure');
                        if (c) c.style.opacity = '0.4';
                    """)

            # Process
            payload_json = json.dumps(payload)
            if self.scene == 'rectas-planos':
                result = await run.io_bound(GeometryController.process_lines_planes, payload_json)
            elif self.scene == 'vectores':
                result = await run.io_bound(GeometryController.process_vectors, payload_json)
            elif self.scene == 'combinacion':
                result = await run.io_bound(GeometryController.process_combination, payload_json)
            else:
                return

            if result.get("status") == "ERROR":
                self._fig_key = None
                self._plotly_element = None
                self.last_result = None
                self.last_payload_hash = None
                self._js("""
                    var c = document.querySelector('.geo-figure');
                    if (c) c.style.opacity = '1';
                """)
                self._render_error(result)
                from src.ai.context import fingerprint
                self._result_fp = fingerprint({"scene": self.scene, "payload": payload})
                p = getattr(self, 'ai_panel', None)
                if p and hasattr(p, 'schedule_context_refresh'):
                    p.schedule_context_refresh()
                return

            # Clear markInvalid
            self._js('scalarisGeo.markInvalid(null);')

            # Reutilizar figura si aplica
            new_fig_key = (self.scene, result.get("n"))
            if not self._first_draw and self._plotly_element and self._fig_key == new_fig_key:
                # Actualizar in situ
                fig = await self._get_figure_only(result, self.scene)
                if fig:
                    self._plotly_element.update_figure(fig)
                    if self.scene == 'vectores' and result.get("frames"):
                        frames_json = json.dumps(result["frames"])
                        wrap_id = f"geo-fig-{id(self)}"
                        self._js(f'scalarisGeo.register("{wrap_id}", {frames_json});')
                    # En el camino de reutilización restaura la opacidad atenuada (.geo-figure vuelve a opacity 1) al terminar
                    self._js("""
                        var c = document.querySelector('.geo-figure');
                        if (c) c.style.opacity = '1';
                    """)
                else:
                    self._render_error({"code": "render_failed", "message": "No pudimos dibujar la figura. Revisa los valores e inténtalo de nuevo."})
                    self.last_payload_hash = None
                    self.last_result = None
                    self._fig_key = None
                    self._plotly_element = None
                    self._first_draw = True
                    self._js("""
                        var c = document.querySelector('.geo-figure');
                        if (c) c.style.opacity = '1';
                    """)
                    p = getattr(self, 'ai_panel', None)
                    if p and hasattr(p, 'schedule_context_refresh'):
                        p.schedule_context_refresh()
                    return
            else:
                # Build figure from scratch
                figure_ok = await self._build_figure(result, self.scene)
                if not figure_ok:
                    self.last_payload_hash = None
                    self.last_result = None
                    self._fig_key = None
                    self._plotly_element = None
                    self._first_draw = True
                    self._js("""
                        var c = document.querySelector('.geo-figure');
                        if (c) c.style.opacity = '1';
                    """)
                    p = getattr(self, 'ai_panel', None)
                    if p and hasattr(p, 'schedule_context_refresh'):
                        p.schedule_context_refresh()
                    return

            self._fig_key = new_fig_key
            self.last_result = result
            self.last_payload_hash = payload_hash

            self._build_slider(result, self.scene)
            self._render_summary(result, self.scene)
            if self.summary_container:
                with self.summary_container:
                    p = getattr(self, 'ai_panel', None)
                    if p and hasattr(p, 'render_inline_chips'):
                        p.render_inline_chips()
            self._first_draw = False

            from src.ai.context import fingerprint
            self._result_fp = fingerprint({"scene": self.scene, "payload": payload})
            p = getattr(self, 'ai_panel', None)
            if p and hasattr(p, 'schedule_context_refresh'):
                p.schedule_context_refresh()

        except asyncio.CancelledError:
            self.last_payload_hash = None
            self._js("""
                var c = document.querySelector('.geo-figure');
                if (c) c.style.opacity = '1';
            """)
            raise
        except Exception:
            self.last_payload_hash = None
            self.last_result = None
            logger.exception("Error al actualizar figura geométrica")
            self._render_error({"code": "render_failed", "message": "No pudimos dibujar la figura. Revisa los valores e inténtalo de nuevo."})

    def _build_payload(self) -> dict | None:
        """Extract payload from current inputs."""
        try:
            if self.scene == 'rectas-planos':
                if not self.grid or self.grid.is_strictly_empty():
                    return None
                matrix_A, vector_b = self.grid.get_matrix_data()
                if not matrix_A or not matrix_A[0]:
                    return None
                return {"matrix_A": matrix_A, "vector_b": vector_b}

            elif self.scene in ('vectores', 'combinacion'):
                panel = self.vec_panel if self.scene == 'vectores' else self.comb_panel
                if not panel:
                    return None

                dim = panel.dim
                vec_list = []
                for name, vdata in panel.vectors.items():
                    cache = vdata.get('cache', {})
                    coords = [cache.get(i, '0') or '0' for i in range(dim)]
                    vec_list.append({"data": coords, "orientation": "column"})

                has_data = any(
                    any(val != '0' for val in vec["data"])
                    for vec in vec_list
                )
                if not has_data:
                    return None

                if self.scene == 'vectores':
                    return {"vectors": vec_list}
                else:
                    return {"b": vec_list[0], "vectors": vec_list[1:]}

        except Exception:
            return None

    def _render_error(self, result: dict):
        """Render error state with cell marking."""
        try:
            self._fig_key = None
            self._plotly_element = None
            if self.figure_container:
                self.figure_container.clear()
            if self.slider_container:
                self.slider_container.clear()
            if self.summary_container:
                self.summary_container.clear()

            self._js("""
                var c = document.querySelector('.geo-figure');
                if (c) c.style.opacity = '1';
            """)

            error_cell = result.get("error_cell")
            code = result.get("code", "")
            message = result.get("message", "Error desconocido.")

            if self.figure_container:
                with self.figure_container:
                    with ui.column().classes('w-full py-8 items-center'):
                        if code in ("bad_dimension", "not_finite"):
                            with ui.row().classes('items-center gap-2 px-4 py-2 badge-warning w-fit'):
                                ui.icon('info', size='sm')
                                ui.label(message).classes('font-bold')
                        else:
                            with ui.row().classes('items-center gap-2 px-4 py-2 badge-error w-fit'):
                                ui.icon('close', size='sm')
                                ui.label(message).classes('font-bold')

                            if error_cell:
                                # Mark the cell
                                selector = self._cell_selector(error_cell)
                                if selector:
                                    self._js(f'scalarisGeo.markInvalid({json.dumps(selector)});')
                                    # "Go to cell" button
                                    ui.button('Ir a la celda', icon='gps_fixed', color=None,
                                              on_click=lambda s=selector: self._js(
                                                  f'var el = document.querySelector({json.dumps(s)}); if(el) {{ el.focus(); el.scrollIntoView({{block: "center"}}); }}'
                                              )).classes('btn-ghost mt-2').props('ripple=false')
        except Exception:
            logger.exception("Error al renderizar estado de error")

    def _cell_selector(self, error_cell: dict) -> str | None:
        """Build a CSS selector for an error cell."""
        from src.frontend.controllers.geometry.controller_geometry import error_cell_selector
        grid_n = self.grid.n if self.grid else 2
        return error_cell_selector(error_cell, scene=self.scene, grid_n=grid_n)

    # --- AI Context ---

    def get_ai_context(self):
        from src.ai.context import AIContext, sanitize_user_string

        if self.last_result is None:
            return AIContext("visualizador", "Visualizador geométrico", f"Escena: {self.scene}", {}, empty=True)

        result = self.last_result
        input_data = {"scene": self.scene}

        # Sanitize inputs
        if self.scene == 'rectas-planos' and self.grid:
            try:
                A, b = self.grid.get_matrix_data()
                input_data["matrix_A"] = [[sanitize_user_string(str(v), 32) for v in row] for row in (A or [])]
                input_data["vector_b"] = [sanitize_user_string(str(v), 32) for v in (b or [])]
            except Exception:
                pass

        result_data = {}
        if result.get("status") == "OK":
            if self.scene == 'rectas-planos':
                sol_set = result.get("set")
                result_data["solution_status"] = result.get("solution_status", "")
                if sol_set:
                    result_data["set_kind"] = sol_set.get("kind", "")
                    if "dimension" in sol_set:
                        result_data["dimension"] = sol_set["dimension"]
                    if "free_vars" in sol_set:
                        result_data["free_vars"] = sol_set["free_vars"]
                if result.get("pending_param"):
                    result_data["pending"] = True
            elif self.scene in ('vectores', 'combinacion'):
                result_data["solution_status"] = result.get("solution_status", "")
        else:
            result_data["status"] = "ERROR"
            result_data["message"] = result.get("message", "")

        ctx = AIContext("visualizador", "Visualizador geométrico", f"Escena: {self.scene}", input_data)
        from src.ai.context import is_stale
        entrada_actual = {"scene": self.scene, "payload": self._build_payload()}
        ctx.stale = is_stale(entrada_actual, getattr(self, '_result_fp', None))
        if ctx.stale:
            ctx.result = None
        else:
            ctx.result = result_data
        return ctx

    def get_ai_signals(self):
        from src.frontend.suggestions import Signals
        try:
            state = "none"
            flags_set = set()

            if self.last_result and self.last_result.get("status") == "OK":
                if self.scene == 'rectas-planos':
                    sol_status = self.last_result.get("solution_status", "")
                    if sol_status == "UNIQUE_SOLUTION":
                        state = "unique"
                    elif sol_status == "NO_SOLUTION":
                        state = "no_solution"
                    elif sol_status == "INFINITE_SOLUTIONS":
                        state = "infinite"
                    flags_set.update(self.last_result.get("flags", []))
                elif self.scene == 'vectores':
                    state = "result"
                elif self.scene == 'combinacion':
                    sol_status = self.last_result.get("solution_status", "")
                    if sol_status == "UNIQUE":
                        state = "unique"
                    elif sol_status == "INFINITE":
                        state = "infinite"
                    elif sol_status == "NO_SOLUTION":
                        state = "no_solution"

            return Signals(tool="visualizador", state=state, flags=frozenset(flags_set))
        except Exception:
            return None


    def render_inline_chips(self):
        """Render inline suggestion chips after badge."""
        if getattr(self, 'ai_panel', None):
            self.ai_panel.render_inline_chips()
