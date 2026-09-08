import json
import asyncio
from nicegui import ui
from src.frontend.controllers.linear_systems.controller_gauss import MatrixController
from src.frontend.components.navbar import create_navbar
from src.frontend.components.equation_grid import EquationGrid
from src.backend.utils.parsers import SystemParser

class GaussUI:
    def __init__(self):
        self.grid = EquationGrid()
        self.contenedor_resultados = None
        self.mode_tabs = None
        
        # Estado del modo ecuaciones
        self.num_ecuaciones = 3
        self.ecuaciones_inputs = []
        self.contenedor_ecuaciones_lista = None

    def add_eq(self):
        if self.num_ecuaciones < 10:
            self.num_ecuaciones += 1
            self.render_ecuaciones()

    def remove_eq(self):
        if self.num_ecuaciones > 1:
            self.num_ecuaciones -= 1
            self.render_ecuaciones()

    def render_ecuaciones(self):
        backup_vals = [inp.value for inp in self.ecuaciones_inputs]
        self.contenedor_ecuaciones_lista.clear()
        self.ecuaciones_inputs.clear()
        with self.contenedor_ecuaciones_lista:
            for i in range(self.num_ecuaciones):
                val = backup_vals[i] if i < len(backup_vals) else ''
                with ui.row().classes('w-full items-center gap-3 no-wrap mb-3'):
                    ui.label(f'{i+1}.').classes('font-bold text-sec w-6 text-right')
                    inp = ui.input(value=val, placeholder=f'Ej. 2x + 3y = {i*2 + 4}').classes('matrix-input flex-1').props('borderless')
                    self.ecuaciones_inputs.append(inp)

    async def confirmar_limpieza(self):
        with ui.dialog() as dialog, ui.card().classes('panel-card p-6 min-w-[300px]'):
            ui.label('¿Vaciar datos?').classes('text-xl font-bold mb-4')
            ui.label('Se perderán todos los datos ingresados.').classes('text-sm text-sec mb-6')
            with ui.row().classes('w-full justify-end gap-3'):
                ui.button('Cancelar', on_click=dialog.close, color=None).classes('btn-ghost px-4').props('ripple=false')
                ui.button('Limpiar', on_click=lambda: (self.limpiar_todo(), dialog.close()), color=None).classes('btn-primary px-4 bg-[var(--error)]').props('ripple=false')
        dialog.open()

    def limpiar_todo(self):
        self.grid.clear()
        for inp in self.ecuaciones_inputs:
            inp.value = ''
        self.reset_resultados()

    def reset_resultados(self):
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.icon('receipt_long', size='3rem').style('color: var(--text-placeholder); opacity: 0.5;')
            ui.label('Los resultados detallados aparecerán aquí').classes('mt-4 text-sm font-medium').style('color: var(--text-placeholder);')

    async def resolver_sistema(self, btn):
        btn.props('loading=true')
        await asyncio.sleep(0.1) 
        
        self.contenedor_resultados.clear()

        # Extraer datos según la pestaña activa
        if self.mode_tabs.value == 'Matriz':
            matrix_A_vals, vector_b_vals = self.grid.get_matrix_data()
        else:
            lineas = [inp.value or "" for inp in self.ecuaciones_inputs]
            raw_text = "\n".join(lineas)
            success, parsed_matrix, variables, msg = SystemParser.parse_system(raw_text)
            
            if not success:
                with self.contenedor_resultados:
                    self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
                    with ui.row().classes('items-center gap-2 px-4 py-2 rounded-full badge-error mb-4 w-fit'):
                        ui.icon('close', size='sm')
                        ui.label(msg).classes('font-bold')
                btn.props('loading=false')
                return
            
            matrix_A_vals = [[str(val) for val in row[:-1]] for row in parsed_matrix.data]
            vector_b_vals = [str(row[-1]) for row in parsed_matrix.data]

        payload_dict = {"matrix_A": matrix_A_vals, "vector_b": vector_b_vals}
        respuesta = json.loads(MatrixController.process_system(json.dumps(payload_dict)))
        
        with self.contenedor_resultados:
            self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
            
            if respuesta.get("status") == "error":
                with ui.row().classes('items-center gap-2 px-4 py-2 rounded-full badge-error mb-4 w-fit'):
                    ui.icon('close', size='sm')
                    ui.label("Sin solución" if "Sin Solución" in respuesta["classification"] else respuesta["message"]).classes('font-bold')
            else:
                is_unique = respuesta.get("solution") is not None
                badge_class = 'badge-success' if is_unique else 'badge-warning'
                icon_str = 'check' if is_unique else 'warning_amber'
                
                with ui.row().classes(f'items-center gap-2 px-4 py-2 rounded-full {badge_class} mb-4 w-fit'):
                    ui.icon(icon_str, size='sm')
                    texto_corto = "Solución única" if is_unique else "Infinitas soluciones"
                    ui.label(texto_corto).classes('font-bold')
                
                if respuesta.get("solution"):
                    with ui.row().classes('gap-4 my-4 w-full flex-wrap'):
                        for idx, val in enumerate(respuesta["solution"]):
                            ui.html(f'<i>x</i><sub>{idx+1}</sub> = {val}').classes('text-lg p-3 panel-card font-bold math-label')
                            
                if respuesta.get("intermediate_steps_latex"):
                    ui.label('Procedimiento paso a paso').classes('font-bold mt-6 text-xl text-main')
                    with ui.expansion('Ver pasos matriciales', icon='visibility').classes('w-full panel-card mt-2').props('header-class="font-bold text-main"'):
                        for paso in respuesta["intermediate_steps_latex"]:
                            with ui.column().classes('w-full p-4 border-b border-[var(--border-input)] last:border-0'):
                                ui.label(paso["descripcion"]).classes('text-sm font-semibold mb-2 text-sec')
                                ui.html(f'<div class="math-label overflow-x-auto text-lg w-full">$$ {paso["matriz"]} $$</div>')
                            
                if respuesta.get("back_substitution_steps") or respuesta.get("verification_steps_latex"):
                    with ui.expansion('Detalles y Comprobación', icon='fact_check').classes('w-full panel-card mt-4').props('header-class="font-bold text-main"'):
                        if respuesta.get("back_substitution_steps"):
                            ui.label('Sustitución:').classes('font-bold text-sm text-sec mt-2')
                            for paso in respuesta["back_substitution_steps"]:
                                ui.html(f'<div class="math-label w-full">$$ {paso} $$</div>')
                        if respuesta.get("verification_steps_latex"):
                            ui.label('Comprobación:').classes('font-bold text-sm text-sec mt-4')
                            for paso in respuesta["verification_steps_latex"]:
                                ui.html(f'<div class="math-label w-full">$$ {paso} $$</div>')

        btn.props('loading=false')
        ui.run_javascript('setTimeout(() => { if (window.MathJax) { MathJax.typesetClear(); MathJax.typesetPromise(); } }, 100);')

    def build(self):
        create_navbar()
        self.grid.inject_scripts()
        
        with ui.column().classes('w-full max-w-6xl mx-auto p-6 mt-8'):
            with ui.row().classes('w-full justify-between items-center mb-8'):
                ui.label('Eliminación de Gauss').classes('text-3xl font-bold text-main')
                
                with ui.tabs().classes('neo-tabs').props('dense no-caps') as self.mode_tabs:
                    ui.tab('Matriz', icon='grid_4x4')
                    ui.tab('Ecuaciones', icon='functions')
            
            with ui.row().classes('w-full no-wrap items-start gap-8'):
                with ui.column().classes('flex-1 min-w-[50%]'):
                    
                    with ui.tab_panels(self.mode_tabs, value='Matriz').classes('w-full p-0 overflow-hidden').props('animated transition-prev="slide-right" transition-next="slide-left"'):
                        with ui.tab_panel('Matriz').classes('p-0'):
                            self.grid.build_grid_container()
                            
                        with ui.tab_panel('Ecuaciones').classes('p-0'):
                            with ui.column().classes('w-full panel-card p-6'):
                                with ui.row().classes('w-full justify-between items-center mb-6'):
                                    ui.label('Sistema de Ecuaciones').classes('text-lg font-bold text-main')
                                    with ui.row().classes('gap-2'):
                                        ui.button(icon='remove', on_click=self.remove_eq, color=None).classes('btn-ghost w-8 h-8 p-0').props('ripple=false')
                                        ui.button(icon='add', on_click=self.add_eq, color=None).classes('btn-ghost w-8 h-8 p-0').props('ripple=false')
                                
                                self.contenedor_ecuaciones_lista = ui.column().classes('w-full')
                                self.render_ecuaciones()
                        
                    with ui.row().classes('w-full mt-6 gap-4'):
                        ui.button('Limpiar', on_click=self.confirmar_limpieza, color=None).classes('btn-ghost flex-1 py-3').props('ripple=false')
                        ui.button('Resolver', on_click=lambda e: self.resolver_sistema(e.sender), color=None).classes('btn-primary flex-[2] py-3').props('ripple=false')
                
                self.contenedor_resultados = ui.column().classes('flex-1 panel-card p-6 items-center justify-center min-h-[400px]')
                self.reset_resultados()