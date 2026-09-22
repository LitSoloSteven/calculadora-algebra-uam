"""Vista principal de Sistemas Lineales (Gauss / Gauss-Jordan) en Scalaris."""
from nicegui import ui
from src.frontend.components.navbar import create_navbar
from src.frontend.components.equation_grid import EquationGrid
from src.frontend.components.calculator import CalculatorPanel
from src.frontend.components.ai_panel import AIPanel
from .sync_mixin import LinearSystemsSyncMixin
from .history_mixin import LinearSystemsHistoryMixin
from .graphics_mixin import LinearSystemsGraphicsMixin
from .results_mixin import LinearSystemsResultsMixin


class LinearSystemsUI(
    LinearSystemsSyncMixin,
    LinearSystemsHistoryMixin,
    LinearSystemsGraphicsMixin,
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

        # Estado del modo ecuaciones
        self.num_ecuaciones = 3
        self.ecuaciones_inputs = []
        self.contenedor_ecuaciones_lista = None

        # Tools Panel
        self.historial = []
        self.preview_task = None
        self.preview_container = None
        self.historial_container = None

    def build(self):
        self.ai_panel = AIPanel(self)
        create_navbar(self, active_route='/sistemas-lineales')
        self.grid.inject_scripts()
        self.grid.on_data_change = self._on_grid_change
        self.calculator.inject_scripts()

        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4'):
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

                self.mode_tabs.on_value_change(on_mode_change)

            with ui.row().classes('w-full flex-col lg:flex-row items-stretch gap-8 mb-8'):
                with ui.column().classes('w-full lg:w-1/2 lg:flex-1'):
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
                                    ).props('ripple=false')
                                    ui.button(icon='add', on_click=self.add_eq, color=None).classes(
                                        'btn-neo-icon w-8 h-8 p-0'
                                    ).props('ripple=false')

                            self.contenedor_ecuaciones_lista = ui.column().classes('w-full')
                            self.render_ecuaciones()

                    with ui.row().classes('w-full mt-6 gap-4'):
                        ui.button(
                            icon='delete', on_click=self.confirmar_limpieza, color=None
                        ).classes('btn-ghost flex-1 py-3').props('ripple=false id="btn-limpiar-main"').tooltip('Limpiar')
                        ui.button(
                            'Resolver', on_click=lambda e: self.resolver_sistema(e.sender), color=None
                        ).classes('btn-primary flex-[2] py-3').props('ripple=false')

                with ui.column().classes('w-full lg:w-1/2 lg:flex-1 tools-panel'):
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
