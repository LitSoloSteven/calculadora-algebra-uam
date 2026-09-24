"""Mixin de renderizado de resultados y pasos para Operaciones con Vectores."""
import re
from nicegui import ui
from src.backend.utils.formatters import matrix_to_latex


class VectorOpsResultsMixin:
    """Maneja la visualización de estados vacíos, resultados y procedimientos paso a paso de vectores."""

    def render_empty_state(self):
        if not self.right_panel:
            return
        self.right_panel.clear()
        with self.right_panel:
            with ui.column().classes('w-full h-full justify-center items-center text-center opacity-50'):
                ui.icon('functions', size='4rem').classes('mb-4')
                ui.label('Ingresa los vectores y presiona Calcular').classes('text-lg')

    def render_result(self, res: dict):
        self.right_panel.clear()

        with self.right_panel:
            status = res.get('status', 'ERROR')
            msg = res.get('message', '')

            if status == 'ERROR':
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-6 w-fit'):
                    ui.icon('close', size='sm')
                    ui.label(msg).classes('font-bold')
                return

            if self.active_op == 'lin_comb':
                if status == 'UNIQUE':
                    badge_class, icon = 'badge-success', 'check'
                elif status == 'INFINITE':
                    badge_class, icon = 'badge-warning', 'warning_amber'
                else:  # NO_SOLUTION
                    badge_class, icon = 'badge-error', 'close'
            else:
                badge_class, icon = 'badge-success', 'check'

            with ui.row().classes(f'items-center gap-2 px-4 py-2 {badge_class} mb-6 w-fit'):
                ui.icon(icon, size='sm')
                ui.label(msg).classes('font-bold')

            if self.active_op in ['add_sub', 'scalar']:
                self.render_steps_and_result(res)
            else:
                self.render_linear_combination_result(res)

    def render_steps_and_result(self, res: dict):
        final_latex = res.get('result_vector_latex')
        if not final_latex and 'latex_details' in res and res['latex_details']:
            final_latex = res['latex_details'][-1]

        if final_latex:
            ui.label('Resultado').classes('text-xl font-bold mb-4 text-main')
            with ui.card().classes('panel-card w-full p-6 mb-6 items-center justify-center'):
                ui.html(f'<div class="math-label overflow-x-auto p-4 text-lg text-center">$$ {final_latex} $$</div>')

        steps = res.get('steps', [])
        if len(steps) > 1:
            with ui.expansion('Ver Pasos de Resolución', icon='list').classes(
                'w-full panel-card rounded-xl overflow-hidden'
            ).props('header-class="text-main font-bold"'):
                with ui.column().classes('w-full p-4 gap-6 bg-[var(--input-bg)]'):
                    for i, step in enumerate(steps, start=1):
                        desc = step.get('description', '')
                        latex = step.get('detail_latex', '')

                        if not latex and step.get('matrix'):
                            latex = matrix_to_latex(step['matrix'])

                        with ui.column().classes('w-full'):
                            ui.label(f'Paso {i}: {desc}').classes('text-sm font-bold text-sec mb-2')
                            if latex:
                                ui.html(
                                    f'<div class="math-label bg-[var(--bg-elevated)] p-4 rounded-lg shadow-sm border border-[var(--border-input)] overflow-x-auto text-center">$$ {latex} $$</div>'
                                )

    def render_linear_combination_result(self, res: dict):
        status = res.get('status')

        if status == 'UNIQUE':
            coef_str = ", ".join(res.get('coeficientes_str', []))
            ui.markdown(f"**Coeficientes:** `{coef_str}`").classes('mb-4')

            v_step = res.get('verification_step')
            if v_step:
                with ui.card().classes('panel-card w-full p-4 mb-6'):
                    ui.label('Verificación formal (y = c₁v₁ + ... + cᵣvᵣ):').classes('font-bold mb-2')
                    detail_tex = v_step.get("detail_latex") or v_step.get("formula_latex", "")
                    if detail_tex:
                        ui.html(f'<div class="math-label overflow-x-auto">$$ {detail_tex} $$</div>')

        elif status == 'INFINITE':
            sol_str = ", ".join(res.get('solucion_parametrica', []))
            ui.markdown(f"**Solución paramétrica:** `{sol_str}`").classes('mb-4')
            ui.markdown(f"**Variables libres:** `{', '.join(res.get('parametros_libres', []))}`").classes('mb-4')

        # 1. ACORDEÓN DE PLANTEAMIENTO ALGEBRAICO
        setup_steps = res.get('setup_steps', [])
        if setup_steps:
            with ui.expansion('Ver Planteamiento Algebraico', icon='view_timeline').classes(
                'w-full panel-card rounded-xl overflow-hidden mb-4'
            ).props('header-class="text-main font-bold" default-opened'):
                with ui.column().classes('w-full p-4 gap-6 bg-[var(--input-bg)]'):
                    for step in setup_steps:
                        desc = step.get('description', '')
                        latex = step.get('detail_latex', '')
                        with ui.column().classes('w-full'):
                            ui.label(desc).classes('text-sm font-bold text-sec mb-2')
                            if latex:
                                ui.html(
                                    f'<div class="math-label bg-[var(--bg-elevated)] p-4 rounded-lg shadow-sm border border-[var(--border-input)] overflow-x-auto text-center">$$ {latex} $$</div>'
                                )

        # 2. ACORDEÓN DE ELIMINACIÓN GAUSSIANA
        # Preferir 'gauss_steps' (solo eliminación). Fallback a 'steps' omitiendo setup_steps si vinieran mezclados.
        gauss_steps = res.get('gauss_steps')
        if gauss_steps is None:
            raw_steps = res.get('steps', [])
            gauss_steps = raw_steps[len(setup_steps):] if setup_steps else raw_steps

        if gauss_steps:
            with ui.expansion('Ver Eliminación Gaussiana', icon='calculate').classes(
                'w-full panel-card rounded-xl overflow-hidden mb-4'
            ).props('header-class="text-main font-bold"'):
                with ui.column().classes('w-full p-4 gap-6 bg-[var(--input-bg)]'):
                    for i, step in enumerate(gauss_steps, start=1):
                        desc = step.get('description', '')
                        desc = re.sub(r'^\d+\.\s*', '', desc)
                        latex = step.get('detail_latex', '')
                        if not latex and step.get('matrix'):
                            latex = matrix_to_latex(step['matrix'])

                        with ui.column().classes('w-full'):
                            ui.label(f'Paso {i}: {desc}').classes('text-sm font-bold text-sec mb-2')
                            if latex:
                                ui.html(
                                    f'<div class="math-label bg-[var(--bg-elevated)] p-4 rounded-lg shadow-sm border border-[var(--border-input)] overflow-x-auto text-center">$$ {latex} $$</div>'
                                )

        # 3. ACORDEÓN DE SUSTITUCIÓN HACIA ATRÁS
        back_steps = res.get('back_substitution_steps', [])
        if back_steps:
            with ui.expansion('Ver Sustitución Hacia Atrás', icon='arrow_upward').classes(
                'w-full panel-card rounded-xl overflow-hidden'
            ).props('header-class="text-main font-bold"'):
                with ui.column().classes('w-full p-4 gap-4 bg-[var(--input-bg)]'):
                    for bs in back_steps:
                        ui.html(
                            f'<div class="math-label bg-[var(--bg-elevated)] p-3 rounded-lg shadow-sm border border-[var(--border-input)] overflow-x-auto">$$ {bs} $$</div>'
                        )
