"""Vista principal del Conversor de Sistemas Numéricos en Scalaris."""
from nicegui import ui
from src.backend.solvers.numeric_systems.conversor_bases import ConversorBases
from src.frontend.components.app_shell import create_app_shell
from src.frontend.navigation import route_of
from src.frontend.components.ai_panel import AIPanel
from .interaction_mixin import NumericSystemsInteractionMixin
from .rendering_mixin import NumericSystemsRenderingMixin


class NumericSystemsUI(NumericSystemsInteractionMixin, NumericSystemsRenderingMixin):
    """Controlador de vista modular para conversión de bases numéricas."""

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
        self.btn_convertir = None
        self.tiene_resultado = False

        self.regex_bases = {
            'binario': r'^[+-]?0[bB]?[01_]*$|^[+-]?[01_]*$',
            'octal': r'^[+-]?0[oO]?[0-7_]*$|^[+-]?[0-7_]*$',
            'decimal': r'^[+-]?[0-9_]*$',
            'hexadecimal': r'^[+-]?0[xX]?[0-9A-Fa-f_]*$|^[+-]?[0-9A-Fa-f_]*$'
        }

    def build(self):
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=route_of('bases'))

        with ui.column().classes('w-full max-w-4xl mx-auto items-center q-pa-md mt-6 view-root'):
            # --- HERO SECTION (Entrada) ---
            with ui.column().classes('w-full panel-card p-6 gap-6'):
                ui.label('Conversor de bases').classes('text-2xl font-bold text-main')

                # Selector de sistemas numéricos
                with ui.row().classes('w-full items-center gap-3 flex-nowrap'):
                    with ui.tabs().classes('neo-tabs method-tabs tabs-wide flex-1') as self.tabs_origen:
                        ui.tab('decimal', label='Dec')
                        ui.tab('binario', label='Bin')
                        ui.tab('octal', label='Oct')
                        ui.tab('hexadecimal', label='Hex')

                    ui.icon('swap_horiz', size='sm').classes('text-sec flex-shrink-0')

                    with ui.tabs().classes('neo-tabs method-tabs tabs-wide flex-1') as self.tabs_destino:
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
                        self.input_valor = ui.input(placeholder='0').classes(
                            'w-full matrix-input conversor-input'
                        ).style('font-size: var(--fs-display) !important; padding: 20px 76px 20px 20px;')
                        self.input_valor.props('autocomplete="off" spellcheck="false"')
                        self.input_valor.on_value_change(self._on_input_change)
                        self.input_valor.on('keydown.enter', self._convertir_btn)

                        with ui.row().classes('absolute right-6 top-1/2 -translate-y-1/2'):
                            ui.button(
                                icon='content_paste', on_click=self._pegar_portapapeles, color=None
                            ).classes('btn-neo-icon w-10 h-10 p-0 text-sec').props('ripple=false aria-label="Pegar"').tooltip('Pegar')

                    self.lbl_error = ui.label('').classes('fs-small').style(
                        'color: var(--error); margin-left: 8px; min-height: 20px;'
                    )

                # Tira visual de bits y ancho
                with ui.row().classes('w-full justify-between items-center mt-2'):
                    self.lbl_info_bits = ui.label('').classes('text-sm font-mono text-sec font-bold')
                    self.bits_container = ui.row().classes('gap-1 items-center flex-wrap')

                self.btn_convertir = ui.button(
                    'Convertir', on_click=self._convertir_btn, color=None
                ).classes('btn-primary w-full py-3 text-lg mt-2 font-bold')

                self.chips_container = ui.column().classes('w-full mt-2')

            # --- RESULTADOS (Tarjetas 2x2) ---
            with ui.element('div').classes('layout-grid-2 mt-6'):
                self._crear_tarjeta_resultado('decimal', 'Decimal', '10')
                self._crear_tarjeta_resultado('hexadecimal', 'Hexadecimal', '16')
                self._crear_tarjeta_resultado('binario', 'Binario', '2')
                self._crear_tarjeta_resultado('octal', 'Octal', '8')

            # --- PROCEDIMIENTO ---
            self.pasos_container = ui.column().classes('w-full gap-4 mt-6 hidden')

        self.tabs_origen.on_value_change(self._cambiar_base_origen)
        self.tabs_destino.on_value_change(self._cambiar_base_destino)

        self.tabs_origen.set_value('decimal')
        self.tabs_destino.set_value('todas')

        self.ai_panel.build()
        self._actualizar_ejemplos()

    def get_ai_context(self):
        from src.ai.context import AIContext, sanitize_user_string, is_stale
        val = getattr(getattr(self, 'input_valor', None), 'value', None)
        if not val:
            return AIContext("bases", "Conversor de bases", "Conversión", {}, empty=True)
            
        base_orig = getattr(getattr(self, 'tabs_origen', None), 'value', self.base_activa)
        base_dest = getattr(getattr(self, 'tabs_destino', None), 'value', self.base_destino)
        
        ctx = AIContext(
            "bases", 
            "Conversor de bases", 
            f"{base_orig} a {base_dest}", 
            {
                "valor_entrada": sanitize_user_string(val, 64),
                "base_origen": base_orig,
                "base_destino": base_dest
            }
        )
        
        entrada_actual = {"valor": val, "base_origen": self.base_activa, "base_destino": self.base_destino}
        ctx.stale = is_stale(entrada_actual, getattr(self, '_result_fp', None))
        
        if getattr(self, 'tiene_resultado', False):
            if ctx.stale:
                ctx.result = None
            else:
                ctx.result = {
                    "status": "SUCCESS",
                    "resultados": self.resultados.copy()
                }
        elif getattr(getattr(self, 'lbl_error', None), 'text', None):
            ctx.result = {
                "status": "ERROR",
                "message": self.lbl_error.text
            }
            
        return ctx

    def get_ai_signals(self):
        from src.frontend.suggestions import Signals, InvalidCell
        import re
        try:
            state = "none"
            flags = set()
            invalid = None
            
            val = self.input_valor.value.strip() if getattr(self, 'input_valor', None) and self.input_valor.value else ""
            if val and self.base_activa in self.regex_bases:
                if not re.match(self.regex_bases[self.base_activa], val.replace(" ", "")):
                    invalid = InvalidCell(label="el número")
                    
            if getattr(self, 'tiene_resultado', False) and not getattr(self.get_ai_context(), 'stale', True):
                state = "result"
                
                res = getattr(self, 'resultados_completos', {})
                pasos = res.get("pasos", [])
                
                if any(p.get("tipo") == "division_sucesiva" for p in pasos):
                    flags.add("division")
                    
                if any(p.get("base_destino") == 16 or p.get("base_origen") == 16 for p in pasos):
                    flags.add("hex")
                    
            return Signals(tool="bases", state=state, flags=frozenset(flags), invalid=invalid)
        except Exception:
            return None