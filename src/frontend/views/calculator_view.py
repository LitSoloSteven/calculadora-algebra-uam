import json
from nicegui import ui
from src.frontend.controllers.controllers_matrix import MatrixController

class CalculatorUI:
    def __init__(self):
        # Atributos de estado (reemplazan a las variables globales)
        self.entradas_A = []
        self.entradas_b = []
        self.m_input = None
        self.n_input = None
        self.contenedor_matriz = None
        self.contenedor_resultados = None

    def generar_cuadricula(self):
        self.contenedor_matriz.clear()
        self.entradas_A.clear()
        self.entradas_b.clear()
        
        filas = int(self.m_input.value)
        columnas = int(self.n_input.value)
        
        with self.contenedor_matriz:
            for i in range(filas):
                with ui.row().classes('items-center gap-2 mb-2'):
                    fila_A = []
                    for j in range(columnas):
                        celda = ui.input(label=f'A[{i+1},{j+1}]', value='0').classes('w-16')
                        fila_A.append(celda)
                    self.entradas_A.append(fila_A)
                    
                    ui.label('|').classes('text-2xl font-light text-gray-400 mx-2')
                    
                    celda_b = ui.input(label=f'b[{i+1}]', value='0').classes('w-16 bg-blue-50')
                    self.entradas_b.append(celda_b)

    def resolver_sistema(self):
        self.contenedor_resultados.clear()
        
        # Extraer valores y preparar payload
        matrix_A_vals = [[celda.value for celda in fila] for fila in self.entradas_A]
        vector_b_vals = [celda.value for celda in self.entradas_b]
        
        payload_dict = {"matrix_A": matrix_A_vals, "vector_b": vector_b_vals}
        json_payload = json.dumps(payload_dict)
        
        # Invocar controlador
        respuesta_json_str = MatrixController.process_system(json_payload)
        respuesta = json.loads(respuesta_json_str)
        
        # Renderizar resultados
        with self.contenedor_resultados:
            if respuesta.get("status") == "error":
                ui.label(respuesta["message"]).classes('text-red-600 font-bold')
                return
                
            ui.label('Clasificación: ' + respuesta["classification"]).classes('text-lg font-bold text-blue-900 mt-4')
            
            if respuesta.get("solution"):
                with ui.row().classes('gap-4 my-2'):
                    for idx, val in enumerate(respuesta["solution"]):
                        ui.label(f'x{idx+1} = {val}').classes('font-mono text-lg p-2 bg-green-50 rounded border')
                        
            if respuesta.get("intermediate_steps_latex"):
                ui.label('Procedimiento:').classes('font-bold mt-4')
                for matriz_latex in respuesta["intermediate_steps_latex"]:
                    ui.latex(f'$$ {matriz_latex} $$').classes('text-xl')
                    
            if respuesta.get("verification_steps_latex"):
                ui.label('Comprobación Ax = b:').classes('font-bold mt-4')
                with ui.card().classes('w-full p-4 bg-purple-50'):
                    for paso in respuesta["verification_steps_latex"]:
                        ui.latex(f'$$ {paso} $$').classes('text-lg my-1')

    def build(self):
        """Construye el layout principal de la aplicación."""
        ui.colors(primary='#005596')
        
        with ui.column().classes('w-full max-w-4xl mx-auto p-6'):
            ui.label('Calculadora de Álgebra Lineal - MTM0120').classes('text-3xl font-bold text-primary mb-2')
            
            with ui.row().classes('gap-6 items-center mb-6 p-4 border rounded bg-gray-50'):
                self.m_input = ui.number(label='Ecuaciones', value=3, min=1, max=10, format='%.0f', on_change=self.generar_cuadricula).classes('w-32')
                self.n_input = ui.number(label='Variables', value=3, min=1, max=10, format='%.0f', on_change=self.generar_cuadricula).classes('w-32')
                
            self.contenedor_matriz = ui.column().classes('mb-6')
            ui.button('Resolver Sistema', on_click=self.resolver_sistema, icon='calculate').classes('w-full max-w-sm mx-auto mb-8')
            self.contenedor_resultados = ui.column().classes('w-full')
            
            self.generar_cuadricula()