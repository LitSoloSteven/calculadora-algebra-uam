"""Vista dedicada para la Calculadora de Números Romanos en Scalaris."""
from collections import Counter
from nicegui import ui
from src.frontend.components.navbar import create_navbar
from src.frontend.components.ai_panel import AIPanel
from src.backend.solvers.numeric_systems.roman_calculator import RomanCalculator, RomanNumeralError


class RomanCalculatorUI:
    """Controlador de vista con presentación especializada para números romanos."""

    def __init__(self):
        self.ai_panel = None

    def build(self):
        self.ai_panel = AIPanel(self)
        create_navbar(self, active_route='/romanos')

        with ui.column().classes('w-full max-w-4xl mx-auto items-center q-pa-md mt-6'):
            # --- PANEL DE ENTRADA ---
            with ui.column().classes('w-full panel-card p-6 gap-6'):
                ui.label('Calculadora de Números Romanos').classes('text-2xl font-bold text-main')

                # Selector de operación con neo-tabs
                with ui.row().classes('w-full items-center gap-3'):
                    with ui.tabs().classes('neo-tabs method-tabs tabs-wide w-full') as tabs_op:
                        ui.tab('suma', label='Suma')
                        ui.tab('resta', label='Resta')
                        ui.tab('mult', label='Mult (1 dígito)')

                # Chips de ejemplos rápidos
                with ui.row().classes('w-full items-center gap-2'):
                    ui.label('Ejemplos rápidos:').classes('text-sm text-sec')
                    with ui.row().classes('gap-2'):
                        def cargar_ejemplo(a_val, b_val, op_val):
                            input_a.value = a_val
                            input_b.value = b_val
                            tabs_op.set_value(op_val)
                            lbl_error.text = ''

                        ui.button('XIV + IX', on_click=lambda: cargar_ejemplo('XIV', 'IX', 'suma'), color=None).classes(
                            'btn-neo-icon text-xs px-3 py-1 text-sec'
                        ).props('ripple=false')
                        ui.button('XX - VIII', on_click=lambda: cargar_ejemplo('XX', 'VIII', 'resta'), color=None).classes(
                            'btn-neo-icon text-xs px-3 py-1 text-sec'
                        ).props('ripple=false')
                        ui.button('III × IV', on_click=lambda: cargar_ejemplo('III', 'IV', 'mult'), color=None).classes(
                            'btn-neo-icon text-xs px-3 py-1 text-sec'
                        ).props('ripple=false')

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

                    conteo_glifos = Counter(res_rom)
                    glifos_str = ', '.join([f'{cnt}×{char}' for char, cnt in conteo_glifos.items()])

                    with resultado_container:
                        # ----------------------------------------------------
                        # 1. HERO CARD: Ecuación Aritmética Completa
                        # ----------------------------------------------------
                        with ui.column().classes('w-full panel-card p-6 rounded-2xl gap-4 border border-white/10 shadow-lg'):
                            with ui.row().classes('w-full justify-between items-center'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.label('RESULTADO DE LA OPERACIÓN').classes('text-xs font-bold tracking-widest text-sec')
                                    ui.label(nombre_op.upper()).classes('text-[10px] font-extrabold px-2 py-0.5 rounded bg-blue-500/20 text-blue-300')
                                ui.button(icon='content_copy', on_click=lambda: copiar(res_rom), color=None).classes(
                                    'btn-neo-icon w-9 h-9 p-0 text-sec'
                                ).props('flat round').tooltip('Copiar resultado romano')

                            # Ecuación en display grande
                            with ui.row().classes('w-full items-center justify-center gap-4 py-2 flex-wrap text-center'):
                                ui.label(val_a).classes('text-3xl md:text-4xl font-extrabold text-sec font-mono')
                                ui.label(simbolo_op).classes('text-2xl font-bold text-sec')
                                ui.label(val_b).classes('text-3xl md:text-4xl font-extrabold text-sec font-mono')
                                ui.label('=').classes('text-2xl font-bold text-sec')
                                ui.label(res_rom).classes(
                                    'text-4xl md:text-5xl font-black font-mono tracking-wider px-5 py-1 rounded-xl bg-[#a8dadc]/15 text-[#a8dadc] border border-[#a8dadc]/30'
                                )

                            with ui.row().classes('w-full justify-center items-center gap-2 text-sec text-sm font-mono'):
                                ui.label(f'Equivalente Decimal: {dec_a} {simbolo_op} {dec_b} = {res_dec}')

                        # ----------------------------------------------------
                        # 2. TRES TARJETAS DE PROPIEDADES ANALÍTICAS
                        # ----------------------------------------------------
                        with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-3 gap-4'):
                            # Valor Decimal
                            with ui.column().classes('panel-card p-5 rounded-xl justify-between min-h-[110px]'):
                                with ui.row().classes('w-full justify-between items-center'):
                                    ui.label('Valor Decimal').classes('text-xs font-bold text-sec uppercase tracking-wider')
                                    ui.label('Base 10').classes('text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400')
                                ui.label(str(res_dec)).classes('text-3xl font-extrabold text-main font-mono')
                                ui.label(f'{nombre_op} completada').classes('text-xs text-sec')

                            # Regla / Composición
                            with ui.column().classes('panel-card p-5 rounded-xl justify-between min-h-[110px]'):
                                ui.label('Rango Histórico').classes('text-xs font-bold text-sec uppercase tracking-wider')
                                ui.label('1 a 3,999 (I – MMMCMXCIX)').classes('text-sm font-mono text-main font-semibold')
                                ui.label('Estándar clásico canónico').classes('text-xs text-sec')

                            # Glifos
                            with ui.column().classes('panel-card p-5 rounded-xl justify-between min-h-[110px]'):
                                with ui.row().classes('w-full justify-between items-center'):
                                    ui.label('Glifos Romanos').classes('text-xs font-bold text-sec uppercase tracking-wider')
                                    ui.label(f'{len(res_rom)} chars').classes('text-[10px] font-mono px-2 py-0.5 rounded bg-white/10 text-sec')
                                ui.label(glifos_str).classes('text-lg font-extrabold text-main font-mono')
                                ui.label('Símbolos empleados').classes('text-xs text-sec')

                        # ----------------------------------------------------
                        # 3. PROCEDIMIENTO MATEMÁTICO MEJORADO (FASE POR FASE)
                        # ----------------------------------------------------
                        ui.label('Procedimiento Matemático').classes('text-2xl font-bold text-main mt-4')

                        # === PASO 1: CONVERSIÓN INICIAL ===
                        with ui.expansion('1. Decodificación de Operandos a Decimal', icon='tag').classes(
                            'w-full panel-card rounded-xl text-main font-bold'
                        ).props('default-opened'):
                            with ui.column().classes('w-full p-4 gap-4 bg-black/15 rounded-b-xl'):
                                ui.label(
                                    'Los números romanos se evalúan sumando valores posicionales o restando valores menores que anteceden a uno mayor:'
                                ).classes('text-xs text-sec')

                                with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 gap-3'):
                                    # Card Operando A
                                    with ui.row().classes('p-3 rounded-lg bg-[#0a1e30] border border-white/5 items-center justify-between'):
                                        with ui.column().classes('gap-0'):
                                            ui.label('Operando A').classes('text-xs text-sec')
                                            ui.label(val_a).classes('text-xl font-mono font-bold text-main')
                                        ui.label(f'= {dec_a}').classes('text-lg font-mono font-extrabold text-[#a8dadc]')

                                    # Card Operando B
                                    with ui.row().classes('p-3 rounded-lg bg-[#0a1e30] border border-white/5 items-center justify-between'):
                                        with ui.column().classes('gap-0'):
                                            ui.label('Operando B').classes('text-xs text-sec')
                                            ui.label(val_b).classes('text-xl font-mono font-bold text-main')
                                        ui.label(f'= {dec_b}').classes('text-lg font-mono font-extrabold text-[#a8dadc]')

                        # === PASO 2: OPERACIÓN ARITMÉTICA ===
                        titulo_paso_2 = (
                            '2. Multiplicación mediante Sumas Sucesivas'
                            if op == 'mult'
                            else f'2. Ejecución Aritmética de la {nombre_op}'
                        )
                        with ui.expansion(titulo_paso_2, icon='calculate').classes(
                            'w-full panel-card rounded-xl text-main font-bold'
                        ).props('default-opened'):
                            with ui.column().classes('w-full p-4 gap-4 bg-black/15 rounded-b-xl'):

                                if op == 'mult' and isinstance(dec_b, int):
                                    # Tabla iterativa
                                    ui.label(
                                        f'Multiplicar {val_a} × {val_b} equivale a sumar el término {val_a} ({dec_a}) un total de {dec_b} veces consecutivas:'
                                    ).classes('text-xs text-sec')

                                    with ui.column().classes('w-full gap-2'):
                                        with ui.row().classes('w-full bg-[#0a1e30] py-2 px-4 rounded-lg text-xs font-bold text-sec items-center'):
                                            ui.label('Iteración').classes('w-1/4 text-center')
                                            ui.label('Operando Sumado').classes('w-1/4 text-center')
                                            ui.label('Acumulado (Dec)').classes('w-1/4 text-center')
                                            ui.label('Valor Parcial').classes('w-1/4 text-center')

                                        acum = 0
                                        for i in range(1, dec_b + 1):
                                            acum += dec_a
                                            with ui.row().classes('w-full py-2 px-4 border-b border-white/5 items-center text-sm font-mono'):
                                                ui.label(f'Paso {i}').classes('w-1/4 text-center text-sec font-bold')
                                                ui.label(f'+ {val_a} ({dec_a})').classes('w-1/4 text-center text-main')
                                                ui.label(str(acum)).classes('w-1/4 text-center text-main font-bold')
                                                with ui.row().classes('w-1/4 justify-center'):
                                                    ui.label(res_rom if i == dec_b else str(acum)).classes(
                                                        'bg-[#a8dadc] text-[#082338] font-black px-4 py-0.5 rounded-md text-xs'
                                                    )
                                else:
                                    # Explicación para suma o resta
                                    with ui.column().classes('w-full p-4 rounded-xl bg-[#0a1e30] border border-white/5 gap-3'):
                                        with ui.row().classes('items-center justify-between w-full'):
                                            ui.label('Operación Aritmética Evaluada').classes('text-xs text-sec font-bold uppercase tracking-wider')
                                            if op == 'resta':
                                                ui.label('Validación: A > B ✓').classes('text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400')
                                            else:
                                                ui.label('Adición Directa ✓').classes('text-[10px] font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-300')

                                        with ui.row().classes('items-center gap-3 py-1'):
                                            ui.label(f'{dec_a}').classes('text-2xl font-mono font-bold text-main')
                                            ui.label(f'{simbolo_op}').classes('text-xl font-bold text-sec')
                                            ui.label(f'{dec_b}').classes('text-2xl font-mono font-bold text-main')
                                            ui.label('=').classes('text-xl font-bold text-sec')
                                            ui.label(f'{res_dec}').classes('text-3xl font-mono font-extrabold text-[#a8dadc]')

                                        if op == 'resta':
                                            ui.label(
                                                '• Los números romanos no contemplan el cero ni valores negativos. El minuendo debe superar estrictamente al sustraendo.'
                                            ).classes('text-xs text-sec font-mono mt-1')

                        # === PASO 3: ENSAMBLE CANÓNICO A ROMANO ===
                        with ui.expansion('3. Notación y Construcción Canónica Romana', icon='history_edu').classes(
                            'w-full panel-card rounded-xl text-main font-bold'
                        ).props('default-opened'):
                            with ui.column().classes('w-full p-4 gap-4 bg-black/15 rounded-b-xl'):
                                ui.label(
                                    f'Se descompone el valor decimal {res_dec} de mayor a menor según los valores canónicos del sistema romano:'
                                ).classes('text-xs text-sec')

                                pasos_can = _desglosar_pasos_canónicos(res_dec)

                                # Tabla de deducción voraz
                                with ui.column().classes('w-full gap-1'):
                                    with ui.row().classes('w-full bg-[#0a1e30] py-2 px-4 rounded-lg text-xs font-bold text-sec items-center'):
                                        ui.label('Sustracción').classes('w-1/3 text-center')
                                        ui.label('Glifo Asignado').classes('w-1/3 text-center')
                                        ui.label('Residuo').classes('w-1/3 text-center')

                                    for p_can in pasos_can:
                                        with ui.row().classes('w-full py-2 px-4 border-b border-white/5 items-center text-sm font-mono'):
                                            ui.label(f'{p_can["anterior"]} − {p_can["valor_restado"]}').classes('w-1/3 text-center text-main')
                                            with ui.row().classes('w-1/3 justify-center'):
                                                ui.label(p_can['simbolo']).classes(
                                                    'bg-[#a8dadc] text-[#082338] font-black px-4 py-0.5 rounded-md text-xs'
                                                )
                                            ui.label(f'= {p_can["restante"]}').classes('w-1/3 text-center text-sec')

                                # Banner de conclusión
                                with ui.column().classes('w-full p-4 items-center justify-center bg-[#071927] border border-white/5 rounded-xl shadow-inner mt-2'):
                                    ui.label('EXPRESIÓN FINAL VERIFICADA').classes('text-[10px] font-bold text-sec tracking-widest')
                                    with ui.row().classes('items-baseline gap-2 mt-1'):
                                        ui.label(f'{val_a} {simbolo_op} {val_b} =').classes('text-lg text-sec font-mono')
                                        ui.label(res_rom).classes('text-2xl font-black text-[#a8dadc] font-mono tracking-widest')
                                        ui.label(f'({res_dec})').classes('text-sm text-sec font-mono')

                except RomanNumeralError as err:
                    lbl_error.text = str(err)
                except Exception as err:
                    lbl_error.text = str(err)

        self.ai_panel.build()