import json
from nicegui import ui
from src.frontend.controllers.linear_systems.controller_gauss import MatrixController
from src.frontend.components.navbar import create_navbar
from src.frontend.components.equation_grid import EquationGrid

class GaussUI:
    def __init__(self):
        # Instancia el componente modular en lugar de reconstruir la cuadrícula manualmente
        self.grid = EquationGrid()
        self.contenedor_resultados = None

    def limpiar_pantalla(self):
        self.contenedor_resultados.clear()
        self.grid.clear()

    def resolver_sistema(self):
        self.contenedor_resultados.clear()
        
        # Obtiene los datos limpios directamente desde el componente
        matrix_A_vals, vector_b_vals = self.grid.get_matrix_data()
        payload_dict = {"matrix_A": matrix_A_vals, "vector_b": vector_b_vals}
        json_payload = json.dumps(payload_dict)
        
        respuesta_json_str = MatrixController.process_system(json_payload)
        respuesta = json.loads(respuesta_json_str)
        
        with self.contenedor_resultados:
            if respuesta.get("status") == "error":
                ui.label(respuesta["message"]).classes('text-red-600 font-bold')
                return
                
            ui.label('Clasificación: ' + respuesta["classification"]).classes('text-lg font-bold text-blue-900 mt-4 text-center')
            
            if respuesta.get("solution"):
                with ui.row().classes('gap-4 my-2 justify-center w-full'):
                    for idx, val in enumerate(respuesta["solution"]):
                        ui.label(f'x{idx+1} = {val}').classes('font-mono text-lg p-2 bg-green-50 rounded border')
                        
            if respuesta.get("intermediate_steps_latex"):
                ui.label('Procedimiento:').classes('font-bold mt-4 text-lg w-full text-center')
                for paso in respuesta["intermediate_steps_latex"]:
                    with ui.card().classes('w-full items-center p-4 my-2 bg-gray-50'):
                        ui.label(paso["descripcion"]).classes('text-md font-semibold text-gray-700 mb-1')
                        ui.label(f'$$ {paso["matriz"]} $$').classes('text-xl overflow-x-auto max-w-full')
                        
            if respuesta.get("back_substitution_steps"):
                ui.label('Sustitución hacia atrás (Despeje de variables):').classes('font-bold mt-4 text-lg w-full text-center')
                with ui.card().classes('w-full p-4 bg-yellow-50 mb-4 items-center'):
                    ui.label("A partir de la matriz escalonada, despejamos cada variable paso a paso:").classes('mb-2 text-gray-700 text-center')
                    for paso in respuesta["back_substitution_steps"]:
                        ui.label(f'$$ {paso} $$').classes('text-lg my-1')
                    
            if respuesta.get("verification_steps_latex"):
                ui.label('Comprobación Ax = b:').classes('font-bold mt-4 w-full text-center')
                with ui.card().classes('w-full p-4 bg-purple-50 items-center'):
                    for paso in respuesta["verification_steps_latex"]:
                        ui.label(f'$$ {paso} $$').classes('text-lg my-1')
                        
            ui.run_javascript('if (window.MathJax) { MathJax.typesetPromise(); }')

    def build(self):
        ui.colors(primary='#005596')
        
        # 1. Inyecta el menú superior
        create_navbar()
        # 2. Inyecta los scripts de configuración matemática y teclado
        self.grid.inject_scripts()
        
        with ui.column().classes('w-full max-w-5xl mx-auto p-6 items-center'):
            ui.label('Eliminación de Gauss').classes('text-3xl font-bold text-primary mb-2 text-center mt-4')
            
            # 3. Construye los componentes visuales de la matriz
            self.grid.build_controls()
            self.grid.build_grid_container()
            
            with ui.row().classes('w-full max-w-sm mx-auto mb-8 gap-4 justify-center'):
                ui.button('A/C', on_click=self.limpiar_pantalla, color='red', icon='delete').classes('w-24')
                ui.button('Resolver Sistema', on_click=self.resolver_sistema, icon='calculate').classes('flex-1')
                
            self.contenedor_resultados = ui.column().classes('w-full items-center')