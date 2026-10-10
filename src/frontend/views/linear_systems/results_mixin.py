"""Mixin de resolución y presentación de resultados para Sistemas Lineales."""
import asyncio
import html
import json
import logging
import re

from nicegui import ui

from src.backend.utils.parsers import SystemParser
from src.frontend.controllers.linear_systems.controller_gauss import MatrixController
from src.frontend.controllers.linear_systems.controller_gauss_jordan import GaussJordanController

logger = logging.getLogger(__name__)


class LinearSystemsResultsMixin:
    """Resuelve sistemas lineales y presenta sus resultados y procedimientos."""

    async def confirmar_limpieza(self):
        if self.is_empty():
            ui.notify('El sistema ya está vacío', type='warning', position='top')
            return

        with ui.dialog() as dialog, ui.card().classes('panel-card no-shadow p-6 min-w-[300px]'):
            ui.label('¿Vaciar datos?').classes('text-xl font-bold mb-4')
            ui.label('Se animarán y eliminarán los datos.').classes('text-sm text-sec mb-6')
            with ui.row().classes('w-full justify-end gap-3'):
                ui.button('Cancelar', on_click=dialog.close, color=None).classes('btn-ghost px-4').props('ripple=false')
                ui.button('Limpiar', on_click=lambda: self.ejecutar_animacion_limpieza(dialog), color=None).classes(
                    'btn-primary px-4'
                ).style('background: var(--error); color: white;').props('ripple=false')
        dialog.open()

    async def ejecutar_animacion_limpieza(self, dialog):
        dialog.close()
        try:
            await ui.run_javascript('return window.animateGarbageCollection()', timeout=2.0)
        except Exception:
            pass
        self.limpiar_todo()

    def limpiar_todo(self):
        if getattr(self, 'reproductor_pasos', None) is not None:
            self.reproductor_pasos.detener()
            self.reproductor_pasos = None
        self.grid.clear()
        for inp in self.ecuaciones_inputs:
            inp.value = ''
        self.reset_resultados()
        self._result_fp = None
        p = getattr(self, 'ai_panel', None)
        if p and hasattr(p, 'schedule_context_refresh'):
            p.schedule_context_refresh()

    def reset_resultados(self):
        if getattr(self, 'reproductor_pasos', None) is not None:
            self.reproductor_pasos.detener()
            self.reproductor_pasos = None
        self.contenedor_resultados.clear()
        self.contenedor_resultados.classes(remove='items-start justify-start', add='items-center justify-center')
        with self.contenedor_resultados:
            ui.icon('calculate', size='4rem').classes('text-placeholder mb-4')
            ui.label('Listo para resolver').classes('text-xl font-bold text-main')
            ui.label('Ingresa las ecuaciones o la matriz y presiona Resolver').classes('text-sm text-sec mt-2 text-center')

    async def resolver_sistema(self, sender):
        if self.is_strictly_empty():
            self.reset_resultados()
            with self.contenedor_resultados:
                self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-warning mb-4 w-fit'):
                    ui.icon('warning_amber', size='sm')
                    ui.label('Ingresa al menos un valor antes de resolver').classes('font-bold')
            ui.run_javascript("setTimeout(() => { const el = document.getElementById('resultados-container'); if(el) el.scrollIntoView({behavior: 'smooth', block: 'start'}) }, MOTION.fast);")
            return

        btn = sender
        btn.props('loading=true')
        try:
            await self._resolver_core(btn)
        except Exception as e:
            self._mostrar_error_inesperado(e)
        finally:
            btn.props('loading=false')

    def _mostrar_error_inesperado(self, exc):
        logger.error("Error inesperado al resolver el sistema", exc_info=exc)
        self.contenedor_resultados.clear()
        self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
        with self.contenedor_resultados:
            with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                ui.icon('close', size='sm')
                ui.label('Ocurrió un error inesperado al resolver el sistema. Revisa los datos e inténtalo de nuevo.').classes('font-bold')
        ui.notify('Error inesperado', type='negative', position='top')

    def _obtener_payload(self) -> tuple[dict, list, list, list] | None:
        """Extrae y valida los datos de entrada según el modo activo."""
        variables = None
        if self.mode_tabs.value == 'Matriz':
            matrix_A_vals, vector_b_vals = self.grid.get_matrix_data()
            if matrix_A_vals and len(matrix_A_vals) > 0:
                variables = [f"x{j+1}" for j in range(len(matrix_A_vals[0]))]
            else:
                variables = []
        else:
            lineas = [inp.value or "" for inp in self.ecuaciones_inputs]
            raw_text = "\n".join(lineas)
            success, parsed_matrix, variables, msg = SystemParser.parse_system(raw_text)

            if not success:
                with self.contenedor_resultados:
                    self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
                    with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                        ui.icon('close', size='sm')
                        ui.label(msg).classes('font-bold')
                return None

            matrix_A_vals = [[str(val) for val in row[:-1]] for row in parsed_matrix.data]
            vector_b_vals = [str(row[-1]) for row in parsed_matrix.data]

        payload_dict = {"matrix_A": matrix_A_vals, "vector_b": vector_b_vals, "variables": variables}
        return payload_dict, matrix_A_vals, vector_b_vals, variables

    async def _resolver_core(self, btn):
        """Coordina el flujo completo de cálculo y renderizado de resultados."""
        await asyncio.sleep(0.1)
        self.contenedor_resultados.clear()

        datos_entrada = self._obtener_payload()
        if datos_entrada is None:
            return
        payload_dict, matrix_A_vals, vector_b_vals, variables = datos_entrada

        if self.method_tabs.value == 'gauss':
            respuesta_json_str = MatrixController.process_system(json.dumps(payload_dict))
        else:
            respuesta_json_str = GaussJordanController.process_system(json.dumps(payload_dict))

        respuesta = json.loads(respuesta_json_str)
        self.last_result = respuesta

        with self.contenedor_resultados:
            self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
            self._render_encabezado_y_solucion(respuesta, variables)
            self._render_steps_section(respuesta)
            self._render_botones_accion(respuesta, matrix_A_vals, vector_b_vals)

        ui.run_javascript('typesetMathWhenReady();')
        ui.run_javascript("replayResultAnimation('resultados-container');")
        ui.run_javascript("setTimeout(() => { const el = document.getElementById('resultados-container'); if(el) el.scrollIntoView({behavior: 'smooth', block: 'start'}) }, MOTION.med);")

        from src.ai.context import fingerprint
        entrada = {"mode": self.mode_tabs.value, "method": self.method_tabs.value}
        if self.mode_tabs.value == 'Ecuaciones':
            entrada["ecuaciones"] = [inp.value for inp in self.ecuaciones_inputs]
        else:
            entrada["A"] = matrix_A_vals
            entrada["b"] = vector_b_vals
        self._result_fp = fingerprint(entrada)
        p = getattr(self, 'ai_panel', None)
        if p and hasattr(p, 'schedule_context_refresh'):
            p.schedule_context_refresh()

    def _render_encabezado_y_solucion(self, respuesta: dict, variables: list | None):
        """Renderiza las insignias de estado y las fichas de solución."""
        status = respuesta.get("status")
        classification_msg = respuesta.get("classification") or respuesta.get("message", "")
        is_error = str(status).upper() == "ERROR"

        if is_error:
            with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                ui.icon('close', size='sm')
                ui.label(classification_msg).classes('font-bold')
        elif status == "NO_SOLUTION":
            with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                ui.icon('close', size='sm')
                ui.label("Sin solución").classes('font-bold')
        else:
            is_unique = (status == "UNIQUE_SOLUTION")
            badge_class = 'badge-success' if is_unique else 'badge-warning'
            icon_str = 'check' if is_unique else 'warning_amber'
            texto_corto = "Solución única" if is_unique else "Infinitas soluciones"

            with ui.row().classes('w-full items-center gap-3 mb-4 flex-wrap'):
                with ui.row().classes(f'items-center gap-2 px-4 py-2 {badge_class}'):
                    ui.icon(icon_str, size='sm')
                    badge_id = f"badge-{id(texto_corto)}"
                    ui.html(f'<b id="{badge_id}"></b>').classes('math-label')
                    ui.timer(0.05, lambda t=texto_corto, bid=badge_id: ui.run_javascript(f'typewriterEffect("{bid}", {json.dumps(t)}, 25)'), once=True)

                if respuesta.get("solution"):
                    for idx, val in enumerate(respuesta["solution"]):
                        raw_var = variables[idx] if variables and idx < len(variables) else f"x{idx+1}"
                        var_name = html.escape(str(raw_var))
                        m = re.match(r'^([a-zA-Z]+)(\d+)$', var_name)
                        if m:
                            html_var = f"<i>{m.group(1)}</i><sub>{m.group(2)}</sub>"
                            latex_var = f"{m.group(1)}_{{{m.group(2)}}}"
                        else:
                            html_var = f"<i>{var_name}</i>"
                            latex_var = f"\\text{{{var_name}}}" if len(var_name) > 1 else var_name

                        if is_unique:
                            ui.html(f'{html_var} = {val}').classes('px-4 py-2 panel-card font-bold math-label text-main min-w-0 max-w-full').style('overflow-wrap: anywhere;')
                        else:
                            ui.html(f'<div class="math-scroll-container px-4 py-2 panel-card math-label text-main min-w-0 max-w-full" style="overflow-wrap: anywhere;">$$ {latex_var} = {val} $$</div>')

            if getattr(self, 'ai_panel', None):
                self.ai_panel.render_inline_chips()

    def _render_botones_accion(self, respuesta: dict, matrix_A_vals: list, vector_b_vals: list):
        """Pinta los botones de handoff hacia Matriz inversa y Visualizador."""
        status = respuesta.get("status")
        is_error = str(status).upper() == "ERROR"
        if is_error:
            return

        self._add_to_history(matrix_A_vals, vector_b_vals, len(matrix_A_vals), len(matrix_A_vals[0]) if matrix_A_vals else 0, status, self.method_tabs.value)
        n_vars = len(matrix_A_vals[0]) if matrix_A_vals else 0

        with ui.row().classes('gap-2 mt-4 flex-wrap'):
            if len(matrix_A_vals) == len(matrix_A_vals[0]):
                from src.frontend.components.handoff import handoff_url, put_matrix
                from src.frontend.navigation import route_of
                ui.button('Ver A⁻¹ en Matriz inversa', icon='arrow_forward', color=None,
                          on_click=lambda: ui.navigate.to(handoff_url(route_of('inversa'), put_matrix('sistemas', matrix_A_vals)))
                         ).classes('btn-ghost').props('ripple=false').tooltip('Misma eliminación de filas, ahora sobre [A | I]')

            if n_vars in (2, 3):
                from src.frontend.components.handoff import handoff_url, put_system
                from src.frontend.navigation import route_of
                ui.button('Ver en el Visualizador', icon='insights', color=None,
                          on_click=lambda: ui.navigate.to(handoff_url(route_of('visualizador'), put_system('sistemas', matrix_A_vals, vector_b_vals)))
                         ).classes('btn-ghost').props('ripple=false').tooltip('Visualiza el sistema en R² o R³')

    def trigger_flip_animation(self, e=None):
        ui.run_javascript('''
            const panel = document.querySelector('.main-grid-panel');
            if(panel) {
                panel.classList.remove('animate-slide-bounce');
                void panel.offsetWidth; // trigger reflow
                panel.classList.add('animate-slide-bounce');
            }
        ''')
        p = getattr(self, 'ai_panel', None)
        if p and hasattr(p, 'schedule_context_refresh'):
            p.schedule_context_refresh()
