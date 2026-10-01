"""Mixin de gestión de historial de cálculos para la vista de Matriz Inversa."""
from __future__ import annotations

import time
from nicegui import ui


class InverseOpsHistoryMixin:
    """Maneja el registro, visualización y restauración del historial de matrices invertidas."""

    def _add_to_history(self, data: list[list[str]], n: int, status: str, det: str | None):
        """Agrega una matriz calculada al historial (máximo 5 elementos)."""
        self.historial.insert(0, {
            'data': data,
            'n': n,
            'status': status,
            'det': det,
            'time': time.strftime("%H:%M"),
        })
        if len(self.historial) > 5:
            self.historial.pop()
        self._render_history()

    def _render_history(self):
        """Dibuja las tarjetas de historial en el contenedor."""
        if not self.historial_container:
            return
        self.historial_container.clear()

        with self.historial_container:
            if not self.historial:
                ui.label('No hay matrices calculadas en esta sesión.').classes(
                    'text-sec italic text-sm mt-4 text-center'
                )
                return

            for h in self.historial:
                with ui.column().classes(
                    'panel-card p-4 w-full mb-3 gap-2 border border-[var(--border-input)]'
                ):
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.badge(f"{h['n']}×{h['n']}", color=None).classes('badge-success font-mono')
                        ui.label(h['time']).classes('text-xs text-sec')

                    status_is_inv = (h['status'] == 'SUCCESS')
                    status_text = 'Invertible' if status_is_inv else 'Singular'
                    status_class = 'text-[var(--accent)]' if status_is_inv else 'text-[var(--error)]'

                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label(status_text).classes(f'text-xs {status_class} font-bold')
                        if h['det'] is not None:
                            ui.label(f"det = {h['det']}").classes('text-xs font-mono text-sec')

                    ui.button(
                        'Restaurar',
                        on_click=lambda e, item=h: self._restore_history(item),
                        color=None,
                    ).classes('btn-ghost text-xs w-full mt-2').props('ripple=false')

    def _restore_history(self, item: dict):
        """Restaura los datos de una matriz guardada en el historial."""
        try:
            self.square_panel.set_data(item['data'])
            ui.notify('Matriz restaurada', type='positive')
        except Exception as e:
            ui.notify(f'Error al restaurar: {e}', type='negative')
