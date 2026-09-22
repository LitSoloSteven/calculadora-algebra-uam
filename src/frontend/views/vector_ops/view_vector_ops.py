"""Vista principal de Operaciones con Vectores en Scalaris."""
import json
import asyncio
from nicegui import ui
from src.frontend.components.navbar import create_navbar
from src.frontend.components.ai_panel import AIPanel
from src.frontend.components.vector_capture import VectorCapturePanel
from src.frontend.controllers.vector_ops.controller_vector_ops import VectorOpsController
from .results_mixin import VectorOpsResultsMixin


class VectorOpsUI(VectorOpsResultsMixin):
    """Controlador de vista modular para operaciones con vectores."""

    def __init__(self):
        self.active_op = 'add_sub'
        self.ai_panel = None
        self.right_panel = None
        self.current_result = None
        self.btn_calculate = None

        # 1. Suma / Resta
        self.panel_add_sub = VectorCapturePanel(
            panel_id="p_add", min_vectors=2, max_vectors=2
        )
        # 2. Escalar x Vector
        self.panel_scalar = VectorCapturePanel(
            panel_id="p_scal", min_vectors=1, max_vectors=1
        )
        # 3. Combinación Lineal
        self.panel_lin_comb = VectorCapturePanel(
            panel_id="p_lin", min_vectors=2, max_vectors=9,
            allow_orientation_toggle=False, default_orientation='column',
            first_vector_fixed_label="b"
        )

        self.panels = {
            'add_sub': self.panel_add_sub,
            'scalar': self.panel_scalar,
            'lin_comb': self.panel_lin_comb
        }

        # Estado de pestañas específicas
        self.add_sub_operation = 'add'
        self.add_sub_strict = False
        self.scalar_value = "2"

    @property
    def vector_panel(self):
        return self.panels[self.active_op]

    def build(self):
        self.ai_panel = AIPanel(self)
        create_navbar(self, active_route='/vectores')
        ui.add_head_html('<script>if(window.typesetMathWhenReady){window.typesetMathWhenReady();}</script>')

        self.panel_add_sub.inject_scripts()

        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4'):
            with ui.row().classes('w-full flex-col lg:flex-row items-stretch gap-8 mb-8'):
                # --- PANEL IZQUIERDO (Entrada) ---
                with ui.column().classes('w-full lg:w-1/2 lg:flex-1 p-8 bg-[var(--bg-page)]').style('scroll-behavior: smooth;') as self.left_panel:
                    with ui.row().classes('w-full justify-between items-center mb-8 gap-4 flex-wrap'):
                        with ui.tabs().classes('neo-tabs method-tabs').props('dense no-caps').style('max-width: 560px !important') as self.method_tabs:
                            ui.tab('add_sub', label='Suma / Resta')
                            ui.tab('scalar', label='Escalar × Vector')
                            ui.tab('lin_comb', label='Combinación Lineal')
                        self.method_tabs.value = self.active_op
                        self.method_tabs.on_value_change(self.on_tab_change)

                    # Tab Panels
                    with ui.tab_panels(self.method_tabs, value=self.active_op).classes('w-full bg-transparent p-0').style('flex: 1;'):
                        # 1. Suma / Resta
                        with ui.tab_panel('add_sub').classes('p-0'):
                            with ui.row().classes('w-full justify-between items-center mb-4 panel-card p-4'):
                                with ui.row().classes('gap-4 items-center'):
                                    ui.label('Operación:').classes('font-bold')
                                    self.op_select = ui.select(
                                        {'add': 'Suma', 'subtract': 'Resta'},
                                        value=self.add_sub_operation,
                                        on_change=lambda e: setattr(self, 'add_sub_operation', e.value)
                                    ).classes('neo-select w-44').props('popup-content-class="neo-select-menu"')
                                self.strict_check = ui.checkbox(
                                    'Estricto (No auto-transponer)',
                                    value=self.add_sub_strict,
                                    on_change=lambda e: setattr(self, 'add_sub_strict', e.value)
                                ).classes('neo-checkbox')

                            self.panel_add_sub.build_container()

                        # 2. Escalar x Vector
                        with ui.tab_panel('scalar').classes('p-0'):
                            with ui.row().classes('w-full items-center mb-4 panel-card p-4 gap-4'):
                                ui.label('Escalar (k):').classes('font-bold')
                                self.scalar_input = ui.input(
                                    value=self.scalar_value,
                                    on_change=lambda e: setattr(self, 'scalar_value', e.value)
                                ).classes('w-32 matrix-input').props('borderless')

                            self.panel_scalar.build_container()

                        # 3. Combinación Lineal
                        with ui.tab_panel('lin_comb').classes('p-0'):
                            ui.markdown('Evalúa si el vector **b** es combinación lineal de los demás vectores.').classes('mb-4 text-sec text-sm')
                            self.panel_lin_comb.build_container()

                    # Action Bar
                    with ui.row().classes('w-full justify-between mt-8 pt-4 border-t border-[var(--border-input)] items-center'):
                        ui.button('Limpiar', icon='delete', on_click=self.clear_all, color=None).classes('btn-ghost').props('ripple=false id="btn-limpiar-main"')
                        self.btn_calculate = ui.button('Calcular', icon='calculate', on_click=self.calculate, color=None).classes('btn-primary px-8 py-2 font-bold')

                # --- PANEL DERECHO (Resultados) ---
                with ui.column().classes('w-full lg:w-1/2 lg:flex-1 p-8 bg-[var(--bg-page)]') as self.right_panel:
                    self.render_empty_state()

        self.ai_panel.build()

    def on_tab_change(self, e):
        if not e.value:
            return
        self.active_op = e.value
        self.render_empty_state()

    async def clear_all(self):
        is_empty = all(not any(str(val).strip() for val in v['cache'].values()) for v in self.vector_panel.vectors.values())
        if is_empty:
            ui.notify('No hay datos para limpiar', type='warning')
            return

        ui.run_javascript("if(window.animateGarbageCollection) window.animateGarbageCollection();")
        await asyncio.sleep(0.8)
        self.vector_panel.clear()
        if self.active_op == 'scalar':
            self.scalar_value = "2"
            self.scalar_input.value = "2"
        self.render_empty_state()

    async def calculate(self):
        self.btn_calculate.disable()
        self.btn_calculate.props('loading')
        try:
            panel = self.vector_panel
            try:
                vecs_dict = panel.get_vectors_dict()
            except ValueError as e:
                ui.notify(str(e), type='negative')
                return

            if self.active_op == 'add_sub':
                v_keys = list(vecs_dict.keys())
                payload = {
                    "operation": self.add_sub_operation,
                    "v1": vecs_dict[v_keys[0]],
                    "v2": vecs_dict[v_keys[1]],
                    "strict": self.add_sub_strict
                }
                res_str = VectorOpsController.process_add_subtract(json.dumps(payload))

            elif self.active_op == 'scalar':
                v_keys = list(vecs_dict.keys())
                payload = {
                    "scalar": self.scalar_input.value,
                    "v": vecs_dict[v_keys[0]]
                }
                res_str = VectorOpsController.process_scalar_multiply(json.dumps(payload))

            elif self.active_op == 'lin_comb':
                b_key = self.panel_lin_comb.first_vector_fixed_label
                b_vec = vecs_dict.pop(b_key, None)
                if not b_vec:
                    ui.notify("No se encontró el vector b.", type='negative')
                    return

                other_vecs = list(vecs_dict.values())
                payload = {
                    "b": b_vec,
                    "vectors": other_vecs
                }
                res_str = VectorOpsController.process_linear_combination(json.dumps(payload))

            res = json.loads(res_str)
            self.current_result = res
            self.render_result(res)

            ui.run_javascript("setTimeout(() => { if(window.typesetMathWhenReady) window.typesetMathWhenReady(); }, 100);")

        except Exception as e:
            ui.notify(f"Error inesperado: {str(e)}", type='negative')
        finally:
            self.btn_calculate.enable()
            self.btn_calculate.props(remove='loading')
