"""Mixin de resolución, gráficos y renderizado de resultados para Sistemas Lineales."""
import json
import asyncio
import logging
import html
import re
from nicegui import ui

logger = logging.getLogger(__name__)

from src.frontend.controllers.linear_systems.controller_gauss import MatrixController
from src.frontend.controllers.linear_systems.controller_gauss_jordan import GaussJordanController
from src.backend.utils.parsers import SystemParser
from src.backend.utils.validators import MatrixValidator
from src.frontend.helpers import format_step_for_mathjax, to_float
from src.frontend.theme import (
    CHART_PALETTE,
    CHART_MARKER_LIGHT,
    CHART_MARKER_BORDER,
    CHART_GRID_COLOR,
    CHART_ZERO_COLOR,
    CHART_FONT_COLOR,
)


class LinearSystemsResultsMixin:
    """Maneja el preview en vivo, resolución de sistemas (Gauss/Gauss-Jordan), gráficos y formateo."""

    def _trigger_live_preview(self):
        if self.preview_task:
            self.preview_task.cancel()
        self.preview_task = asyncio.create_task(self._update_preview())

    async def _update_preview(self):
        await asyncio.sleep(0.3)
        if not self.preview_container:
            return

        try:
            self.preview_container.clear()
            with self.preview_container:
                matrix_A, vector_b = self.grid.get_matrix_data()
                if not matrix_A or len(matrix_A) == 0 or len(matrix_A[0]) == 0:
                    ui.label('La matriz está vacía.').classes('text-sec italic text-sm mt-4 text-center')
                    return

                m = len(matrix_A)
                n = len(matrix_A[0])

                def sanitize(val):
                    if not val:
                        return '0'
                    success, _, _ = MatrixValidator.parse_number_exact(val)
                    if not success:
                        return r"\color{gray}{?}"
                    return val

                # Construir LaTeX para matriz aumentada
                latex_lines = []
                for i, row in enumerate(matrix_A):
                    row_strs = [sanitize(val) for val in row]
                    b_val = sanitize(vector_b[i] if i < len(vector_b) else '0')
                    latex_lines.append(" & ".join(row_strs) + f" & {b_val}")

                spec = "c" * n + "|c"
                matrix_tex = rf"\left[ \begin{{array}}{{{spec}}} " + r" \\ ".join(latex_lines) + r" \end{array} \right]"
                matrix_tex = html.escape(matrix_tex)

                ui.html(f'<div id="preview-matrix" class="math-scroll-container math-label text-lg mb-6 w-full text-center">$$ {matrix_tex} $$</div>')

                if m * n > 48:
                    ui.label('Sistema demasiado grande para vista previa en ecuaciones.').classes('text-sec italic text-sm mt-4 text-center')
                    ui.run_javascript("typesetMathWhenReady(['preview-matrix']);")
                    return

                # Validar celdas antes de exportar a ecuaciones
                todas_validas = True
                for i in range(m):
                    for j in range(n):
                        val = matrix_A[i][j]
                        if val:
                            success, _, _ = MatrixValidator.parse_number_exact(val)
                            if not success:
                                todas_validas = False
                                break
                    if not todas_validas:
                        break

                b_valid = True
                for i in range(m):
                    val = vector_b[i] if i < len(vector_b) else ''
                    if val:
                        success, _, _ = MatrixValidator.parse_number_exact(val)
                        if not success:
                            b_valid = False
                            break

                if not todas_validas or not b_valid:
                    ui.label('Corrige los valores inválidos para ver las ecuaciones.').classes('text-sec italic text-sm mt-4 text-center')
                    ui.run_javascript("typesetMathWhenReady(['preview-matrix']);")
                    return

                # Construir LaTeX para sistema de ecuaciones
                eqs = self.grid.export_to_equations()
                if not eqs:
                    ui.label('No hay ecuaciones válidas.').classes('text-sec italic text-sm mt-4 text-center')
                    ui.run_javascript("typesetMathWhenReady(['preview-matrix']);")
                    return

                eqs_tex = r" \\ ".join(eqs)
                eqs_tex = re.sub(r'x(\d+)', r'x_{\1}', eqs_tex)
                system_tex = r" \begin{cases} " + eqs_tex + r" \end{cases} "
                system_tex = html.escape(system_tex)

                ui.html(f'<div id="preview-system" class="math-scroll-container math-label text-lg w-full text-center">$$ {system_tex} $$</div>')
                ui.run_javascript("typesetMathWhenReady(['preview-matrix', 'preview-system']);")
        except Exception as e:
            logger.error("Error al actualizar vista previa", exc_info=e)
            with self.preview_container:
                ui.label('No se pudo generar la vista previa.').classes('text-sec italic text-sm mt-4 text-center')

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
        ui.run_javascript('animateGarbageCollection()')
        await asyncio.sleep(0.8)
        self.limpiar_todo()

    def limpiar_todo(self):
        self.grid.clear()
        for inp in self.ecuaciones_inputs:
            inp.value = ''
        self.reset_resultados()

    def reset_resultados(self):
        self.contenedor_resultados.clear()
        self.contenedor_resultados.classes(remove='items-start justify-start', add='items-center justify-center')
        with self.contenedor_resultados:
            ui.icon('calculate', size='4rem').classes('text-placeholder mb-4')
            ui.label('Listo para resolver').classes('text-xl font-bold text-main')
            ui.label('Ingresá las ecuaciones o la matriz y presioná Resolver').classes('text-sm text-sec mt-2 text-center')

    async def resolver_sistema(self, sender):
        if self.is_strictly_empty():
            self.reset_resultados()
            with self.contenedor_resultados:
                self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-warning mb-4 w-fit'):
                    ui.icon('warning_amber', size='sm')
                    ui.label('Ingresá al menos un valor antes de resolver').classes('font-bold')
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

    async def _resolver_core(self, btn):
        await asyncio.sleep(0.1)
        self.contenedor_resultados.clear()

        # Extraer datos según la pestaña activa
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
                return

            matrix_A_vals = [[str(val) for val in row[:-1]] for row in parsed_matrix.data]
            vector_b_vals = [str(row[-1]) for row in parsed_matrix.data]

        payload_dict = {"matrix_A": matrix_A_vals, "vector_b": vector_b_vals, "variables": variables}

        if self.method_tabs.value == 'gauss':
            respuesta_json_str = MatrixController.process_system(json.dumps(payload_dict))
        else:
            respuesta_json_str = GaussJordanController.process_system(json.dumps(payload_dict))

        respuesta = json.loads(respuesta_json_str)

        with self.contenedor_resultados:
            self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')

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
                            var_name = variables[idx] if variables and idx < len(variables) else f"x{idx+1}"
                            m = re.match(r'^([a-zA-Z]+)(\d+)$', var_name)
                            if m:
                                html_var = f"<i>{m.group(1)}</i><sub>{m.group(2)}</sub>"
                                latex_var = f"{m.group(1)}_{{{m.group(2)}}}"
                            else:
                                html_var = f"<i>{var_name}</i>"
                                latex_var = f"\\text{{{var_name}}}" if len(var_name) > 1 else var_name

                            if is_unique:
                                ui.html(f'{html_var} = {val}').classes('px-4 py-2 panel-card font-bold math-label text-main')
                            else:
                                ui.html(f'<div class="px-4 py-2 panel-card math-label text-main">$$ {latex_var} = {val} $$</div>')

                if respuesta.get("intermediate_steps_latex"):
                    ui.label('Procedimiento paso a paso').classes('font-bold mt-6 text-xl text-main')
                    with ui.expansion('Ver pasos matriciales', icon='visibility').classes('w-full panel-card mt-2 timeline-expansion').props('header-class="font-bold text-main"'):
                        for paso in respuesta["intermediate_steps_latex"]:
                            with ui.column().classes('w-full p-4 border-l-2 border-l-[var(--accent)] ml-2 mb-2 bg-[var(--bg-panel)] rounded-r-lg'):
                                desc_id = f"desc-{id(paso)}"
                                ui.html(f'<span id="{desc_id}"></span>').classes('text-sm font-semibold mb-2 text-sec block')
                                ui.timer(0.05, lambda text=paso["descripcion"], eid=desc_id: ui.run_javascript(f'typewriterEffect("{eid}", {json.dumps(text)}, 18)'), once=True)
                                ui.html(f'<div class="math-scroll-container math-label text-lg">$$ {paso["matriz"]} $$</div>')

                if respuesta.get("back_substitution_steps") or respuesta.get("verification_steps_latex"):
                    with ui.expansion('Detalles y Comprobación', icon='fact_check').classes('w-full panel-card mt-4').props('header-class="font-bold text-main"'):
                        if respuesta.get("back_substitution_steps"):
                            ui.label('Sustitución:' if self.method_tabs.value == 'gauss' else 'Solución Final:').classes('font-bold text-sm text-sec mt-2')
                            for paso in respuesta["back_substitution_steps"]:
                                ui.html(f'<div class="math-scroll-container math-label w-full">$$ {format_step_for_mathjax(paso)} $$</div>')

                        if respuesta.get("verification_steps_latex"):
                            ui.label('Comprobación Ax = b:').classes('font-bold text-sm text-sec mt-4')
                            for paso in respuesta["verification_steps_latex"]:
                                ui.html(f'<div class="math-scroll-container math-label">$$ {format_step_for_mathjax(paso)} $$</div>')

        if not is_error:
            self._add_to_history(matrix_A_vals, vector_b_vals, len(matrix_A_vals), len(matrix_A_vals[0]) if matrix_A_vals else 0, status, self.method_tabs.value)

        ui.run_javascript('typesetMathWhenReady();')

        with self.contenedor_resultados:
            if not is_error:
                await self.render_graphics(matrix_A_vals, vector_b_vals, respuesta)

        ui.run_javascript("replayResultAnimation('resultados-container');")
        ui.run_javascript("setTimeout(() => { const el = document.getElementById('resultados-container'); if(el) el.scrollIntoView({behavior: 'smooth', block: 'start'}) }, MOTION.med);")

    def trigger_flip_animation(self):
        ui.run_javascript('''
            const panel = document.querySelector('.main-grid-panel');
            if(panel) {
                panel.classList.remove('animate-slide-bounce');
                void panel.offsetWidth; // trigger reflow
                panel.classList.add('animate-slide-bounce');
            }
        ''')

