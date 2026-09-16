from nicegui import ui
from src.backend.solvers.numeric_systems.conversor_bases import ConversorBases

class NumericSystemsUI:
    def __init__(self):
        self.conversor = ConversorBases()

    def build(self):
        with ui.column().classes('w-full max-w-3xl mx-auto items-center q-pa-md mt-10'):
            ui.label('Conversor de Bases Numéricas').classes('text-3xl font-bold mb-6 text-main')

            # Contenedor principal
            with ui.column().classes('w-full panel-card q-pa-md gap-4'):
                self.base_origen = ui.select(
                    {
                        'decimal': 'Decimal', 
                        'binario': 'Binario', 
                        'octal': 'Octal', 
                        'hexadecimal': 'Hexadecimal'
                    },
                    value='decimal', 
                    label='Elige la base de origen'
                ).classes('w-full')

                self.valor_input = ui.input(label='Ingresa el valor a convertir').classes('w-full matrix-input text-lg')

                ui.button('Convertir', on_click=self.convertir).classes('btn-primary w-full q-py-sm mt-4')

            # Contenedor de resultados (Oculto al inicio)
            self.resultados_card = ui.column().classes('w-full panel-card q-pa-md mt-6 gap-2').style('display: none;')
            
            with self.resultados_card:
                ui.label('Resultados de la conversión:').classes('text-xl font-bold mb-4')
                self.lbl_error = ui.label().classes('text-negative font-bold text-lg')
                self.lbl_dec = ui.label().classes('text-lg')
                self.lbl_bin = ui.label().classes('text-lg')
                self.lbl_oct = ui.label().classes('text-lg')
                self.lbl_hex = ui.label().classes('text-lg')

    def convertir(self):
        valor = self.valor_input.value.strip()
        if not valor:
            ui.notify('Por favor ingresa un valor primero', type='warning')
            return

        base = self.base_origen.value
        resultado = {}

        # Llamamos al backend que acabas de crear
        if base == 'decimal':
            resultado = self.conversor.decimal_a_todo(valor)
        elif base == 'binario':
            resultado = self.conversor.binario_a_todo(valor)
        elif base == 'octal':
            resultado = self.conversor.octal_a_todo(valor)
        elif base == 'hexadecimal':
            resultado = self.conversor.hexadecimal_a_todo(valor)

        # Mostramos la tarjeta de resultados
        self.resultados_card.style('display: flex;')

        # Si hay error, ocultamos los números y mostramos el mensaje
        if "error" in resultado:
            self.lbl_error.text = resultado["error"]
            self.lbl_error.set_visibility(True)
            self.lbl_dec.set_visibility(False)
            self.lbl_bin.set_visibility(False)
            self.lbl_oct.set_visibility(False)
            self.lbl_hex.set_visibility(False)
        else:
            # Si todo salió bien, mostramos las 4 bases
            self.lbl_error.set_visibility(False)
            self.lbl_dec.text = f"Decimal: {resultado['decimal']}"
            self.lbl_dec.set_visibility(True)
            self.lbl_bin.text = f"Binario: {resultado['binario']}"
            self.lbl_bin.set_visibility(True)
            self.lbl_oct.text = f"Octal: {resultado['octal']}"
            self.lbl_oct.set_visibility(True)
            self.lbl_hex.text = f"Hexadecimal: {resultado['hexadecimal']}"
            self.lbl_hex.set_visibility(True)