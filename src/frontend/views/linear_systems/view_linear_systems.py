"""Vista principal de Sistemas Lineales (Gauss / Gauss-Jordan) en Scalaris."""
from nicegui import ui
from src.frontend.components.app_shell import create_app_shell
from src.frontend.navigation import route_of
from src.frontend.components.equation_grid import EquationGrid
from src.frontend.components.calculator import CalculatorPanel
from src.frontend.components.ai_panel import AIPanel
from .sync_mixin import LinearSystemsSyncMixin
from .history_mixin import LinearSystemsHistoryMixin
from .steps_mixin import LinearSystemsStepsMixin
from .results_mixin import LinearSystemsResultsMixin
from .preview_mixin import LinearSystemsPreviewMixin


class LinearSystemsUI(
    LinearSystemsSyncMixin,
    LinearSystemsHistoryMixin,
    LinearSystemsPreviewMixin,
    LinearSystemsStepsMixin,
    LinearSystemsResultsMixin
):
    """Controlador de vista modular para Sistemas Lineales."""

    def __init__(self, initial_method='gauss'):
        self.grid = EquationGrid()
        self.calculator = CalculatorPanel()
        self.contenedor_resultados = None
        self.mode_tabs = None
        self.method_tabs = None
        self.initial_method = initial_method
        self.reproductor_pasos = None

        # Estado del modo ecuaciones
        self.num_ecuaciones = 3
        self.ecuaciones_inputs = []
        self.contenedor_ecuaciones_lista = None

        # Tools Panel
        self.historial = []
        self.preview_task = None
        self.preview_container = None
        self.historial_container = None

    def build(self, handoff_token: str = ''):
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=route_of('sistemas'))
        self.grid.inject_scripts()
        self.grid.on_data_change = self._on_grid_change
        self.calculator.inject_scripts()

        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4 view-root'):
            self.handoff_slot = ui.column().classes('w-full')
            # Header con Título y Selectores
            with ui.row().classes('w-full justify-between items-center mb-8 gap-4 flex-wrap'):
                # Selector de Modo (Matriz/Ecuaciones)
                with ui.tabs().classes('neo-tabs mode-tabs').props('dense no-caps') as self.mode_tabs:
                    ui.tab('Matriz', icon='grid_4x4')
                    ui.tab('Ecuaciones', icon='functions')

                # Selector de Método
                with ui.tabs().classes('neo-tabs method-tabs').props('dense no-caps') as self.method_tabs:
                    ui.tab('gauss', label='Gauss')
                    ui.tab('gauss-jordan', label='Gauss-Jordan')
                self.method_tabs.value = self.initial_method
                self.method_tabs.on_value_change(self.trigger_flip_animation)

                def on_mode_change(e):
                    if e.value == 'Ecuaciones' and not self.is_matriz_empty():
                        self.sync_from_matrix()
                    elif e.value == 'Matriz' and not self.is_ecuaciones_empty():
                        self.sync_from_equations()
                    self._trigger_live_preview()

                self.mode_tabs.on_value_change(on_mode_change)

            with ui.element('div').classes('layout-split mb-8'):
                with ui.column().classes('layout-pane'):
                    with ui.tab_panels(self.mode_tabs, value='Matriz').classes(
                        'w-full p-0 overflow-hidden panel-card main-grid-panel'
                    ).props('animated transition-prev="slide-right" transition-next="slide-left"'):

                        # TAB MATRIZ
                        with ui.tab_panel('Matriz').classes('p-6'):
                            with ui.row().classes('w-full justify-end mb-4'):
                                self.sync_btn_from_eq = ui.button(
                                    'Sincronizar desde Ecuaciones',
                                    icon='sync',
                                    on_click=self.sync_from_equations,
                                    color=None
                                ).classes('btn-ghost text-xs py-1 px-3').props('ripple=false')

                            self.grid.build_grid_container()

                        # TAB ECUACIONES
                        with ui.tab_panel('Ecuaciones').classes('p-6'):
                            with ui.row().classes('w-full justify-between items-center mb-6'):
                                ui.label('Sistema de Ecuaciones').classes('text-lg font-bold text-main')
                                self.sync_btn_from_matrix = ui.button(
                                    'Sincronizar desde Matriz',
                                    icon='sync',
                                    on_click=self.sync_from_matrix,
                                    color=None
                                ).classes('btn-ghost text-xs py-1 px-3').props('ripple=false')

                                with ui.row().classes('gap-2 ml-auto'):
                                    ui.button(icon='remove', on_click=self.remove_eq, color=None).classes(
                                        'btn-neo-icon w-8 h-8 p-0'
                                    ).props('ripple=false aria-label="Quitar ecuación"').tooltip('Quitar ecuación')
                                    ui.button(icon='add', on_click=self.add_eq, color=None).classes(
                                        'btn-neo-icon w-8 h-8 p-0'
                                    ).props('ripple=false aria-label="Añadir ecuación"').tooltip('Añadir ecuación')

                            self.contenedor_ecuaciones_lista = ui.column().classes('w-full')
                            self.render_ecuaciones()

                    with ui.row().classes('w-full mt-6 gap-4'):
                        ui.button(
                            icon='delete', on_click=self.confirmar_limpieza, color=None
                        ).classes('btn-ghost flex-1 py-3').props('ripple=false id="btn-limpiar-main" aria-label="Limpiar"').tooltip('Limpiar')
                        ui.button(
                            'Resolver', on_click=lambda e: self.resolver_sistema(e.sender), color=None
                        ).classes('btn-primary flex-[2] py-3').props('ripple=false')

                with ui.column().classes('layout-pane tools-panel'):
                    with ui.tabs().classes('neo-tabs w-full').props('dense no-caps') as self.tools_tabs:
                        ui.tab('teclado', label='Teclado')
                        ui.tab('preview', label='Vista previa')
                        ui.tab('history', label='Historial')
                    self.tools_tabs.on_value_change(
                        lambda e: self._trigger_live_preview() if e.value == 'preview' else None
                    )

                    with ui.tab_panels(self.tools_tabs, value='teclado').classes('w-full p-0 bg-transparent').props('animated'):
                        with ui.tab_panel('teclado').classes('p-0 mt-4'):
                            self.calculator.build(self.mode_tabs)

                        with ui.tab_panel('preview').classes('p-6 panel-card mt-4 min-h-[300px] items-center'):
                            ui.label('Vista Previa en Vivo').classes('font-bold text-main mb-4')
                            self.preview_container = ui.column().classes('w-full items-center justify-center')
                            self._trigger_live_preview()

                        with ui.tab_panel('history').classes('p-6 panel-card mt-4 min-h-[300px]'):
                            ui.label('Últimos 5 sistemas resueltos').classes('font-bold text-main mb-4')
                            self.historial_container = ui.column().classes('w-full')
                            self._render_history()

            self.contenedor_resultados = ui.column().classes(
                'w-full panel-card p-6 items-center justify-center min-h-[400px]'
            ).props('id="resultados-container"')
            self.reset_resultados()
            self.update_sync_buttons()

        self.ai_panel.build()

        from src.frontend.components.handoff import consume_matrix, render_handoff_notice, clean_handoff_url
        res = consume_matrix(handoff_token, max_n=10)
        if res is not None:
            with self.handoff_slot:
                n = len(res.data) if res.data else 0
                render_handoff_notice(res, f"Cargamos A ({n}×{n}) desde {res.source_name}. El vector b está vacío: complétalo y presiona Resolver.")
            if res.status == 'ok':
                if self.mode_tabs.value == 'Ecuaciones':
                    self.mode_tabs.set_value('Matriz')
                self.grid.clear()
                self.grid.m = self.grid.n = n
                self.grid._cache_A.clear()
                self.grid._cache_b.clear()
                for i, row in enumerate(res.data):
                    for j, val in enumerate(row):
                        if val != "0":
                            self.grid._cache_A[(i, j)] = val
                self.grid.generar_cuadricula()
                self._on_grid_change()
            clean_handoff_url()

    def get_ai_context(self):
        from src.ai.context import AIContext, describir_matriz, sanitize_user_string, is_stale, window_note_from
        empty = True
        label = "Sistema Lineal"
        input_data = {}
        
        if self.mode_tabs.value == 'Ecuaciones':
            lineas = [sanitize_user_string(inp.value, 120) for inp in self.ecuaciones_inputs if inp.value]
            if lineas:
                empty = False
                label = f"Sistema de {len(lineas)} ecuaciones"
                input_data = {"ecuaciones": lineas}
        else:
            matrix_A_vals, vector_b_vals = self.grid.get_matrix_data()
            if matrix_A_vals and any(any(c for c in r if str(c).strip() not in ('0', '', '0.0')) for r in matrix_A_vals):
                empty = False
                n_eq = len(matrix_A_vals)
                n_vars = len(matrix_A_vals[0])
                label = f"Sistema {n_eq}×{n_vars} (matriz)"
                
                # Format to strings
                data_a = [[sanitize_user_string(c, 32) for c in r] for r in matrix_A_vals]
                data_b = [[sanitize_user_string(v, 32)] for v in vector_b_vals]
                
                desc_a = describir_matriz(data_a)
                desc_b = describir_matriz(data_b)
                input_data = {
                    "A": desc_a,
                    "b": desc_b
                }
                
        if empty:
            return AIContext("sistemas", "Sistemas de ecuaciones", label, {}, empty=True)
            
        ctx = AIContext("sistemas", "Sistemas de ecuaciones", label, input_data)
        if "A" in input_data and "b" in input_data:
            ctx.window_note = window_note_from(input_data["A"], input_data["b"])
        
        method_val = getattr(getattr(self, 'method_select', None), 'value', getattr(self.method_tabs, 'value', 'gauss'))
        entrada_actual = {"mode": self.mode_tabs.value, "method": method_val}
        if self.mode_tabs.value == 'Ecuaciones':
            entrada_actual["ecuaciones"] = [inp.value for inp in self.ecuaciones_inputs]
        else:
            matrix_A_vals, vector_b_vals = self.grid.get_matrix_data()
            entrada_actual["A"] = matrix_A_vals
            entrada_actual["b"] = vector_b_vals
        ctx.stale = is_stale(entrada_actual, getattr(self, '_result_fp', None))
        
        if getattr(self, 'last_result', None):
            if ctx.stale:
                ctx.result = None
            else:
                res = self.last_result
                ctx.result = {
                    "status": res.get("status", "ERROR")
                }
                msg = res.get("classification") or res.get("message")
                if msg:
                    ctx.result["message"] = msg
                
        return ctx

    def get_ai_signals(self):
        from src.frontend.suggestions import Signals, first_invalid_cell
        try:
            state = "none"
            flags = set()
            invalid = None
            
            if self.mode_tabs.value == 'Matriz':
                items = []
                for (r, c), val in self.grid._cache_A.items():
                    items.append((f"A[{r+1},{c+1}]", val))
                for r, val in self.grid._cache_b.items():
                    items.append((f"b[{r+1}]", val))
                invalid = first_invalid_cell(items)
                                    
            if self.grid.m > self.grid.n:
                flags.add("m_gt_n")
                
            res = getattr(self, 'last_result', None)
            if res and not getattr(self.get_ai_context(), 'stale', True):
                st = res.get("status")
                if st == "UNIQUE_SOLUTION": state = "unique"
                elif st == "INFINITE_SOLUTIONS": state = "infinite"
                elif st == "NO_SOLUTION": state = "no_solution"
                
                steps = res.get("intermediate_steps_latex", [])
                if any(step.get("descripcion", "").startswith("Intercambio") for step in steps):
                    flags.add("swap")
                    
            return Signals(tool="sistemas", state=state, flags=frozenset(flags), invalid=invalid)
        except Exception:
            return None
