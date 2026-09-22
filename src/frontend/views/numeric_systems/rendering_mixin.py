"""Mixin de renderizado de tarjetas, bits y procedimientos para Sistemas Numéricos."""
import asyncio
from nicegui import ui


class NumericSystemsRenderingMixin:
    """Maneja la creación de tarjetas de resultado, cálculo de conversión, bits y pasos detallados."""

    def _crear_tarjeta_resultado(self, id_base, titulo, subindice):
        with ui.column().classes('panel-card p-5 relative overflow-hidden').style(
            'min-height: 120px; opacity: 0; transform: translateY(16px); '
            'transition: opacity 300ms ease, transform 300ms ease;'
        ) as card:
            self.ui_cards[id_base] = card

            with ui.row().classes('w-full justify-between items-center mb-2 gap-2 flex-wrap'):
                with ui.row().classes('items-center gap-2'):
                    ui.html(f'<span class="font-bold text-sec">{titulo}</span><sub class="font-bold ml-1 text-xs">{subindice}</sub>')
                    badge = ui.label('ENTRADA ACTUAL').classes('badge-success text-[10px] font-bold px-2 py-0.5')
                    badge.bind_visibility_from(self, 'base_activa', backward=lambda v: v == id_base)

                with ui.row().classes('gap-2'):
                    ui.button(
                        icon='swap_vert',
                        on_click=lambda e, b=id_base: self._swap_base(b),
                        color=None
                    ).classes('btn-ghost w-8 h-8 p-0 text-sec').props('ripple=false').tooltip('Usar como entrada')
                    ui.button(
                        icon='content_copy',
                        on_click=lambda e, b=id_base: self._copiar_resultado(b, e.sender),
                        color=None
                    ).classes('btn-ghost w-8 h-8 p-0 text-sec').props('ripple=false').tooltip('Copiar')

            self.ui_valores[id_base] = ui.label('0').classes(
                'text-2xl font-mono text-main break-all tracking-wide transition-opacity duration-300'
            ).bind_text_from(self.resultados, id_base)

    async def _ejecutar_conversion(self, val, inmediato=False, revelar_tarjetas=True):
        try:
            if not inmediato:
                await asyncio.sleep(0.15)
            if not val.strip():
                self._limpiar_resultados()
                return False

            if self.base_activa == 'hexadecimal':
                val = val.upper()

            metodo = getattr(self.conversor, f"{self.base_activa}_a_todo")
            res = metodo(val, self.base_destino)

            if "error" in res:
                self._limpiar_resultados()
                return False

            # Formatear y agrupar resultados
            self.resultados['decimal'] = f"{int(res['decimal']):,}".replace(',', ' ')
            self.resultados['binario'] = self._agrupar(res['binario'], 4)
            self.resultados['octal'] = res['octal']
            self.resultados['hexadecimal'] = self._agrupar(res['hexadecimal'], 2)

            self.resultados_completos = res
            self.tiene_resultado = True

            self._render_bits(res['binario'].replace('-', ''))
            self._aplicar_opacidad_tarjetas(revelar=revelar_tarjetas)
            self._mostrar_procedimiento()
            return True
        except asyncio.CancelledError:
            pass

    def _agrupar(self, string, n):
        signo = "-" if string.startswith("-") else ""
        s = string.lstrip("-")
        grupos = [s[max(i - n, 0):i] for i in range(len(s), 0, -n)]
        return signo + " ".join(reversed(grupos))

    def _limpiar_resultados(self):
        self.tiene_resultado = False
        for k in ['decimal', 'binario', 'octal', 'hexadecimal']:
            self.resultados[k] = '0'
        for card in self.ui_cards.values():
            card.style('opacity: 0; transform: translateY(16px);')
        self.lbl_info_bits.text = ''
        self.bits_container.clear()
        if self.bits_container:
            self.bits_container.style('opacity: 0;')
        self.pasos_container.classes('hidden')

    def _render_bits(self, bin_str):
        self.bits_container.clear()
        l = len(bin_str)
        self.lbl_info_bits.text = f"{l} BITS"

        if l > 32:
            return

        with self.bits_container:
            for i, bit in enumerate(bin_str):
                peso = l - 1 - i
                color = 'bg-[var(--accent)]' if bit == '1' else 'bg-[var(--border-input)]'
                ui.html(f'<div class="w-4 h-4 rounded-sm {color} transition-colors" title="2^{peso} = {2**peso}"></div>')

    def _mostrar_procedimiento(self):
        if not hasattr(self, 'resultados_completos') or "pasos" not in self.resultados_completos:
            ui.notify('Realiza una conversión válida primero', type='warning')
            return

        nombres_base = {2: "Binario", 8: "Octal", 10: "Decimal", 16: "Hexadecimal"}
        self.pasos_container.clear()
        self.pasos_container.classes(remove='hidden')

        with self.pasos_container:
            ui.label('Procedimiento Matemático').classes('text-2xl font-bold text-main mt-4')

            if not self.resultados_completos.get("pasos"):
                ui.label('El número ya se encuentra en el sistema destino seleccionado.').classes('text-sec italic text-sm mb-2')

            for idx, paso in enumerate(self.resultados_completos.get("pasos", []), start=1):
                if paso["tipo"] == "expansion_posicional":
                    nombre = nombres_base.get(paso["base_origen"], f'Base {paso["base_origen"]}')
                    titulo = f'{idx}. Expansión Posicional desde {nombre}'
                    with ui.expansion(titulo, icon='functions').classes('w-full panel-card font-bold text-main timeline-expansion'):
                        filas_html = ""
                        eq_str = ""
                        for t in paso["terminos"]:
                            filas_html += f"<tr><td class='p-2 border-b border-[var(--border-input)] text-center font-mono'>{t['digito']}</td><td class='p-2 border-b border-[var(--border-input)] text-center'>{t['valor']}</td><td class='p-2 border-b border-[var(--border-input)] text-center'>{paso['base_origen']}<sup>{t['potencia']}</sup></td><td class='p-2 border-b border-[var(--border-input)] text-center'>{t['peso']}</td><td class='p-2 border-b border-[var(--border-input)] text-center font-bold text-[var(--accent)]'>{t['producto']}</td></tr>"
                            eq_str += f"({t['valor']} \\times {paso['base_origen']}^{{{t['potencia']}}}) + "

                        eq_str = eq_str[:-3]
                        if paso.get("es_negativo"):
                            eq_str = f"-\\left[ {eq_str} \\right]"
                        eq_str += f" = {paso['total']}"

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
                    nombre = nombres_base.get(paso["base_destino"], f'Base {paso["base_destino"]}')
                    titulo = f'{idx}. Divisiones Sucesivas hacia {nombre}'
                    with ui.expansion(titulo, icon='vertical_align_bottom').classes('w-full panel-card font-bold text-main timeline-expansion'):
                        filas_html = ""
                        for f in paso["filas"]:
                            filas_html += f"<tr><td class='p-2 border-b border-[var(--border-input)] text-center'>{f['dividendo']}</td><td class='p-2 border-b border-[var(--border-input)] text-center'>÷ {f['divisor']}</td><td class='p-2 border-b border-[var(--border-input)] text-center font-bold'>{f['cociente']}</td><td class='p-2 border-b border-[var(--border-input)] text-center font-bold text-[var(--btn-primary-text)] bg-[var(--accent)] rounded-md m-1 block'>{f['residuo']}</td></tr>"

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

            ui.run_javascript("typesetMathWhenReady();")
