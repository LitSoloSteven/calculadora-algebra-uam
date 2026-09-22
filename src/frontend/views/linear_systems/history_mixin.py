"""Mixin de gestión de historial de cálculos para Sistemas Lineales."""
import time
from nicegui import ui


class LinearSystemsHistoryMixin:
    """Maneja el registro, visualización y restauración del historial de sistemas resueltos."""

    def _add_to_history(self, matrix_A, vector_b, m, n, status, method):
        self.historial.insert(0, {
            'matrix_A': matrix_A,
            'vector_b': vector_b,
            'm': m,
            'n': n,
            'status': status,
            'method': method,
            'time': time.strftime("%H:%M")
        })
        if len(self.historial) > 5:
            self.historial.pop()
        self._render_history()

    def _render_history(self):
        if not self.historial_container:
            return
        self.historial_container.clear()
        self.historial_container.update()

        with self.historial_container:
            if not self.historial:
                ui.label('No hay sistemas resueltos en esta sesión.').classes('text-sec italic text-sm mt-4 text-center')
                return

            for h in self.historial:
                with ui.column().classes('panel-card p-4 w-full mb-3 gap-2 border border-[var(--border-input)]'):
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.badge(f"{h['m']}×{h['n']}", color=None).classes('badge-success font-mono')
                        ui.label(h['time']).classes('text-xs text-sec')

                    ui.label(f"Método: {h['method'].replace('-', ' ').title()}").classes('text-sm font-bold text-main')

                    status_class = 'text-[var(--accent)]' if h['status'] == 'UNIQUE_SOLUTION' else (
                        'text-warning' if h['status'] == 'INFINITE_SOLUTIONS' else 'text-[var(--error)]'
                    )
                    status_text = 'Solución Única' if h['status'] == 'UNIQUE_SOLUTION' else (
                        'Infinitas Soluciones' if h['status'] == 'INFINITE_SOLUTIONS' else (
                            'Sin Solución' if h['status'] == 'NO_SOLUTION' else 'Error'
                        )
                    )

                    ui.label(status_text).classes(f'text-xs {status_class} font-bold')

                    ui.button(
                        'Restaurar',
                        on_click=lambda e, data=h: self._restore_history(data),
                        color=None
                    ).classes('btn-ghost text-xs w-full mt-2').props('ripple=false')

    def _restore_history(self, data):
        if self.mode_tabs.value == 'Ecuaciones':
            self.mode_tabs.set_value('Matriz')

        self.grid.clear()
        self.grid.m = data['m']
        self.grid.n = data['n']

        self.grid._cache_A.clear()
        self.grid._cache_b.clear()
        for i, row in enumerate(data['matrix_A']):
            for j, val in enumerate(row):
                if val != '0':
                    self.grid._cache_A[(i, j)] = val
        for i, val in enumerate(data['vector_b']):
            if val != '0':
                self.grid._cache_b[i] = val

        self.grid.entradas_A.clear()
        self.grid.entradas_b.clear()
        self.grid.generar_cuadricula()
        self._on_grid_change()

        ui.notify('Matriz restaurada', type='positive')
