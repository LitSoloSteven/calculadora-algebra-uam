from nicegui import ui
from src.backend.solvers.numeric_systems.conversor_bases import ConversorBases
from src.frontend.components.navbar import create_navbar

class NumericSystemsUI:
    def __init__(self):
        self.conversor = ConversorBases()

    def build(self):
        # AQUÍ INVOCAMOS LA BARRA DE NAVEGACIÓN PARA NO QUEDAR ATRAPADOS
        create_navbar()

        with ui.column().classes('w-full max-w-3xl mx-auto items-center q-pa-md mt-10'):
            ui.label('Conversor de Bases Numéricas').classes('text-3xl font-bold mb-6 text-main')

            # Contenedor principal de inputs
            with ui.column().classes('w-full panel-card q-pa-md gap-4'):
                with ui.row().classes('w-full gap-4'):
                    self.base_origen = ui.select(
                        {'decimal': 'Decimal', 'binario': 'Binario', 'octal': 'Octal', 'hexadecimal': 'Hexadecimal'},
                        value='decimal', label='Base origen'
                    ).classes('flex-grow')
                    
                    self.base_destino = ui.select(
                        {'todas': 'Mostrar Todas', 'decimal': 'Decimal', 'binario': 'Binario', 'octal': 'Octal', 'hexadecimal': 'Hexadecimal'},
                        value='todas', label='Base destino'
                    ).classes('flex-grow')

                self.valor_input = ui.input(label='Ingresa el valor a convertir').classes('w-full matrix-input text-lg')
                ui.button('Convertir', on_click=self.convertir).classes('btn-primary w-full q-py-sm mt-4')

            # Contenedor de resultados (Oculto al inicio)
            self.resultados_card = ui.column().classes('w-full mt-6 gap-6').style('display: none;')
            
            with self.resultados_card:
                # Tarjeta de respuestas finales
                with ui.column().classes('w-full panel-card q-pa-md gap-2'):
                    ui.label('Resultados:').classes('text-xl font-bold mb-2 text-main')
                    self.lbl_error = ui.label().classes('badge-error q-pa-sm font-bold text-lg w-full text-center')
                    self.lbl_dec = ui.label().classes('text-lg math-label')
                    self.lbl_bin = ui.label().classes('text-lg math-label')
                    self.lbl_oct = ui.label().classes('text-lg math-label')
                    self.lbl_hex = ui.label().classes('text-lg math-label')

                # Contenedor dinámico para los pasos (estilo acordeón)
                self.pasos_container = ui.column().classes('w-full gap-2')

    def convertir(self):
        valor = self.valor_input.value.strip()
        if not valor:
            ui.notify('Por favor ingresa un valor primero', type='warning')
            return

        origen = self.base_origen.value
        destino = self.base_destino.value
        
        if origen == 'decimal':
            resultado = self.conversor.decimal_a_todo(valor)
        elif origen == 'binario':
            resultado = self.conversor.binario_a_todo(valor)
        elif origen == 'octal':
            resultado = self.conversor.octal_a_todo(valor)
        elif origen == 'hexadecimal':
            resultado = self.conversor.hexadecimal_a_todo(valor)

        self.resultados_card.style('display: flex;')
        self.pasos_container.clear()

        if "error" in resultado:
            self.lbl_error.text = resultado["error"]
            self.lbl_error.set_visibility(True)
            self.lbl_dec.set_visibility(False)
            self.lbl_bin.set_visibility(False)
            self.lbl_oct.set_visibility(False)
            self.lbl_hex.set_visibility(False)
        else:
            self.lbl_error.set_visibility(False)
            
            self.lbl_dec.text = f"Decimal: {resultado['decimal']}"
            self.lbl_dec.set_visibility(destino in ['todas', 'decimal'])
            
            self.lbl_bin.text = f"Binario: {resultado['binario']}"
            self.lbl_bin.set_visibility(destino in ['todas', 'binario'])
            
            self.lbl_oct.text = f"Octal: {resultado['octal']}"
            self.lbl_oct.set_visibility(destino in ['todas', 'octal'])
            
            self.lbl_hex.text = f"Hexadecimal: {resultado['hexadecimal']}"
            self.lbl_hex.set_visibility(destino in ['todas', 'hexadecimal'])
            
            # Renderizar los pasos matemáticos en paneles desplegables integrados con el tema
            with self.pasos_container:
                ui.label('Procedimiento Paso a Paso:').classes('text-xl font-bold mt-2 text-main')
                for paso in resultado.get("pasos", []):
                    with ui.expansion(paso["titulo"], icon='calculate').classes('w-full panel-card font-bold text-main'):
                        ui.label(paso["explicacion"]).classes('text-md text-sec mb-4 font-normal')
                        ui.label(paso["operacion"]).classes('text-lg math-label matrix-input q-pa-md w-full text-center rounded-lg')