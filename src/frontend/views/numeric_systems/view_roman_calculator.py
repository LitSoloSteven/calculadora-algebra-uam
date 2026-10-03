"""Vista dedicada para la Calculadora de Números Romanos en Scalaris."""
from collections import Counter
from nicegui import ui
from src.frontend.components.app_shell import create_app_shell
from src.frontend.navigation import route_of
from src.frontend.components.ai_panel import AIPanel
from src.backend.solvers.numeric_systems.roman_calculator import RomanCalculator, RomanNumeralError


class RomanCalculatorUI:
    """Controlador de vista con presentación especializada para números romanos."""

    def __init__(self):
        self.ai_panel = None

    def build(self):
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=route_of('romanos'))

        with ui.column().classes('w-full max-w-4xl mx-auto items-center q-pa-md mt-6'):
            # --- PANEL DE ENTRADA ---
            with ui.column().classes('w-full panel-card p-6 gap-6'):
                ui.label('Calculadora de Números Romanos').classes('text-2xl font-bold text-main')

                # Selector de operación con neo-tabs
                with ui.row().classes('w-full items-center gap-3'):
                    with ui.tabs().classes('neo-tabs method-tabs tabs-wide w-full') as tabs_op:
                        ui.tab('suma', label='Suma')
                        ui.tab('resta', label='Resta')
                        ui.tab('mult', label='Mult')

                # --- CHIPS DE EJEMPLOS RÁPIDOS ADAPTABLES ---
                with ui.row().classes('w-full items-center gap-3 flex-wrap'):
                    with ui.row().classes('items-center gap-1.5 text-sec'):
                        ui.icon('bolt', size='xs').style('color: var(--accent);')
                        ui.label('Ejemplos rápidos:').classes('text-xs font-semibold tracking-wider uppercase')

                    with ui.row().classes('gap-2.5 flex-wrap'):
                        def cargar_ejemplo(a_val, b_val, op_val):
                            input_a.value = a_val
                            input_b.value = b_val
                            tabs_op.set_value(op_val)
                            lbl_error.text = ''

                        def chip_ejemplo(label_txt, a_val, b_val, op_val):
                            return ui.button(
                                label_txt,
                                on_click=lambda: cargar_ejemplo(a_val, b_val, op_val),
                                color=None
                            ).classes(
                                'px-3.5 py-1.5 rounded-lg border text-main '
                                'font-mono text-xs font-bold tracking-wide transition-all duration-200 cursor-pointer'
                            ).style(
                                'background: var(--elev-2); border-color: var(--border-input); box-shadow: var(--elev-1);'
                            ).props('no-caps flat ripple=false')

                        chip_ejemplo('XIV + IX', 'XIV', 'IX', 'suma')
                        chip_ejemplo('XX − VIII', 'XX', 'VIII', 'resta')
                        chip_ejemplo('III × IV', 'III', 'IV', 'mult')

                # Cajas de texto de entrada
                with ui.column().classes('w-full gap-1'):
                    with ui.row().classes('w-full items-center gap-3 flex-nowrap'):
                        input_a = ui.input(placeholder='Operando A (ej: XIV)').classes(
                            'flex-1 matrix-input conversor-input text-center'
                        ).style('font-size: 1.5rem !important; padding: 18px 20px; text-transform: uppercase;')
                        input_a.props('autocomplete="off" spellcheck="false"')

                        lbl_signo = ui.label('+').classes('text-2xl font-bold text-sec flex-shrink-0')

                        input_b = ui.input(placeholder='Operando B (ej: IX)').classes(
                            'flex-1 matrix-input conversor-input text-center'
                        ).style('font-size: 1.5rem !important; padding: 18px 20px; text-transform: uppercase;')
                        input_b.props('autocomplete="off" spellcheck="false"')

                    lbl_error = ui.label('').classes('fs-small').style(
                        'color: var(--error); margin-left: 8px; min-height: 20px;'
                    )

                # Botón de cálculo
                ui.button(
                    'CALCULAR', on_click=lambda: operar_romanos(), color=None
                ).classes('btn-primary w-full py-3 text-lg mt-2 font-bold')

            # --- CONTENEDOR DINÁMICO DE RESULTADOS ---
            resultado_container = ui.column().classes('w-full gap-6 mt-6')

            def actualizar_signo(e):
                signos = {'suma': '+', 'resta': '−', 'mult': '×'}
                lbl_signo.text = signos.get(e.value, '+')
                lbl_error.text = ''

            tabs_op.on_value_change(actualizar_signo)
            tabs_op.set_value('suma')

            input_a.on('keydown.enter', lambda: operar_romanos())
            input_b.on('keydown.enter', lambda: operar_romanos())

            def copiar(texto: str):
                ui.clipboard.write(texto)
                ui.notify(f'Copiado: {texto}', type='positive', position='top')

            def _desglosar_pasos_canónicos(n: int):
                """Devuelve las deducciones voraces paso a paso para convertir decimal a romano."""
                tabla = [
                    (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
                    (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
                    (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
                ]
                pasos = []
                resto = n
                for val, rom in tabla:
                    while resto >= val:
                        nuevo_resto = resto - val
                        pasos.append({
                            'valor_restado': val,
                            'simbolo': rom,
                            'anterior': resto,
                            'restante': nuevo_resto
                        })
                        resto = nuevo_resto
                return pasos

            def operar_romanos():
                lbl_error.text = ''
                resultado_container.clear()

                val_a = (input_a.value or '').strip().upper()
                val_b = (input_b.value or '').strip().upper()
                op = tabs_op.value or 'suma'

                if not val_a or not val_b:
                    lbl_error.text = 'Ingresa ambos operandos en números romanos.'
                    return

                try:
                    if op == 'suma':
                        res = RomanCalculator.sumar(val_a, val_b)
                        simbolo_op = '+'
                        nombre_op = 'Suma'
                    elif op == 'resta':
                        res = RomanCalculator.restar(val_a, val_b)
                        simbolo_op = '−'
                        nombre_op = 'Resta'
                    else:
                        res = RomanCalculator.multiplicar_un_digito(val_a, val_b)
                        simbolo_op = '×'
                        nombre_op = 'Multiplicación'

                    dec_a = getattr(res, 'operando_a_decimal', None)
                    dec_b = getattr(res, 'operando_b_decimal', None)
                    res_rom = res.resultado_romano
                    res_dec = res.resultado_decimal

                    with resultado_container:
                        # ----------------------------------------------------
                        # HERO CARD: Ecuación Aritmética Limpia y Destacada
                        # ----------------------------------------------------
                        with ui.column().classes('w-full panel-card p-6 rounded-2xl gap-4'):
                            with ui.row().classes('w-full justify-between items-center'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.label('RESULTADO DE LA OPERACIÓN').classes('text-xs font-bold tracking-widest text-sec')
                                    ui.label(nombre_op.upper()).classes(
                                        'text-[10px] font-extrabold px-2.5 py-0.5 rounded border'
                                    ).style('background: var(--elev-inset); color: var(--accent); border-color: var(--border-input);')
                                ui.button(icon='content_copy', on_click=lambda: copiar(res_rom), color=None).classes(
                                    'btn-neo-icon w-9 h-9 p-0 text-sec'
                                ).props('flat round').tooltip('Copiar resultado romano')

                            # Ecuación en display grande
                            with ui.row().classes('w-full items-center justify-center gap-4 py-4 flex-wrap text-center'):
                                ui.label(val_a).classes('text-3xl md:text-4xl font-extrabold text-sec font-mono')
                                ui.label(simbolo_op).classes('text-2xl font-bold text-sec')
                                ui.label(val_b).classes('text-3xl md:text-4xl font-extrabold text-sec font-mono')
                                ui.label('=').classes('text-2xl font-bold text-sec')
                                ui.label(res_rom).classes(
                                    'text-4xl md:text-5xl font-black font-mono tracking-wider px-6 py-2.5 rounded-xl border'
                                ).style(
                                    'background: var(--elev-inset); color: var(--accent); border-color: var(--border-input);'
                                )

                        # ----------------------------------------------------
                        # PROCEDIMIENTO MATEMÁTICO
                        # ----------------------------------------------------
                        ui.label('Procedimiento Matemático').classes(
                            'text-3xl font-extrabold text-main'
                        ).style('margin-top: 48px !important; margin-bottom: 24px !important; display: block;')

                        # === PASO 1: DECODIFICACIÓN (CON BAJADA INTERNA Y EXTERNA) ===
                        with ui.expansion('1. Decodificación de Operandos a Decimal', icon='tag').classes(
                            'w-full panel-card rounded-2xl text-main font-bold text-xl'
                        ).props('default-opened header-class="pt-5 pb-3 px-6 items-center"'):
                            with ui.column().classes('w-full p-6 gap-5 rounded-b-2xl').style('background: var(--elev-inset);'):
                                with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 gap-4'):
                                    # Card Operando A
                                    with ui.row().classes('p-5 rounded-xl border items-center justify-between').style(
                                        'background: var(--elev-2); border-color: var(--border-input); box-shadow: var(--elev-1);'
                                    ):
                                        with ui.column().classes('gap-1'):
                                            ui.label('Operando A').classes('text-base font-semibold text-sec')
                                            ui.label(val_a).classes('text-3xl md:text-4xl font-mono font-bold text-main')
                                        ui.label(f'= {dec_a}').classes('text-3xl md:text-4xl font-mono font-black').style('color: var(--accent);')

                                    # Card Operando B
                                    with ui.row().classes('p-5 rounded-xl border items-center justify-between').style(
                                        'background: var(--elev-2); border-color: var(--border-input); box-shadow: var(--elev-1);'
                                    ):
                                        with ui.column().classes('gap-1'):
                                            ui.label('Operando B').classes('text-base font-semibold text-sec')
                                            ui.label(val_b).classes('text-3xl md:text-4xl font-mono font-bold text-main')
                                        ui.label(f'= {dec_b}').classes('text-3xl md:text-4xl font-mono font-black').style('color: var(--accent);')

                        # === PASO 2: OPERACIÓN ARITMÉTICA ===
                        titulo_paso_2 = (
                            '2. Multiplicación mediante Sumas Sucesivas'
                            if op == 'mult'
                            else f'2. Ejecución Aritmética de la {nombre_op}'
                        )
                        with ui.expansion(titulo_paso_2, icon='calculate').classes(
                            'w-full panel-card rounded-2xl text-main font-bold text-xl mt-4'
                        ).props('default-opened header-class="pt-5 pb-3 px-6 items-center"'):
                            with ui.column().classes('w-full p-6 gap-5 rounded-b-2xl').style('background: var(--elev-inset);'):

                                if op == 'mult' and isinstance(dec_b, int):
                                    with ui.column().classes('w-full gap-2.5'):
                                        with ui.row().classes('w-full py-3.5 px-5 rounded-xl text-base font-bold text-sec items-center border').style(
                                            'background: var(--elev-2); border-color: var(--border-input);'
                                        ):
                                            ui.label('Iteración').classes('w-1/4 text-center')
                                            ui.label('Operando Sumado').classes('w-1/4 text-center')
                                            ui.label('Acumulado (Dec)').classes('w-1/4 text-center')
                                            ui.label('Valor Parcial').classes('w-1/4 text-center')

                                        acum = 0
                                        for i in range(1, dec_b + 1):
                                            acum += dec_a
                                            with ui.row().classes('w-full py-3.5 px-5 border-b items-center text-lg md:text-xl font-mono').style(
                                                'border-color: var(--border-input);'
                                            ):
                                                ui.label(f'Paso {i}').classes('w-1/4 text-center text-sec font-bold')
                                                ui.label(f'+ {val_a} ({dec_a})').classes('w-1/4 text-center text-main font-semibold')
                                                ui.label(str(acum)).classes('w-1/4 text-center text-main font-black text-xl')
                                                with ui.row().classes('w-1/4 justify-center'):
                                                    ui.label(res_rom if i == dec_b else str(acum)).classes(
                                                        'font-black px-4 py-1.5 rounded-lg text-base border tracking-wider'
                                                    ).style(
                                                        'background: var(--elev-2); color: var(--accent); border-color: var(--border-input);'
                                                    )
                                else:
                                    with ui.column().classes('w-full p-6 rounded-2xl border gap-4').style(
                                        'background: var(--elev-2); border-color: var(--border-input);'
                                    ):
                                        with ui.row().classes('items-center justify-between w-full'):
                                            ui.label('Operación Aritmética Evaluada').classes(
                                                'text-base md:text-lg text-sec font-bold uppercase tracking-wider'
                                            )
                                            if op == 'resta':
                                                ui.label('Validación: A > B ✓').classes(
                                                    'text-base md:text-lg font-bold px-4 py-1.5 rounded-xl border'
                                                ).style('background: var(--elev-inset); color: var(--accent); border-color: var(--border-input);')
                                            else:
                                                ui.label('Adición Directa ✓').classes(
                                                    'text-base md:text-lg font-bold px-4 py-1.5 rounded-xl border'
                                                ).style('background: var(--elev-inset); color: var(--accent); border-color: var(--border-input);')

                                        with ui.row().classes('items-center gap-5 py-3 justify-center flex-wrap'):
                                            ui.label(f'{dec_a}').classes('text-4xl md:text-5xl font-mono font-bold text-main')
                                            ui.label(f'{simbolo_op}').classes('text-3xl md:text-4xl font-bold text-sec')
                                            ui.label(f'{dec_b}').classes('text-4xl md:text-5xl font-mono font-bold text-main')
                                            ui.label('=').classes('text-3xl md:text-4xl font-bold text-sec')
                                            ui.label(f'{res_dec}').classes('text-5xl md:text-6xl font-mono font-black').style('color: var(--accent);')

                                        if op == 'resta':
                                            ui.label(
                                                '• Los números romanos no contemplan el cero ni valores negativos. El minuendo debe superar estrictamente al sustraendo.'
                                            ).classes('text-base text-sec font-mono mt-1')

                        # === PASO 3: ENSAMBLE CANÓNICO A ROMANO ===
                        with ui.expansion('3. Notación y Construcción Canónica Romana', icon='history_edu').classes(
                            'w-full panel-card rounded-2xl text-main font-bold text-xl mt-4'
                        ).props('default-opened header-class="pt-5 pb-3 px-6 items-center"'):
                            with ui.column().classes('w-full p-6 gap-5 rounded-b-2xl').style('background: var(--elev-inset);'):
                                pasos_can = _desglosar_pasos_canónicos(res_dec)

                                with ui.column().classes('w-full gap-2'):
                                    with ui.row().classes('w-full py-3.5 px-5 rounded-xl text-base font-bold text-sec items-center border').style(
                                        'background: var(--elev-2); border-color: var(--border-input);'
                                    ):
                                        ui.label('Sustracción').classes('w-1/3 text-center')
                                        ui.label('Glifo Asignado').classes('w-1/3 text-center')
                                        ui.label('Residuo').classes('w-1/3 text-center')

                                    for p_can in pasos_can:
                                        with ui.row().classes('w-full py-3.5 px-5 border-b items-center text-xl md:text-2xl font-mono').style(
                                            'border-color: var(--border-input);'
                                        ):
                                            ui.label(f'{p_can["anterior"]} − {p_can["valor_restado"]}').classes('w-1/3 text-center text-main font-black')
                                            with ui.row().classes('w-1/3 justify-center'):
                                                ui.label(p_can['simbolo']).classes(
                                                    'font-black px-6 py-2 rounded-xl text-xl border tracking-widest'
                                                ).style(
                                                    'background: var(--elev-2); color: var(--accent); border-color: var(--border-input);'
                                                )
                                            ui.label(f'= {p_can["restante"]}').classes('w-1/3 text-center text-sec font-bold')

                                with ui.column().classes(
                                    'w-full p-6 items-center justify-center border rounded-2xl shadow-inner mt-4'
                                ).style('background: var(--elev-2); border-color: var(--border-input);'):
                                    ui.label('EXPRESIÓN FINAL VERIFICADA').classes('text-xs md:text-sm font-bold text-sec tracking-widest')
                                    with ui.row().classes('items-baseline gap-4 mt-2 flex-wrap justify-center'):
                                        ui.label(f'{val_a} {simbolo_op} {val_b} =').classes('text-2xl md:text-3xl text-sec font-mono font-medium')
                                        ui.label(res_rom).classes(
                                            'text-4xl md:text-5xl font-black font-mono tracking-widest'
                                        ).style('color: var(--accent);')
                                        ui.label(f'({res_dec})').classes('text-lg md:text-xl text-sec font-mono')

                except RomanNumeralError as err:
                    lbl_error.text = str(err)
                except Exception as err:
                    lbl_error.text = str(err)

        self.ai_panel.build()