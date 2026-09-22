"""Mixin de interacción de usuario y gestión de entradas para Sistemas Numéricos."""
import asyncio
import re
from nicegui import ui


class NumericSystemsInteractionMixin:
    """Maneja cambios de base, portapapeles, eventos de input y desincronización visual."""

    def _cambiar_base_origen(self, e):
        if not e.value:
            return
        self.base_activa = e.value
        self._actualizar_ejemplos()
        if hasattr(self, 'input_valor'):
            try:
                asyncio.create_task(self._on_input_change(None))
            except RuntimeError:
                pass

    def _cambiar_base_destino(self, e):
        if not e.value:
            return
        self.base_destino = e.value
        if hasattr(self, 'input_valor'):
            if self.tiene_resultado:
                self._aplicar_opacidad_tarjetas(revelar=False)
                val = self.input_valor.value or ''
                if val.strip():
                    try:
                        asyncio.create_task(self._ejecutar_conversion(val, inmediato=True, revelar_tarjetas=False))
                    except RuntimeError:
                        pass
            else:
                try:
                    asyncio.create_task(self._on_input_change(None))
                except RuntimeError:
                    pass

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
                ui.button(
                    ej,
                    on_click=lambda e, val=ej: self._set_input(val),
                    color=None
                ).classes('btn-ghost py-0 px-3 min-h-0 text-xs font-mono').props('ripple=false')

    def _set_input(self, val):
        self.input_valor.set_value(val)
        asyncio.create_task(self._on_input_change(None))

    async def _pegar_portapapeles(self):
        try:
            val = await ui.run_javascript('navigator.clipboard.readText()', timeout=15)
            if val:
                self._set_input(val.strip())
        except Exception:
            self.lbl_error.text = "Error al pegar: permiso denegado o portapapeles vacío."

    async def _copiar_resultado(self, id_base, btn):
        val = self.resultados.get(id_base, '').replace(' ', '')
        if not val:
            return
        try:
            success = await ui.run_javascript(
                f'navigator.clipboard.writeText("{val}").then(() => true).catch(() => false)',
                timeout=2.0
            )
            if not success:
                ui.notify("No se pudo copiar", type="warning")
                return
        except Exception:
            pass

        btn.props('icon=check color=positive')

        def reset_icon():
            btn.props(remove='color')
            btn.props('icon=content_copy')

        ui.timer(2.0, reset_icon, once=True)

    def _swap_base(self, nueva_base):
        if nueva_base == self.base_activa:
            return
        val = self.resultados.get(nueva_base, '').replace(' ', '')
        self.tabs_origen.set_value(nueva_base)
        self._set_input(val)

    async def _on_input_change(self, e):
        val = self.input_valor.value or ''

        if val and not re.match(self.regex_bases[self.base_activa], val.replace(" ", "")):
            await ui.run_javascript('''
                const inp = document.querySelector(".conversor-input");
                if(inp) {
                    inp.classList.remove("animate-shake");
                    void inp.offsetWidth;
                    inp.classList.add("animate-shake");
                }
            ''')
            self.lbl_error.text = f'Base {self.base_activa}: solo se admiten caracteres válidos.'
            return

        self.lbl_error.text = ''
        if self.tiene_resultado:
            self._marcar_resultado_desincronizado()

    def _marcar_resultado_desincronizado(self):
        """Atenúa los resultados visibles al cambiar el input hasta volver a convertir."""
        for card in self.ui_cards.values():
            card.style('opacity: 0.45;')
        if self.bits_container:
            self.bits_container.style('opacity: 0.45;')

    def _aplicar_opacidad_tarjetas(self, revelar=True):
        for base, card in self.ui_cards.items():
            if revelar:
                card.style('opacity: 1; transform: translateY(0);')

            if self.base_destino == 'todas':
                opacidad = "0.45" if base == self.base_activa else "1"
            else:
                opacidad = "1" if base == self.base_destino else "0.45"

            if base in self.ui_valores:
                self.ui_valores[base].style(f'opacity: {opacidad};')
        if self.bits_container:
            self.bits_container.style('opacity: 1;')

    async def _convertir_btn(self, e=None):
        btn = self.btn_convertir
        val = self.input_valor.value or ''
        if not val.strip():
            ui.notify('Ingresá un valor para convertir.', type='warning')
            return

        val_clean = val.replace(" ", "")
        if not re.match(self.regex_bases[self.base_activa], val_clean):
            ui.notify(f'Base {self.base_activa}: solo se admiten caracteres válidos.', type='warning')
            return

        if btn:
            btn.props('loading=true')
        try:
            if not await self._ejecutar_conversion(val, inmediato=True, revelar_tarjetas=False):
                return

            for card in self.ui_cards.values():
                card.style('opacity: 0; transform: translateY(16px);')

            await asyncio.sleep(0.32)

            for i, (base, card) in enumerate(self.ui_cards.items()):
                card.style('opacity: 1; transform: translateY(0);')
                await asyncio.sleep(0.04)

            self._aplicar_opacidad_tarjetas(revelar=True)
            self._mostrar_procedimiento()
        finally:
            if btn:
                btn.props('loading=false')
