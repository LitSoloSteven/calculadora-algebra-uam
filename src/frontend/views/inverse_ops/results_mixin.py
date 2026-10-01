"""Mixin de resolución, comprobaciones y renderizado de resultados para Matriz Inversa."""
from __future__ import annotations

import asyncio
import html
import json
import logging
from nicegui import run, ui

from src.backend.constants import (
    INVERSE_LATEX_MAX_DIMENSION,
)
from src.backend.utils.formatters import format_fraction_str
from src.backend.utils.validators import MatrixValidator
from src.frontend.controllers.inverse_ops.controller_inverse_ops import (
    InverseOpsController,
)
from src.frontend.views.inverse_ops._config import (
    CONFIRM_BIG_N,
    PREVIEW_MAX_N,
)
from src.frontend.views.inverse_ops._render import (
    matrix_table_html,
)

logger = logging.getLogger(__name__)


class InverseOpsResultsMixin:
    """Maneja el preview en vivo, resolución y presentación de la matriz inversa y verificaciones."""

    def _trigger_live_preview(self):
        """Dispara la actualización de la vista previa con debounce."""
        if self.preview_task and not self.preview_task.done():
            self.preview_task.cancel()
        self.preview_task = asyncio.create_task(self._update_preview())

    async def _update_preview(self):
        """Genera y renderiza el preview de la matriz en MathJax."""
        await asyncio.sleep(0.3)
        if not self.preview_container or self.preview_container.is_deleted:
            return

        try:
            self.preview_container.clear()
            with self.preview_container:
                n = self.square_panel.n
                data = self.square_panel.get_matrix_data()

                if n > PREVIEW_MAX_N:
                    ui.label(f'Vista previa disponible hasta {PREVIEW_MAX_N}×{PREVIEW_MAX_N}.').classes(
                        'text-sec italic text-sm mt-4 text-center'
                    )
                    return

                def sanitize(val: str) -> str:
                    if not val or val == '0':
                        return '0'
                    ok, _, _ = MatrixValidator.parse_number_exact(val)
                    if not ok:
                        return r"\color{gray}{?}"
                    return val

                latex_rows = []
                for row in data:
                    latex_rows.append(" & ".join(sanitize(v) for v in row))
                matrix_a_tex = html.escape(
                    r"\begin{bmatrix} " + r" \\ ".join(latex_rows) + r" \end{bmatrix}"
                )

                ui.html(
                    f'<div id="preview-a" class="math-scroll-container math-label text-lg mb-4 w-full text-center">$$ A = {matrix_a_tex} $$</div>'
                )
                typeset_ids = ['preview-a']

                if n <= 6:
                    aug_rows = []
                    for i, row in enumerate(data):
                        left_str = " & ".join(sanitize(v) for v in row)
                        right_str = " & ".join('1' if i == j else '0' for j in range(n))
                        aug_rows.append(f"{left_str} & {right_str}")
                    spec = "c" * n + "|" + "c" * n
                    aug_tex = html.escape(
                        rf"\left[ \begin{{array}}{{{spec}}} "
                        + r" \\ ".join(aug_rows)
                        + r" \end{array} \right]"
                    )
                    ui.html(
                        rf'<div id="preview-aug" class="math-scroll-container math-label text-base w-full text-center">$$ [A \mid I] = {aug_tex} $$</div>'
                    )
                    typeset_ids.append('preview-aug')

                ui.run_javascript(f"typesetMathWhenReady({json.dumps(typeset_ids)});")
        except Exception as e:
            if not self.preview_container or self.preview_container.is_deleted:
                return
            logger.error("Error al actualizar vista previa de matriz inversa", exc_info=e)
            with self.preview_container:
                ui.label('No se pudo generar la vista previa.').classes(
                    'text-sec italic text-sm mt-4 text-center'
                )

    def reset_resultados(self):
        """Restaura el estado inicial y placeholder de la tarjeta de resultados."""
        if not self.contenedor_resultados:
            return
        self.contenedor_resultados.clear()
        self.contenedor_resultados.style('opacity: 1;')
        self.contenedor_resultados.classes(
            remove='items-start justify-start',
            add='items-center justify-center',
        )
        with self.contenedor_resultados:
            ui.icon('flip', size='4rem').classes('text-placeholder mb-4')
            ui.label('Listo para invertir').classes('text-xl font-bold text-main')
            ui.label(
                'Ingresá una matriz cuadrada y presioná Calcular inversa'
            ).classes('text-sm text-sec mt-2 text-center')

    def _on_matrix_change(self):
        """Handler reactivo invocado cuando el usuario edita o redimensiona la matriz."""
        self._trigger_live_preview()
        if self.last_result is not None and self.contenedor_resultados:
            self.contenedor_resultados.style('opacity: 0.45;')

    async def confirmar_limpieza(self):
        """Muestra el diálogo neumórfico para confirmar el vaciado de datos."""
        if self.square_panel.is_empty():
            ui.notify('El sistema ya está vacío', type='warning', position='top')
            return

        with ui.dialog() as dialog, ui.card().classes('panel-card no-shadow p-6 min-w-[300px]'):
            ui.label('¿Vaciar datos?').classes('text-xl font-bold mb-4')
            ui.label('Se animarán y eliminarán los datos.').classes('text-sm text-sec mb-6')
            with ui.row().classes('w-full justify-end gap-3'):
                ui.button('Cancelar', on_click=dialog.close, color=None).classes('btn-ghost px-4').props('ripple=false')
                ui.button(
                    'Limpiar',
                    on_click=lambda: self.ejecutar_animacion_limpieza(dialog),
                    color=None,
                ).classes('btn-primary px-4').style('background: var(--error); color: white;').props('ripple=false')
        dialog.open()

    async def ejecutar_animacion_limpieza(self, dialog):
        """Ejecuta la animación de recolección de basura y limpia la matriz."""
        dialog.close()
        ui.run_javascript('animateGarbageCollection()')
        await asyncio.sleep(0.8)
        self.limpiar_todo()

    def limpiar_todo(self):
        """Limpia los inputs de la matriz y el panel de resultados."""
        self.square_panel.clear()
        self.last_result = None
        self.reset_resultados()

    async def calcular(self, sender):
        """Punto de entrada para validar, confirmar (si n es grande) y ejecutar el cálculo."""
        if self.square_panel.is_strictly_empty():
            self.contenedor_resultados.clear()
            self.contenedor_resultados.style('opacity: 1;')
            self.contenedor_resultados.classes(
                remove='items-center justify-center', add='items-start justify-start'
            )
            with self.contenedor_resultados:
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-warning mb-4 w-fit'):
                    ui.icon('warning', size='sm')
                    ui.label('Ingresá al menos un valor antes de calcular.').classes('font-bold')
            return

        n = self.square_panel.n
        if n >= CONFIRM_BIG_N:
            with ui.dialog() as dialog, ui.card().classes('panel-card no-shadow p-6 min-w-[320px]'):
                ui.label('Confirmar cálculo').classes('text-xl font-bold mb-3')
                ui.label(
                    f'Una dimensión n={n} ({n}×{n}) puede tardar unos segundos y consumir bastante memoria. '
                    f'¿Deseas continuar?'
                ).classes('text-sm text-sec mb-6')
                with ui.row().classes('w-full justify-end gap-3'):
                    ui.button('Cancelar', on_click=lambda: dialog.submit(False), color=None).classes('btn-ghost px-4').props('ripple=false')
                    ui.button('Continuar', on_click=lambda: dialog.submit(True), color=None).classes('btn-primary px-4').props('ripple=false')
            ok = await dialog
            if not ok:
                return

        sender.props('loading=true')
        self.contenedor_resultados.clear()
        self.contenedor_resultados.style('opacity: 1;')
        self.contenedor_resultados.classes(
            remove='items-start justify-start', add='items-center justify-center'
        )

        with self.contenedor_resultados:
            ui.spinner(size='3rem').classes('text-accent mb-4')
            msg_calc = 'Calculando inversa...'
            if n >= 20:
                msg_calc += ' (matrices grandes pueden tardar)'
            ui.label(msg_calc).classes('text-sec font-semibold')

        try:
            payload = json.dumps({"n": n, "data": self.square_panel.get_matrix_data()})
            result = await run.io_bound(InverseOpsController.process_inverse, payload)

            if self.contenedor_resultados.is_deleted:
                return

            self.last_result = result
            self.contenedor_resultados.style('opacity: 1;')
            self._render_result(result)

            if result.get("status") in ("SUCCESS", "SINGULAR"):
                self._add_to_history(
                    self.square_panel.get_matrix_data(),
                    n,
                    result["status"],
                    result.get("determinant_str"),
                )

            ui.run_javascript('typesetMathWhenReady();')
            ui.run_javascript("if(window.replayResultAnimation) replayResultAnimation('resultados-inv');")
            ui.run_javascript(
                "document.getElementById('resultados-inv')?.scrollIntoView({behavior: 'smooth', block: 'start'});"
            )

        except Exception as e:
            self._mostrar_error_inesperado(e)
        finally:
            if not sender.is_deleted:
                sender.props('loading=false')

    def _mostrar_error_inesperado(self, exc: Exception):
        """Muestra un badge de error ante excepciones no controladas."""
        if self.contenedor_resultados.is_deleted:
            return
        logger.error("Error inesperado en calcular matriz inversa", exc_info=exc)
        self.contenedor_resultados.clear()
        self.contenedor_resultados.classes(
            remove='items-center justify-center', add='items-start justify-start'
        )
        with self.contenedor_resultados:
            with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                ui.icon('close', size='sm')
                ui.label(
                    'Ocurrió un error inesperado al procesar la matriz inversa. Revisa los datos e inténtalo de nuevo.'
                ).classes('font-bold')
        ui.notify('Error inesperado', type='negative', position='top')

    def _render_result(self, result: dict):
        """Renderiza la sección de resultados según el estado (ERROR, SINGULAR o SUCCESS)."""
        self.contenedor_resultados.clear()
        self.contenedor_resultados.classes(
            remove='items-center justify-center', add='items-start justify-start'
        )

        status = result.get("status", "ERROR")
        n = result.get("n", self.square_panel.n)

        with self.contenedor_resultados:
            # 1. CASO ERROR
            if status == "ERROR":
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                    ui.icon('error', size='sm')
                    ui.label(result.get('message', 'Error en los datos ingresados.')).classes('font-bold')
                if result.get('error_cell'):
                    r, c = result['error_cell']
                    self.square_panel.flash_cell(r, c)
                    ui.notify(result.get('message', 'Celda inválida'), type='negative')
                return

            # 2. CASO SINGULAR
            if status == "SINGULAR":
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                    ui.icon('warning', size='sm')
                    ui.label('Matriz singular: no tiene inversa').classes('font-bold')

                with ui.column().classes('panel-card p-6 w-full mb-6 gap-3'):
                    ui.label('Matriz Singular (det = 0)').classes('text-lg font-bold text-main')
                    ui.label(
                        'Una matriz cuadrada tiene inversa si y solo si det(A) ≠ 0. '
                        'Aquí det(A) = 0, por lo tanto no es posible obtener un pivote en cada columna.'
                    ).classes('text-sm text-sec')

                    ui.label('Matriz evaluada A:').classes('text-sm font-semibold text-main mt-2')
                    if n <= INVERSE_LATEX_MAX_DIMENSION and result.get('matrix_a_latex'):
                        ui.html(
                            f'<div class="math-scroll-container math-label text-base">$$ A = {result["matrix_a_latex"]} $$</div>'
                        )
                    elif result.get('matrix_a'):
                        ui.html(matrix_table_html(result['matrix_a']))

                if result.get('steps'):
                    self._render_steps_section(result)
                return

            # 3. CASO SUCCESS
            # 3.1 Badge éxito con typewriter
            badge_id = f"badge-inv-{next(self._uid_counter)}"
            with ui.row().classes('items-center gap-2 px-4 py-2 badge-success mb-4 w-fit'):
                ui.icon('check_circle', size='sm')
                ui.html(f'<span id="{badge_id}"></span>').classes('font-bold')
            ui.run_javascript(f"typewriterEffect('{badge_id}', 'Matriz invertible', 20);")

            # 3.2 Fila de chips resumen
            with ui.row().classes('panel-card px-4 py-2 fs-small items-center gap-4 flex-wrap mb-6 w-full'):
                ui.label(f"{n} × {n}").classes('font-bold text-main')
                ui.label(f"det(A) = {result['determinant_str']} ≠ 0").classes('font-semibold text-main')
                ui.label(f"{result['stats']['total']} pasos").classes('text-sec')
                ui.label(f"{result['stats']['intercambios']} intercambios").classes('text-sec')
                ui.label(f"calculado en {result['elapsed_s']:.2f} s").classes('text-sec')

            # 3.3 Tarjeta Resultado A⁻¹
            with ui.column().classes('panel-card p-6 w-full mb-6'):
                ui.label('Resultado: A⁻¹').classes('text-lg font-bold text-main mb-4')

                if n <= INVERSE_LATEX_MAX_DIMENSION:
                    with ui.row().classes('items-center justify-center gap-6 flex-wrap w-full my-4'):
                        ui.html(
                            f'<div class="math-scroll-container math-label text-base">$$ A = {result["matrix_a_latex"]} $$</div>'
                        )
                        ui.icon('arrow_forward', size='md').classes('text-sec')
                        ui.html(
                            f'<div class="math-scroll-container math-label text-base">$$ A^{{-1}} = {result["inverse_latex"]} $$</div>'
                        )
                else:
                    with ui.row().classes('items-start justify-center gap-8 flex-wrap w-full my-4'):
                        with ui.column().classes('items-center'):
                            ui.label('A').classes('font-bold text-main mb-2')
                            ui.html(matrix_table_html(result['matrix_a']))
                        with ui.column().classes('items-center'):
                            ui.label('A⁻¹').classes('font-bold text-main mb-2')
                            ui.html(matrix_table_html(result['inverse']))

                def copiar_inversa():
                    inv = result.get('inverse')
                    if not inv:
                        return
                    lines = []
                    for i in range(n):
                        lines.append("\t".join(format_fraction_str(inv.get(i, j)) for j in range(n)))
                    text_to_copy = "\n".join(lines)
                    ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(text_to_copy)});")
                    ui.notify('A⁻¹ copiada al portapapeles', type='positive')

                with ui.row().classes('w-full justify-between items-center mt-4 flex-wrap gap-2'):
                    ui.button(
                        'Copiar A⁻¹',
                        icon='content_copy',
                        on_click=copiar_inversa,
                        color=None,
                    ).classes('btn-ghost text-xs').props('ripple=false')

                with ui.expansion('Ver A⁻¹ en decimales (≈4 cifras)', icon='numbers').classes(
                    'w-full mt-3 panel-card'
                ).props('header-class="font-bold text-main text-sm"'):
                    ui.html(matrix_table_html(result['inverse'], decimals=True))

                ui.label(
                    'Cada columna j de A⁻¹ es la solución x de A·x = eⱼ (eⱼ = columna j de la identidad).'
                ).classes('text-sec fs-small mt-3')

            # 3.4 Expansión Comprobaciones
            with ui.expansion('Comprobaciones formales', icon='verified').classes(
                'w-full mb-6 panel-card'
            ).props('default-opened header-class="font-bold text-main"'):
                with ui.column().classes('w-full gap-4 p-2'):
                    for v in result.get('verifications', []):
                        with ui.row().classes('w-full justify-between items-center gap-4 flex-wrap'):
                            ui.label(v['title']).classes('font-bold text-main text-sm')
                            badge_cls = 'badge-success' if v['coincide'] else 'badge-error'
                            badge_txt = 'Correcto' if v['coincide'] else 'Incorrecto'
                            ui.badge(badge_txt, color=None).classes(badge_cls)
                        if v.get('detail_latex'):
                            ui.html(f'<div class="math-scroll-container math-label text-sm my-1">$$ {v["detail_latex"]} $$</div>')
                    if n > INVERSE_LATEX_MAX_DIMENSION:
                        ui.label('Verificado con aritmética exacta (fracciones).').classes(
                            'text-sec fs-small italic mt-2'
                        )

            # 3.5 Sección de pasos
            self._render_steps_section(result)

            # 3.6 Expansión ¿Cómo interpretar este resultado?
            with ui.expansion('¿Cómo interpretar este resultado?', icon='help_outline').classes(
                'w-full mt-6 panel-card'
            ).props('header-class="font-bold text-main"'):
                ui.label(
                    'A⁻¹ cumple A·A⁻¹ = A⁻¹·A = I. Existe solo si det(A) ≠ 0. '
                    'Todos los valores son exactos (fracciones). (Aᵀ)⁻¹ = (A⁻¹)ᵀ.'
                ).classes('text-sec text-sm p-3')
