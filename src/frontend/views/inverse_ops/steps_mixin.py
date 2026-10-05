"""Mixin para la visualización interactiva y reproducción paso a paso del algoritmo de inversión."""
from __future__ import annotations

import html
import json
import logging
from nicegui import ui

from src.frontend.views.inverse_ops._config import AUTOPLAY_SPEEDS
from src.frontend.views.inverse_ops._render import (
    augmented_table_html,
    kind_chip_html,
)

logger = logging.getLogger(__name__)


class InverseOpsStepsMixin:
    """Maneja la sección de pasos, reproductor interactivo y el índice didáctico por fases."""

    def _render_steps_section(self, result: dict):
        """Renderiza el reproductor y el índice didáctico de pasos."""
        steps = result.get("steps", [])
        groups = result.get("groups", [])
        n = result.get("n", self.square_panel.n)
        n_steps = len(steps)

        if n_steps == 0:
            return

        self.step_result = result
        self.current_step = 0

        # 8.1 Encabezado
        ui.label('Procedimiento paso a paso').classes('font-bold mt-6 text-xl text-main')

        # 8.2 Expansión "¿Cómo leer los pasos?"
        with ui.expansion('¿Cómo leer los pasos?', icon='help_outline').classes(
            'w-full panel-card mt-2'
        ).props('default-opened header-class="font-bold text-main"'):
            with ui.column().classes('p-4 gap-2 text-sm'):
                ui.label(
                    '• La tabla es la matriz aumentada [A | I]: a la izquierda va A y a la derecha la identidad. '
                    'La línea verde las separa.'
                ).classes('text-main')
                ui.label(
                    '• Cada paso aplica UNA operación elemental de fila a la fila completa (ambos bloques a la vez).'
                ).classes('text-main')
                ui.label(
                    '• Meta: que el bloque izquierdo quede igual a I. Cuando eso pasa, el bloque derecho es A⁻¹.'
                ).classes('text-main')
                ui.label(
                    '• Colores: fila resaltada = fila modificada en ese paso · celda con borde = pivote · '
                    'ámbar = filas intercambiadas · verde (último paso) = A⁻¹.'
                ).classes('text-main')

                with ui.row().classes('items-center gap-3 flex-wrap mt-3 pt-3 border-t border-[var(--border-input)]'):
                    ui.label('Leyenda de operaciones:').classes('font-bold text-sec text-xs mr-2')
                    for k in ('inicial', 'intercambio', 'pivote', 'eliminacion', 'normalizacion'):
                        ui.html(kind_chip_html(k))

        # 8.3 Reproductor
        with ui.column().classes('w-full panel-card p-4 gap-3 mt-4').props('id="step-card-inv"'):
            # Fila superior de información
            with ui.row().classes('w-full justify-between items-center flex-wrap gap-2'):
                with ui.row().classes('items-center gap-3'):
                    self.step_label_idx = ui.label('').classes(
                        'font-bold text-main text-base font-mono'
                    )
                    self.step_chip = ui.html('')
                self.step_phase = ui.label('').classes('text-sec fs-small font-medium')

            # Barra de progreso
            self.step_progress = ui.linear_progress(value=0, show_value=False).classes(
                'inv-progress w-full'
            )

            # Textos descriptivos del paso
            with ui.row().classes('w-full justify-between items-start gap-2'):
                with ui.column().classes('flex-1 gap-1'):
                    self.step_desc = ui.label('').classes('font-semibold text-main text-sm')
                    self.step_expl = ui.html('').classes('w-full')
                self.step_explain_btn_container = ui.row()

            # Bloque visual de la matriz aumentada
            with ui.column().classes('w-full items-center my-2'):
                ui.label('Bloque izquierdo: A → I · Bloque derecho: I → A⁻¹').classes(
                    'text-sec fs-small mb-2'
                )
                self.step_table_container = ui.column().classes('w-full items-center')

            # Controles de navegación y autoplay (solo si hay más de 1 paso)
            if n_steps > 1:
                with ui.row().classes('w-full items-center justify-between gap-4 mt-2 flex-wrap'):
                    with ui.row().classes('items-center gap-1'):
                        ui.button(
                            icon='first_page',
                            color=None,
                            on_click=lambda: self._goto_step(0),
                        ).classes('btn-neo-icon w-9 h-9 p-0').props('ripple=false aria-label="Primer paso"').tooltip('Primer paso')

                        ui.button(
                            icon='chevron_left',
                            color=None,
                            on_click=lambda: self._goto_step(self.current_step - 1),
                        ).classes('btn-neo-icon w-9 h-9 p-0').props('ripple=false aria-label="Paso anterior"').tooltip('Paso anterior')

                        self.btn_play = ui.button(
                            icon='play_arrow',
                            color=None,
                            on_click=self._toggle_play,
                        ).classes('btn-neo-icon w-9 h-9 p-0').props('ripple=false aria-label="Reproducción automática"').tooltip('Reproducción automática')

                        ui.button(
                            icon='chevron_right',
                            color=None,
                            on_click=lambda: self._goto_step(self.current_step + 1),
                        ).classes('btn-neo-icon w-9 h-9 p-0').props('ripple=false aria-label="Paso siguiente"').tooltip('Paso siguiente')

                        ui.button(
                            icon='last_page',
                            color=None,
                            on_click=lambda: self._goto_step(n_steps - 1),
                        ).classes('btn-neo-icon w-9 h-9 p-0').props('ripple=false aria-label="Último paso"').tooltip('Último paso')

                        ui.select(
                            list(AUTOPLAY_SPEEDS.keys()),
                            value='Normal',
                            on_change=self._on_speed_change,
                        ).classes('neo-select w-28 text-xs').props('dense popup-content-class="neo-select-menu"')

                    self.step_slider = ui.slider(
                        min=0,
                        max=n_steps - 1,
                        step=1,
                        value=0,
                        on_change=self._on_slider_change,
                    ).classes('inv-slider flex-1 min-w-[160px]').props('label')

                # Timer para autoplay
                self.play_timer = ui.timer(
                    AUTOPLAY_SPEEDS['Normal'],
                    self._tick,
                    active=False,
                )

        # 8.4 Índice por fases con carga perezosa
        with ui.expansion('Índice de pasos por fases', icon='list').classes(
            'w-full panel-card mt-4 timeline-expansion'
        ).props('header-class="font-bold text-main"'):
            with ui.column().classes('w-full p-2 gap-2'):
                for g_idx, group in enumerate(groups):
                    title = group.get("title", f"Fase {g_idx + 1}")
                    summary = group.get("summary", "")
                    step_indices = group.get("step_indices", [])

                    with ui.expansion(title, caption=summary).classes(
                        'w-full border border-[var(--border-input)] rounded-lg'
                    ).props('header-class="font-semibold text-main text-sm"') as exp:
                        content_box = ui.column().classes('w-full p-2 gap-1')

                        def make_lazy_loader(box, s_indices):
                            loaded = [False]

                            def on_change(e):
                                if e.value and not loaded[0]:
                                    loaded[0] = True
                                    with box:
                                        for s_idx in s_indices:
                                            if s_idx < n_steps:
                                                st = steps[s_idx]
                                                chip_k = "final" if s_idx == n_steps - 1 else st["kind"]
                                                with ui.button(
                                                    color=None,
                                                    on_click=lambda e, target_idx=s_idx: self._select_step_from_index(target_idx),
                                                ).classes('btn-ghost w-full justify-start py-2 px-3 text-left').props('ripple=false'):
                                                    with ui.row().classes('items-center gap-3 w-full'):
                                                        ui.html(kind_chip_html(chip_k))
                                                        ui.label(f"{s_idx + 1}. {st['description']}").classes(
                                                            'text-sm font-medium text-main'
                                                        )

                            return on_change

                        exp.on_value_change(make_lazy_loader(content_box, step_indices))

        # Renderizar paso 0 inicial
        self._goto_step(0)

    def _goto_step(self, i: int, *, is_autoplay: bool = False):
        """Navega al paso i actualizando el reproductor y la visualización."""
        if not self.step_result:
            return
        steps = self.step_result.get("steps", [])
        n_steps = len(steps)
        if n_steps == 0:
            return

        i = max(0, min(i, n_steps - 1))
        self.current_step = i

        if hasattr(self, 'step_slider') and self.step_slider and self.step_slider.value != i:
            self.step_slider.value = i

        self._update_step_view(is_autoplay=is_autoplay)
        ui.run_javascript("if(window.flashStepCard) flashStepCard('step-card-inv');")

        if is_autoplay and i == n_steps - 1:
            self._stop_play()

    def _update_step_view(self, *, is_autoplay: bool = False):
        """Actualiza los componentes internos del reproductor con el paso actual."""
        if not self.step_result:
            return
        steps = self.step_result.get("steps", [])
        groups = self.step_result.get("groups", [])
        n = self.step_result.get("n", self.square_panel.n)
        n_steps = len(steps)

        step = steps[self.current_step]
        is_last = (self.current_step == n_steps - 1)

        # 1. Labels superiores
        self.step_label_idx.set_text(f"Paso {self.current_step + 1} de {n_steps}")
        chip_kind = "final" if is_last else step["kind"]
        self.step_chip.set_content(kind_chip_html(chip_kind))

        group_title = ""
        g_idx = step.get("group_index")
        if g_idx is not None and 0 <= g_idx < len(groups):
            group_title = groups[g_idx].get("title", "")
        self.step_phase.set_text(group_title)

        # 2. Barra de progreso
        self.step_progress.set_value((self.current_step + 1) / n_steps)

        # 3. Descripción y Explicación
        self.step_desc.set_text(step.get("description", ""))
        
        if getattr(self, 'ai_panel', None):
            self.step_explain_btn_container.clear()
            with self.step_explain_btn_container:
                from src.frontend.components.glosa_chips import render_explain_button
                from src.frontend.controllers.inverse_ops.controller_inverse_ops import InverseOpsController
                render_explain_button(
                    self.current_step + 1,
                    n_steps,
                    step.get("description", ""),
                    lambda idx, st=step, s_idx=self.current_step: self.ai_panel.trigger_explain_step({
                        'index': idx,
                        'total': n_steps,
                        'kind': st.get('kind', 'otro'),
                        'op': st.get('description', ''),
                        **InverseOpsController.build_focus_for_step(steps, s_idx)
                    }),
                    is_loading=getattr(self.ai_panel, '_is_sending', False)
                )

        expl_text = step.get("explanation", "")
        if is_autoplay:
            self.step_expl.set_content(
                f'<span class="text-sec text-sm leading-relaxed">{html.escape(expl_text)}</span>'
            )
        else:
            expl_id = f"step-expl-{next(self._uid_counter)}"
            self.step_expl.set_content(
                f'<span id="{expl_id}" class="text-sec text-sm leading-relaxed"></span>'
            )
            ui.run_javascript(f'typewriterEffect("{expl_id}", {json.dumps(expl_text)}, 12);')

        # 4. Tabla de matriz aumentada
        table_html = augmented_table_html(
            step["matrix"],
            n,
            changed_rows=step.get("rows_changed", ()),
            pivot=step.get("pivot"),
            swap_rows=step.get("swap_rows") or (),
            is_final=is_last,
        )
        self.step_table_container.clear()
        with self.step_table_container:
            ui.html(table_html)

    def _tick(self):
        """Avance automático del reproductor."""
        if not self.step_result:
            return
        n_steps = len(self.step_result.get("steps", []))
        if self.current_step < n_steps - 1:
            self._goto_step(self.current_step + 1, is_autoplay=True)
        else:
            self._stop_play()

    def _toggle_play(self):
        """Inicia o pausa la reproducción automática."""
        if not self.play_timer or not self.step_result:
            return
        n_steps = len(self.step_result.get("steps", []))
        if self.play_timer.active:
            self._stop_play()
        else:
            if self.current_step >= n_steps - 1:
                self._goto_step(0)
            self.play_timer.active = True
            if hasattr(self, 'btn_play') and self.btn_play:
                self.btn_play.props('icon=pause')

    def _stop_play(self):
        """Detiene la reproducción automática y restaura el icono del botón."""
        if self.play_timer:
            self.play_timer.active = False
        if hasattr(self, 'btn_play') and self.btn_play:
            self.btn_play.props('icon=play_arrow')

    def _on_speed_change(self, e):
        """Cambia el intervalo de tiempo entre pasos en la reproducción automática."""
        if self.play_timer:
            speed = AUTOPLAY_SPEEDS.get(e.value, 0.6)
            self.play_timer.interval = speed

    def _on_slider_change(self, e):
        """Reacciona al arrastre del slider."""
        val = int(e.value)
        if val != self.current_step:
            self._goto_step(val)

    def _select_step_from_index(self, target_idx: int):
        """Selecciona un paso desde el índice por fases y hace scroll hacia el reproductor."""
        self._goto_step(target_idx)
        ui.run_javascript(
            "document.getElementById('step-card-inv')?.scrollIntoView({behavior:'smooth', block:'center'});"
        )
