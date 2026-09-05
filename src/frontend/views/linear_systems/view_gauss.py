import json
from nicegui import ui
from src.frontend.controllers.linear_systems.controller_gauss import MatrixController
from src.frontend.components.navbar import create_navbar
from src.frontend.components.equation_grid import EquationGrid

class GaussUI:
    def __init__(self):
        self.grid = EquationGrid()
        self.contenedor_resultados = None

    def limpiar_pantalla(self):
        self.contenedor_resultados.clear()
        self.grid.clear()

    def resolver_sistema(self):
        self.contenedor_resultados.clear()
        
        matrix_A_vals, vector_b_vals = self.grid.get_matrix_data()
        payload_dict = {"matrix_A": matrix_A_vals, "vector_b": vector_b_vals}
        json_payload = json.dumps(payload_dict)
        
        respuesta_json_str = MatrixController.process_system(json_payload)
        respuesta = json.loads(respuesta_json_str)
        
        with self.contenedor_resultados:
            if respuesta.get("status") == "error":
                ui.label(respuesta["message"]).classes('text-red-500 font-bold neu-flat p-4')
                return
                
            ui.label('Clasificación: ' + respuesta["classification"]).classes('text-xl font-bold mt-4 text-center')
            
            if respuesta.get("solution"):
                with ui.row().classes('gap-4 my-4 justify-center w-full'):
                    for idx, val in enumerate(respuesta["solution"]):
                        ui.label(f'x{idx+1} = {val}').classes('font-mono text-lg p-4 neu-pressed font-bold')
                        
            if respuesta.get("intermediate_steps_latex"):
                ui.label('Procedimiento:').classes('font-bold mt-6 text-xl w-full text-center')
                for paso in respuesta["intermediate_steps_latex"]:
                    # Tarjetas neumórficas para los pasos
                    with ui.card().classes('w-full items-center p-6 my-4 neu-flat'):
                        ui.label(paso["descripcion"]).classes('text-md font-semibold mb-2')
                        ui.label(f'$$ {paso["matriz"]} $$').classes('text-xl overflow-x-auto max-w-full')
                        
            if respuesta.get("back_substitution_steps"):
                ui.label('Sustitución hacia atrás:').classes('font-bold mt-6 text-xl w-full text-center')
                with ui.card().classes('w-full p-6 my-4 items-center neu-flat'):
                    for paso in respuesta["back_substitution_steps"]:
                        ui.label(f'$$ {paso} $$').classes('text-lg my-2')
                    
            if respuesta.get("verification_steps_latex"):
                ui.label('Comprobación Ax = b:').classes('font-bold mt-6 w-full text-center text-xl')
                with ui.card().classes('w-full p-6 my-4 items-center neu-flat'):
                    for paso in respuesta["verification_steps_latex"]:
                        ui.label(f'$$ {paso} $$').classes('text-lg my-2')
                        
            # Añadir espacio inferior para no superponer con el navbar flotante
            ui.space().classes('h-24')
            ui.run_javascript('if (window.MathJax) { MathJax.typesetPromise(); }')

    def build(self):
        create_navbar()
        self.grid.inject_scripts()
        
        with ui.column().classes('w-full max-w-5xl mx-auto p-6 items-center'):
            ui.label('Eliminación de Gauss').classes('text-4xl font-extrabold mb-6 text-center mt-4 tracking-tight')
            
            self.grid.build_controls()
            self.grid.build_grid_container()
            
            # Botones con estilo Neumórfico
            with ui.row().classes('w-full max-w-sm mx-auto mb-8 gap-6 justify-center'):
                ui.button('Limpiar', on_click=self.limpiar_pantalla, color=None).classes('neu-btn w-32 py-3')
                ui.button('Resolver', on_click=self.resolver_sistema, color=None).classes('neu-btn flex-1 py-3')
                
            self.contenedor_resultados = ui.column().classes('w-full items-center')