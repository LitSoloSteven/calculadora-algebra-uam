import json
import asyncio
from nicegui import ui
from src.frontend.components.navbar import create_navbar
from src.frontend.components.ai_panel import AIPanel
from src.frontend.components.vector_capture import VectorCapturePanel
from src.frontend.controllers.vector_ops.controller_vector_ops import VectorOpsController

class VectorOpsUI:
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
        
        # State variables for specific tabs
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
        
        # Inyectar scripts para atajos de teclado y paste
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
                                    self.op_select = ui.select({'add': 'Suma', 'subtract': 'Resta'}, value=self.add_sub_operation, on_change=lambda e: setattr(self, 'add_sub_operation', e.value)).classes('neo-select w-44').props('popup-content-class="neo-select-menu"')
                                self.strict_check = ui.checkbox('Estricto (No auto-transponer)', value=self.add_sub_strict, on_change=lambda e: setattr(self, 'add_sub_strict', e.value)).classes('neo-checkbox')
                                
                            self.panel_add_sub.build_container()
                            
                        # 2. Escalar x Vector
                        with ui.tab_panel('scalar').classes('p-0'):
                            with ui.row().classes('w-full items-center mb-4 panel-card p-4 gap-4'):
                                ui.label('Escalar (k):').classes('font-bold')
                                self.scalar_input = ui.input(value=self.scalar_value, on_change=lambda e: setattr(self, 'scalar_value', e.value)).classes('w-32 matrix-input').props('borderless')
                                
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
        if not e.value: return
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

    def render_empty_state(self):
        if not self.right_panel: return
        self.right_panel.clear()
        with self.right_panel:
            with ui.column().classes('w-full h-full justify-center items-center text-center opacity-50'):
                ui.icon('functions', size='4rem').classes('mb-4')
                ui.label('Ingresa los vectores y presiona Calcular').classes('text-lg')
        
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
            
            # Re-typeset math
            ui.run_javascript("setTimeout(() => { if(window.typesetMathWhenReady) window.typesetMathWhenReady(); }, 100);")
            
        except Exception as e:
            ui.notify(f"Error inesperado: {str(e)}", type='negative')
        finally:
            self.btn_calculate.enable()
            self.btn_calculate.props(remove='loading')

    def render_result(self, res: dict):
        self.right_panel.clear()
        
        with self.right_panel:
            status = res.get('status', 'ERROR')
            msg = res.get('message', '')
            
            if status == 'ERROR':
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-6 w-fit'):
                    ui.icon('close', size='sm')
                    ui.label(msg).classes('font-bold')
                return

            if self.active_op == 'lin_comb':
                if status == 'UNIQUE':
                    badge_class, icon = 'badge-success', 'check'
                elif status == 'INFINITE':
                    badge_class, icon = 'badge-warning', 'warning_amber'
                else:  # NO_SOLUTION
                    badge_class, icon = 'badge-error', 'close'
            else:
                badge_class, icon = 'badge-success', 'check'

            with ui.row().classes(f'items-center gap-2 px-4 py-2 {badge_class} mb-6 w-fit'):
                ui.icon(icon, size='sm')
                ui.label(msg).classes('font-bold')
                
            # Content
            if self.active_op in ['add_sub', 'scalar']:
                self.render_steps_and_result(res)
            else:
                self.render_linear_combination_result(res)
                
    def render_steps_and_result(self, res: dict):
        # Result matrix
        if 'latex_details' in res and res['latex_details']:
            final_latex = res['latex_details'][-1]
            if final_latex:
                ui.label('Resultado').classes('text-xl font-bold mb-4 text-main')
                with ui.card().classes('panel-card w-full p-6 mb-6 items-center justify-center'):
                    ui.html(f'<div class="math-label overflow-x-auto p-4 text-lg">$$ {final_latex} $$</div>')
                    
        # Steps
        steps = res.get('steps', [])
        if len(steps) > 1:
            with ui.expansion('Ver Pasos de Resolución', icon='list').classes('w-full panel-card rounded-xl overflow-hidden').props('header-class="text-main font-bold"'):
                with ui.column().classes('w-full p-4 gap-6 bg-[var(--input-bg)]'):
                    for i, step in enumerate(steps):
                        desc = step.get('description', '')
                        latex = step.get('detail_latex', '')
                        
                        if not latex and step.get('matrix'):
                            # Fallback just in case
                            from src.backend.utils.formatters import matrix_to_latex
                            latex = matrix_to_latex(step['matrix'])
                            
                        with ui.column().classes('w-full'):
                            ui.label(f'Paso {i}: {desc}').classes('text-sm font-bold text-sec mb-2')
                            if latex:
                                ui.html(f'<div class="math-label bg-[var(--bg-elevated)] p-4 rounded-lg shadow-sm border border-[var(--border-input)] overflow-x-auto text-center">$$ {latex} $$</div>')

    def render_linear_combination_result(self, res: dict):
        status = res.get('status')
        es_comb = res.get('es_combinacion_lineal', False)
        
        # Details
        if status == 'UNIQUE':
            coef_str = ", ".join(res.get('coeficientes_str', []))
            ui.markdown(f"**Coeficientes:** `{coef_str}`").classes('mb-4')
            
            v_step = res.get('verification_step')
            if v_step:
                with ui.card().classes('panel-card w-full p-4 mb-6'):
                    ui.label('Verificación:').classes('font-bold mb-2')
                    ui.label(v_step.get('description', '')).classes('text-sm text-sec mb-2')
                    ui.html(f'<div class="math-label overflow-x-auto">$$ {v_step.get("detail_latex", "")} $$</div>')
                    
        elif status == 'INFINITE':
            sol_str = ", ".join(res.get('solucion_parametrica', []))
            ui.markdown(f"**Solución paramétrica:** `{sol_str}`").classes('mb-4')
            ui.markdown(f"**Variables libres:** `{', '.join(res.get('parametros_libres', []))}`").classes('mb-4')

        # Gauss Steps
        steps = res.get('steps', [])
        if steps:
            from src.backend.utils.formatters import matrix_to_latex
            with ui.expansion('Ver Eliminación Gaussiana', icon='functions').classes('w-full panel-card rounded-xl overflow-hidden mb-4').props('header-class="text-main font-bold"'):
                with ui.column().classes('w-full p-4 gap-6 bg-[var(--input-bg)]'):
                    for i, step in enumerate(steps):
                        desc = step.get('description', '')
                        latex = step.get('detail_latex', '')
                        
                        with ui.column().classes('w-full'):
                            ui.label(f'Paso {i}: {desc}').classes('text-sm font-bold text-sec mb-2')
                            if latex:
                                ui.html(f'<div class="math-label bg-[var(--bg-elevated)] p-4 rounded-lg shadow-sm border border-[var(--border-input)] overflow-x-auto text-center">$$ {latex} $$</div>')
                                
        # Back substitution steps
        back_steps = res.get('back_substitution_steps', [])
        if back_steps:
            with ui.expansion('Ver Sustitución Hacia Atrás', icon='arrow_upward').classes('w-full panel-card rounded-xl overflow-hidden').props('header-class="text-main font-bold"'):
                with ui.column().classes('w-full p-4 gap-4 bg-[var(--input-bg)]'):
                    for bs in back_steps:
                        ui.html(f'<div class="math-label bg-[var(--bg-elevated)] p-3 rounded-lg shadow-sm border border-[var(--border-input)] overflow-x-auto">$$ {bs} $$</div>')
