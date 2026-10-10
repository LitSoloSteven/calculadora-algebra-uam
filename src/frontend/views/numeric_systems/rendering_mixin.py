"""Mixin de renderizado de tarjetas, bits y procedimientos para Sistemas Numéricos."""
import asyncio
from nicegui import ui
from .procedure_mixin import NumericSystemsProcedureMixin


class NumericSystemsRenderingMixin(NumericSystemsProcedureMixin):
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
                    ).classes('btn-ghost w-8 h-8 p-0 text-sec').props('ripple=false aria-label="Usar como entrada"').tooltip('Usar como entrada')
                    ui.button(
                        icon='content_copy',
                        on_click=lambda e, b=id_base: self._copiar_resultado(b, e.sender),
                        color=None
                    ).classes('btn-ghost w-8 h-8 p-0 text-sec').props('ripple=false aria-label="Copiar"').tooltip('Copiar')

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

            val_raw = val
            val_conv = val.upper() if self.base_activa == 'hexadecimal' else val

            metodo = getattr(self.conversor, f"{self.base_activa}_a_todo")
            res = metodo(val_conv, self.base_destino)

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
            
            from src.ai.context import fingerprint
            entrada = {"valor": val_raw, "base_origen": self.base_activa, "base_destino": self.base_destino}
            self._result_fp = fingerprint(entrada)
            p = getattr(self, 'ai_panel', None)
            if p and hasattr(p, 'schedule_context_refresh'):
                p.schedule_context_refresh()

            if getattr(self, 'ai_panel', None) and getattr(self, 'chips_container', None):
                self.chips_container.clear()
                with self.chips_container:
                    self.ai_panel.render_inline_chips()
                    
            return True
        except asyncio.CancelledError:
            pass

    def _agrupar(self, string, n):
        signo = "-" if string.startswith("-") else ""
        s = string.lstrip("-")
        grupos = [s[max(i - n, 0):i] for i in range(len(s), 0, -n)]
        return signo + " ".join(reversed(grupos))

    def _limpiar_resultados(self):
        rep = getattr(self, "reproductor", None)
        if rep is not None and hasattr(rep, "detener"):
            rep.detener()
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
        if getattr(self, 'chips_container', None):
            self.chips_container.clear()

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

