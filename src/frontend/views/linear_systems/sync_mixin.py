"""Mixin de sincronización bidireccional y validación de vacíos para Sistemas Lineales."""
from nicegui import ui
from src.backend.utils.parsers import SystemParser


class LinearSystemsSyncMixin:
    """Maneja la lista de ecuaciones, su sincronización con la matriz y verificación de estado vacío."""

    def add_eq(self):
        if self.num_ecuaciones < 10:
            self.num_ecuaciones += 1
            self.render_ecuaciones()

    def remove_eq(self):
        if self.num_ecuaciones > 1:
            self.num_ecuaciones -= 1
            self.render_ecuaciones()
            self.update_sync_buttons()

    def _on_equations_change(self, e=None):
        self.update_sync_buttons()
        self._trigger_live_preview()

    def render_ecuaciones(self):
        backup_vals = [inp.value for inp in self.ecuaciones_inputs]
        if self.contenedor_ecuaciones_lista:
            self.contenedor_ecuaciones_lista.clear()
            self.ecuaciones_inputs.clear()
            with self.contenedor_ecuaciones_lista:
                for i in range(self.num_ecuaciones):
                    val = backup_vals[i] if i < len(backup_vals) else ''
                    with ui.row().classes('w-full items-center gap-3 no-wrap mb-3'):
                        ui.label(f'{i+1}.').classes('font-bold text-sec w-6 text-right')
                        inp = ui.input(
                            value=val,
                            placeholder=f'Ej. 2x + 3y = {i*2 + 4}',
                            on_change=self._on_equations_change
                        ).classes('matrix-input flex-1').props(f'borderless autocomplete="new-password" name="eq{i}"')
                        self.ecuaciones_inputs.append(inp)

    def sync_from_matrix(self):
        eqs = self.grid.export_to_equations(preserve_shape=True)
        self.num_ecuaciones = max(len(eqs), 1)

        if self.contenedor_ecuaciones_lista:
            self.contenedor_ecuaciones_lista.clear()
            self.ecuaciones_inputs.clear()
            with self.contenedor_ecuaciones_lista:
                for i in range(self.num_ecuaciones):
                    val = eqs[i] if i < len(eqs) else ''
                    with ui.row().classes('w-full items-center gap-3 no-wrap mb-3'):
                        ui.label(f'{i+1}.').classes('font-bold text-sec w-6 text-right')
                        inp = ui.input(
                            value=val,
                            placeholder=f'Ej. 2x + 3y = {i*2 + 4}',
                            on_change=self._on_equations_change
                        ).classes('matrix-input flex-1').props(f'borderless autocomplete="new-password" name="eq{i}"')
                        self.ecuaciones_inputs.append(inp)

        self.update_sync_buttons()
        ui.notify('Sincronizado desde Matriz', type='positive', position='top')

    def sync_from_equations(self):
        lineas = [inp.value or "" for inp in self.ecuaciones_inputs]
        raw_text = "\n".join(lineas)
        success, parsed_matrix, variables, msg = SystemParser.parse_system(raw_text, strict_variables=False)

        if not success:
            ui.notify(f'Error al sincronizar: {msg}', type='negative', position='top')
            return

        self.grid.import_from_parsed(parsed_matrix)
        ui.notify('Sincronizado desde Ecuaciones', type='positive', position='top')

    def is_matriz_empty(self):
        matrix_A, vector_b = self.grid.get_matrix_data()
        for row in matrix_A:
            for val in row:
                if val and str(val).strip() != '' and str(val).strip() != '0':
                    return False
        for val in vector_b:
            if val and str(val).strip() != '' and str(val).strip() != '0':
                return False
        return True

    def is_ecuaciones_empty(self):
        for inp in self.ecuaciones_inputs:
            if inp.value and str(inp.value).strip() != '' and str(inp.value).strip() != '0':
                return False
        return True

    def is_empty(self):
        if self.mode_tabs.value == 'Matriz':
            return self.is_matriz_empty()
        else:
            return self.is_ecuaciones_empty()

    def is_strictly_empty(self):
        if self.mode_tabs.value == 'Matriz':
            return self.grid.is_strictly_empty()
        else:
            for inp in self.ecuaciones_inputs:
                if inp.value and str(inp.value).strip() != '':
                    return False
            return True

    def update_sync_buttons(self, _=None):
        if hasattr(self, 'sync_btn_from_eq') and self.sync_btn_from_eq:
            self.sync_btn_from_eq.set_visibility(not self.is_ecuaciones_empty())
        if hasattr(self, 'sync_btn_from_matrix') and self.sync_btn_from_matrix:
            self.sync_btn_from_matrix.set_visibility(not self.is_matriz_empty())

    def _on_grid_change(self):
        self._trigger_live_preview()
        self.update_sync_buttons()
