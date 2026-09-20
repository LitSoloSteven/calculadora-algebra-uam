import asyncio
import re
from nicegui import ui, events
from src.backend.solvers.numeric_systems.conversor_bases import ConversorBases
from src.frontend.components.navbar import create_navbar
from src.frontend.components.ai_panel import AIPanel

class NumericSystemsUI:
    def __init__(self):
        self.conversor = ConversorBases()
        self.base_activa = 'decimal'
        self.base_destino = 'todas'
        self.debounce_task = None
        self.resultados = {'decimal': '0', 'binario': '0', 'octal': '0', 'hexadecimal': '0'}
        self.bits_container = None
        self.pasos_container = None
        self.ui_cards = {}
        self.ui_valores = {}
        
        self.regex_bases = {
            'binario': r'^[+-]?0[bB]?[01_]*$|^[+-]?[01_]*$',
            'octal': r'^[+-]?0[oO]?[0-7_]*$|^[+-]?[0-7_]*$',
            'decimal': r'^[+-]?[0-9_]*$',
            'hexadecimal': r'^[+-]?0[xX]?[0-9A-Fa-f_]*$|^[+-]?[0-9A-Fa-f_]*$'
        }

    def build(self):
        self.ai_panel = AIPanel(self)
        create_navbar(self, active_route='/conversor')

        with ui.column().classes('w-full max-w-4xl mx-auto items-center q-pa-md mt-6'):
            # --- HERO SECTION (Entrada) ---
            with ui.column().classes('w-full panel-card p-6 gap-6'):
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label('Conversor de Bases').classes('text-2xl font-bold text-main')
                    
                    # Neo-tabs para base origen y destino
                    with ui.row().classes('items-center gap-4'):
                        with ui.tabs().classes('neo-tabs method-tabs') as self.tabs_origen:
                            ui.tab('decimal', label='Dec')
                            ui.tab('binario', label='Bin')
                            ui.tab('octal', label='Oct')
                            ui.tab('hexadecimal', label='Hex')
                            
                        self.btn_swap_tabs = ui.button(icon='swap_horiz', on_click=self._swap_origen_destino, color=None).classes('btn-neo-icon text-main').props('ripple=false').style('transition: transform 240ms ease;')
                        
                        with ui.tabs().classes('neo-tabs method-tabs') as self.tabs_destino:
                            ui.tab('todas', label='Todas')
                            ui.tab('decimal', label='Dec')
                            ui.tab('binario', label='Bin')
                            ui.tab('octal', label='Oct')
                            ui.tab('hexadecimal', label='Hex')
                        
                # Chips de ejemplos rápidos
                with ui.row().classes('w-full items-center gap-2'):
                    ui.label('Ejemplos rápidos:').classes('text-sm text-sec')
                    self.container_ejemplos = ui.row().classes('gap-2')
                
                # Input gigante
                with ui.column().classes('w-full gap-1'):
                    with ui.row().classes('w-full relative'):
                        self.input_valor = ui.input(placeholder='0').classes('w-full matrix-input').style('font-size: var(--fs-display) !important; padding: 20px;')
                        self.input_valor.props('id="input-conversor" autocomplete="off" spellcheck="false"')
                        self.input_valor.on_value_change(self._on_input_change)
                        
                        # Botones limpiar / pegar dentro del input
                        with ui.row().classes('absolute right-4 top-1/2 -translate-y-1/2 gap-2'):
                            ui.button(icon='content_paste', on_click=self._pegar_portapapeles, color=None).classes('btn-neo-icon w-10 h-10 p-0').props('ripple=false text-sec').tooltip('Pegar')
                            ui.button(icon='backspace', on_click=self._limpiar, color=None).classes('btn-neo-icon w-10 h-10 p-0').style('color: var(--error)').props('ripple=false').tooltip('Limpiar')
                    
                    self.lbl_error = ui.label('').classes('fs-small').style('color: var(--error); margin-left: 8px; min-height: 20px;')

                # Tira visual de bits y ancho
                with ui.row().classes('w-full justify-between items-center mt-2'):
                    self.lbl_info_bits = ui.label('').classes('text-sm font-mono text-sec font-bold')
                    self.bits_container = ui.row().classes('gap-1 items-center flex-wrap')

                ui.button('Convertir', on_click=self._convertir_btn, color=None).classes('btn-primary w-full py-3 text-lg mt-2 font-bold')

            # --- RESULTADOS (Tarjetas 2x2) ---
            with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 gap-4 mt-6'):
                self._crear_tarjeta_resultado('decimal', 'Decimal', '10')
                self._crear_tarjeta_resultado('hexadecimal', 'Hexadecimal', '16')
                self._crear_tarjeta_resultado('binario', 'Binario', '2')
                self._crear_tarjeta_resultado('octal', 'Octal', '8')

            # --- PROCEDIMIENTO ---
            self.pasos_container = ui.column().classes('w-full gap-4 mt-6 hidden')
            
        # Set handlers y valores iniciales
        self.tabs_origen.on_value_change(self._cambiar_base_origen)
        self.tabs_destino.on_value_change(self._cambiar_base_destino)
        
        self.tabs_origen.set_value('decimal')
        self.tabs_destino.set_value('todas')
        
        self.ai_panel.build()

    def _crear_tarjeta_resultado(self, id_base, titulo, subindice):
        with ui.column().classes('panel-card p-5 relative overflow-hidden transition-all duration-300 opacity-0 translate-y-4').style('min-height: 120px;') as card:
            self.ui_cards[id_base] = card
            
            with ui.row().classes('w-full justify-between items-center mb-2'):
                ui.html(f'<span class="font-bold text-sec">{titulo}</span><sub class="font-bold ml-1 text-xs">{subindice}</sub>')
                
                with ui.row().classes('gap-2'):
                    ui.button(icon='swap_vert', on_click=lambda e, b=id_base: self._swap_base(b), color=None).classes('btn-ghost w-8 h-8 p-0 text-sec').props('ripple=false').tooltip(f'Usar como entrada')
                    ui.button(icon='content_copy', on_click=lambda e, b=id_base: self._copiar_resultado(b, e.sender), color=None).classes('btn-ghost w-8 h-8 p-0 text-sec').props('ripple=false').tooltip('Copiar')
            
            # Valor formateado
            self.ui_valores[id_base] = ui.label('0').classes('text-2xl font-mono text-main break-all tracking-wide transition-opacity duration-300').bind_text_from(self.resultados, id_base)
            
            # Etiqueta "Entrada" para dimmear la tarjeta origen
            ui.label('ENTRADA ACTUAL').classes('absolute -right-8 top-4 bg-[var(--accent)] text-[var(--btn-primary-text)] text-[10px] font-bold py-1 px-10 rotate-45').bind_visibility_from(self, 'base_activa', backward=lambda v: v == id_base)

    def _cambiar_base_origen(self, e):
        if not e.value: return
        self.base_activa = e.value
        if self.base_activa == self.base_destino:
            self.tabs_destino.set_value('todas')
        self._actualizar_ejemplos()
        asyncio.create_task(self._on_input_change(None))
        
    def _cambiar_base_destino(self, e):
        if not e.value: return
        self.base_destino = e.value
        if self.base_destino == self.base_activa:
            self.tabs_destino.set_value('todas')
        asyncio.create_task(self._on_input_change(None))

    def _swap_origen_destino(self, e):
        ui.run_javascript('''
            const btn = document.activeElement;
            if (btn) {
                let currentRot = parseInt(btn.dataset.rot || "0");
                currentRot += 180;
                btn.dataset.rot = currentRot;
                btn.style.transform = `rotate(${currentRot}deg)`;
            }
        ''')
        
        if self.base_destino == 'todas': return
        old_origen = self.base_activa
        self.tabs_origen.set_value(self.base_destino)
        self.tabs_destino.set_value(old_origen)

    def _actualizar_ejemplos(self):
        self.container_ejemplos.clear()
        ejemplos = {
            'hexadecimal': ['FF', '1A', 'A5'],
            'decimal': ['255', '42', '128'],
            'binario': ['11111111', '101010', '10000000'],
            'octal': ['377', '52', '200']
        }.get(self.base_activa, [])
        
        with self.container_ejemplos:
            for ej in ejemplos:
                ui.button(ej, on_click=lambda e, val=ej: self._set_input(val), color=None).classes('btn-ghost py-0 px-3 min-h-0 text-xs font-mono').props('ripple=false')

    def _set_input(self, val):
        self.input_valor.set_value(val)
        asyncio.create_task(self._on_input_change(None))

    def _limpiar(self):
        self._set_input('')
        
    async def _pegar_portapapeles(self):
        try:
            val = await ui.run_javascript('navigator.clipboard.readText()', timeout=15)
            if val: self._set_input(val.strip())
        except Exception:
            self.lbl_error.text = "Error al pegar: permiso denegado o portapapeles vacío."

    async def _copiar_resultado(self, id_base, btn):
        val = self.resultados.get(id_base, '').replace(' ', '')
        if not val: return
        ui.run_javascript(f'navigator.clipboard.writeText("{val}")')
        btn.props('icon=check color=positive')
        
        def reset_icon():
            btn.props('icon=content_copy color=None')
            
        ui.timer(2.0, reset_icon, once=True)

    def _swap_base(self, nueva_base):
        if nueva_base == self.base_activa: return
        val = self.resultados.get(nueva_base, '').replace(' ', '')
        self.tabs_origen.set_value(nueva_base)
        self._set_input(val)

    async def _on_input_change(self, e):
        val = self.input_valor.value or ''
        
        # Validación en vivo
        if val and not re.match(self.regex_bases[self.base_activa], val.replace(" ", "")):
            # Shake effect CSS 
            await ui.run_javascript('''
                const inp = document.getElementById("input-conversor");
                if(inp) {
                    inp.classList.remove("animate-shake");
                    void inp.offsetWidth; // trigger reflow
                    inp.classList.add("animate-shake");
                }
            ''')
            self.lbl_error.text = f'Base {self.base_activa}: solo se admiten caracteres válidos.'
            return

        self.lbl_error.text = ''
        # Debounce manual
        if self.debounce_task:
            self.debounce_task.cancel()
        self.debounce_task = asyncio.create_task(self._ejecutar_conversion(val))

    async def _ejecutar_conversion(self, val, inmediato=False):
        if not inmediato:
            await asyncio.sleep(0.15) # 150ms debounce
        if not val.strip():
            self._limpiar_resultados()
            return False
            
        if self.base_activa in ('hexadecimal', 'base32'):
            val = val.upper()
            
        metodo = getattr(self.conversor, f"{self.base_activa}_a_todo")
        res = metodo(val, self.base_destino)
        
        if "error" in res:
            self._limpiar_resultados()
            return False
            
        # Agrupar formato
        self.resultados['decimal'] = f"{int(res['decimal']):,}".replace(',', ' ')
        self.resultados['binario'] = self._agrupar(res['binario'], 4)
        self.resultados['octal'] = res['octal']
        self.resultados['hexadecimal'] = self._agrupar(res['hexadecimal'], 2)
        
        self.resultados_completos = res # Guardar para procedimiento
        
        # Bits tira
        self._render_bits(res['binario'].replace('-', ''))
        
        self._aplicar_opacidad_tarjetas()
        return True

    def _aplicar_opacidad_tarjetas(self):
        for base, card in self.ui_cards.items():
            card.classes(remove='opacity-0 translate-y-4') # Quitar estado oculto inicial
            
            if self.base_destino == 'todas':
                opacidad = "0.45" if base == self.base_activa else "1"
            else:
                if base == self.base_destino: opacidad = "1"
                else: opacidad = "0.45"
            pointer = "none" if base == self.base_activa else "auto"
            
            card.style(f'pointer-events: {pointer};')
            
            if base in self.ui_valores:
                self.ui_valores[base].style(f'opacity: {opacidad};')

    async def _convertir_btn(self, e):
        btn = e.sender
        val = self.input_valor.value or ''
        if not val.strip():
            ui.notify('Ingresá un valor para convertir.', type='warning')
            return
            
        val_clean = val.replace(" ", "")
        if not re.match(self.regex_bases[self.base_activa], val_clean):
            ui.notify(f'Base {self.base_activa}: solo se admiten caracteres válidos.', type='warning')
            return
            
        btn.props('loading=true')
        try:
            if not await self._ejecutar_conversion(val, inmediato=True):
                return
            
            # Animación stagger
            for i, (base, card) in enumerate(self.ui_cards.items()):
                card.classes(remove='opacity-0 translate-y-4')
                await asyncio.sleep(0.04)
                
            self._aplicar_opacidad_tarjetas()
            self._mostrar_procedimiento()
        finally:
            btn.props('loading=false')

    def _agrupar(self, string, n):
        signo = "-" if string.startswith("-") else ""
        s = string.lstrip("-")
        # Agrupar de derecha a izquierda
        grupos = [s[max(i-n, 0):i] for i in range(len(s), 0, -n)]
        return signo + " ".join(reversed(grupos))

    def _limpiar_resultados(self):
        for k in ['decimal', 'binario', 'octal', 'hexadecimal']:
            self.resultados[k] = '0'
        for card in self.ui_cards.values():
            card.classes('opacity-0 translate-y-4')
        self.lbl_info_bits.text = ''
        self.bits_container.clear()
        self.pasos_container.classes('hidden')

    def _render_bits(self, bin_str):
        self.bits_container.clear()
        l = len(bin_str)
        self.lbl_info_bits.text = f"{l} BITS"
        
        if l > 32: 
            return # No renderizar tiras muy largas
            
        with self.bits_container:
            for i, bit in enumerate(bin_str):
                peso = l - 1 - i
                color = 'bg-[var(--accent)]' if bit == '1' else 'bg-[var(--border-input)]'
                ui.html(f'<div class="w-4 h-4 rounded-sm {color} transition-colors" title="2^{peso} = {2**peso}"></div>')

    def _mostrar_procedimiento(self):
        if not hasattr(self, 'resultados_completos') or "pasos" not in self.resultados_completos:
            ui.notify('Realiza una conversión válida primero', type='warning')
            return
            
        self.pasos_container.clear()
        self.pasos_container.classes(remove='hidden')
        
        with self.pasos_container:
            ui.label('Procedimiento Matemático').classes('text-2xl font-bold text-main mt-4')
            
            for paso in self.resultados_completos["pasos"]:
                if paso["tipo"] == "expansion_posicional":
                    with ui.expansion(f'1. Expansión Posicional desde Base {paso["base_origen"]}', icon='functions').classes('w-full panel-card font-bold text-main timeline-expansion'):
                        # Construir tabla HTML con MathJax
                        filas_html = ""
                        eq_str = ""
                        for t in paso["terminos"]:
                            filas_html += f"<tr><td class='p-2 border-b border-[var(--border-input)] text-center font-mono'>{t['digito']}</td><td class='p-2 border-b border-[var(--border-input)] text-center'>{t['valor']}</td><td class='p-2 border-b border-[var(--border-input)] text-center'>{paso['base_origen']}<sup>{t['potencia']}</sup></td><td class='p-2 border-b border-[var(--border-input)] text-center'>{t['peso']}</td><td class='p-2 border-b border-[var(--border-input)] text-center font-bold text-[var(--accent)]'>{t['producto']}</td></tr>"
                            eq_str += f"({t['valor']} \\times {paso['base_origen']}^{{{t['potencia']}}}) + "
                            
                        eq_str = eq_str[:-3] + f" = {paso['total']}"
                        
                        tabla = f"""
                        <table class="w-full text-sm mt-4 mb-6 border-collapse">
                            <thead>
                                <tr class="bg-[var(--bg-elevated)]">
                                    <th class="p-2 text-sec">Dígito</th>
                                    <th class="p-2 text-sec">Valor Int</th>
                                    <th class="p-2 text-sec">Posición</th>
                                    <th class="p-2 text-sec">Peso</th>
                                    <th class="p-2 text-sec">Subtotal</th>
                                </tr>
                            </thead>
                            <tbody>{filas_html}</tbody>
                        </table>
                        <div class="math-scroll-container w-full text-center p-4 bg-[var(--bg-elevated)] rounded-lg math-label text-lg">
                            $${eq_str}$$
                        </div>
                        """
                        ui.html(tabla).classes('w-full font-normal')
                        
                elif paso["tipo"] == "division_sucesiva":
                    with ui.expansion(f'2. Divisiones Sucesivas hacia Base {paso["base_destino"]}', icon='vertical_align_bottom').classes('w-full panel-card font-bold text-main timeline-expansion'):
                        
                        filas_html = ""
                        for f in paso["filas"]:
                            filas_html += f"<tr><td class='p-2 border-b border-[var(--border-input)] text-center'>{f['dividendo']}</td><td class='p-2 border-b border-[var(--border-input)] text-center'>÷ {f['divisor']}</td><td class='p-2 border-b border-[var(--border-input)] text-center font-bold'>{f['cociente']}</td><td class='p-2 border-b border-[var(--border-input)] text-center font-bold text-white bg-[var(--accent)] rounded-md m-1 block'>{f['residuo']}</td></tr>"
                            
                        tabla = f"""
                        <div class="flex items-center gap-6 mt-4 font-normal">
                            <div class="overflow-x-auto flex-grow">
                                <table class="w-full text-sm border-collapse">
                                    <thead>
                                        <tr class="bg-[var(--bg-elevated)]">
                                            <th class="p-2 text-sec">Dividendo</th>
                                            <th class="p-2 text-sec">Divisor</th>
                                            <th class="p-2 text-sec">Cociente</th>
                                            <th class="p-2 text-sec">Residuo</th>
                                        </tr>
                                    </thead>
                                    <tbody>{filas_html}</tbody>
                                </table>
                            </div>
                            <div class="flex flex-col items-center justify-center text-sec">
                                <span class="material-icons text-3xl">arrow_upward</span>
                                <span class="text-xs text-center w-24">{paso["lectura"]}</span>
                            </div>
                        </div>
                        <div class="math-scroll-container w-full text-center p-4 bg-[var(--bg-elevated)] rounded-lg math-label text-xl mt-4">
                            $$ {paso['resultado']}_{{{paso['base_destino']}}} $$
                        </div>
                        """
                        ui.html(tabla).classes('w-full')
                        
            # Refrescar MathJax
            ui.run_javascript("typesetMathWhenReady();")