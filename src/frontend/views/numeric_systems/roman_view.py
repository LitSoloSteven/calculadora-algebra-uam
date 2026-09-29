"""
Componente visual de NiceGUI para la Calculadora de Números Romanos.
"""

from nicegui import ui
from src.backend.solvers.numeric_systems.roman_calculator import (
    RomanCalculator,
    RomanNumeralError,
)


def render_roman_calculator():
    """Renderiza la tarjeta interactiva de la calculadora de números romanos."""
    with ui.card().classes('w-full p-6 rounded-xl shadow-md border border-gray-200 dark:border-zinc-700'):
        # Título y descripción
        with ui.row().classes('items-center gap-2 mb-2'):
            ui.icon('calculate', size='md').classes('text-primary')
            ui.label('Aritmética con Números Romanos').classes('text-xl font-bold text-primary')
        
        ui.label(
            'Realiza sumas, restas (sin cero ni negativos) y multiplicaciones de 1 dígito (I a IX) mediante sumas sucesivas.'
        ).classes('text-sm text-gray-500 dark:text-gray-400 mb-4')

        # Entradas y selector de operación
        with ui.row().classes('w-full items-center gap-4'):
            input_a = ui.input(
                label='Operando A',
                placeholder='Ej: XIV (1-3999)'
            ).classes('flex-1 uppercase').props('outlined dense')

            op_select = ui.select(
                options={
                    'suma': '➕ Suma (A + B)',
                    'resta': '➖ Resta (A - B)',
                    'mult': '✖️ Multiplicación (1 dígito)'
                },
                value='suma',
                label='Operación'
            ).classes('w-64').props('outlined dense')

            input_b = ui.input(
                label='Operando B',
                placeholder='Ej: IX'
            ).classes('flex-1 uppercase').props('outlined dense')

        # Contenedor dinámico de resultados
        result_container = ui.column().classes('w-full mt-4')

        def calcular():
            result_container.clear()
            raw_a = (input_a.value or '').strip().upper()
            raw_b = (input_b.value or '').strip().upper()
            op = op_select.value

            if not raw_a or not raw_b:
                ui.notify('Por favor, ingresa ambos operandos romanos.', type='warning', position='top')
                return

            try:
                if op == 'suma':
                    res = RomanCalculator.sumar(raw_a, raw_b)
                elif op == 'resta':
                    res = RomanCalculator.restar(raw_a, raw_b)
                elif op == 'mult':
                    res = RomanCalculator.multiplicar_un_digito(raw_a, raw_b)
                else:
                    return

                with result_container:
                    with ui.card().classes('w-full p-5 rounded-lg bg-blue-50 dark:bg-zinc-800/80 border border-blue-200 dark:border-blue-900'):
                        ui.label('Resultado Final').classes('text-xs font-semibold uppercase tracking-wider text-blue-700 dark:text-blue-300')
                        
                        with ui.row().classes('items-baseline gap-3 my-1'):
                            ui.label(res.resultado_romano).classes('text-3xl font-extrabold text-blue-600 dark:text-blue-400')
                            ui.label(f'= {res.resultado_decimal} (decimal)').classes('text-base text-gray-500 dark:text-gray-400')

                        ui.separator().classes('my-3')
                        
                        ui.label('Procedimiento paso a paso:').classes('text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2')
                        with ui.column().classes('gap-1 pl-2'):
                            for paso in res.pasos:
                                ui.label(f'• {paso}').classes('text-sm font-mono text-gray-700 dark:text-gray-300')

                ui.notify('Operación realizada con éxito', type='positive', position='top')

            except RomanNumeralError as err:
                ui.notify(str(err), type='negative', position='top')
                with result_container:
                    with ui.card().classes('w-full p-4 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-lg'):
                        ui.label('⚠️ Error en la operación').classes('text-sm font-bold text-red-700 dark:text-red-400')
                        ui.label(str(err)).classes('text-sm text-red-600 dark:text-red-300 mt-1')

        def limpiar():
            input_a.value = ''
            input_b.value = ''
            result_container.clear()

        # Botones de acción
        with ui.row().classes('mt-4 gap-3'):
            ui.button('Calcular', on_click=calcular, icon='play_arrow').props('unelevated color=primary')
            ui.button('Limpiar', on_click=limpiar, icon='refresh').props('flat color=grey')