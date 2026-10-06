import json
import asyncio
import logging
import html
from nicegui import ui

logger = logging.getLogger(__name__)
from src.frontend.components.app_shell import create_app_shell
from src.frontend.navigation import route_of
from src.frontend.components.matrix_capture import MatrixCapturePanel
from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixOpsController
from src.frontend.components.ai_panel import AIPanel

class MatrixOpsUI:
    def __init__(self):
        self.capture_panel = MatrixCapturePanel()
        self.contenedor_resultados = None
        self.input_expresion = None

    def reset_resultados(self):
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.icon('data_object', size='4rem').classes('text-placeholder mb-4')
            ui.label('Sin resultados').classes('text-xl font-bold text-main')
            ui.label('Añade matrices y escribe una expresión matemática para empezar').classes('text-sm text-sec mt-2 text-center')

    async def evaluar_expresion(self, btn):
        expresion = self.input_expresion.value
        if not expresion:
            ui.notify('Ingresa una expresión para evaluar.', type='warning')
            return

        btn.props('loading=true')
        try:
            await self._evaluar_core(btn, expresion)
        except Exception as e:
            self._mostrar_error_inesperado(e)
        finally:
            btn.props('loading=false')

    def _mostrar_error_inesperado(self, exc):
        logger.error("Error inesperado al evaluar la expresión", exc_info=exc)
        self.contenedor_resultados.clear()
        self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
        with self.contenedor_resultados:
            with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                ui.icon('close', size='sm')
                ui.label('Ocurrió un error inesperado al evaluar la expresión. Revisa los datos e inténtalo de nuevo.').classes('font-bold')
        ui.notify('Error inesperado', type='negative', position='top')

    async def _evaluar_core(self, btn, expresion):
        await asyncio.sleep(0.1)

        try:
            matrices_dict = self.capture_panel.get_matrices_dict()
            matrices_json = json.dumps(matrices_dict)
        except Exception as e:
            ui.notify(str(e), type='negative')
            return

        respuesta_json_str = MatrixOpsController.process_expression(expresion, matrices_json)
        respuesta = json.loads(respuesta_json_str)
        self.last_result = respuesta
        
        self.contenedor_resultados.clear()

        with self.contenedor_resultados:
            self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
            
            if respuesta.get("status") == "ERROR":
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                    ui.icon('close', size='sm')
                    ui.label(respuesta.get("message", "Error desconocido")).classes('font-bold')
                
                if getattr(self, 'ai_panel', None):
                    self.ai_panel.render_inline_chips()
            else:
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-success mb-6 w-fit'):
                    ui.icon('check', size='sm')
                    ui.label(respuesta.get("message", "Éxito")).classes('font-bold')

                if getattr(self, 'ai_panel', None):
                    self.ai_panel.render_inline_chips()

                if respuesta.get("segment_steps"):
                    ui.label('Evaluación paso a paso:').classes('font-bold text-xl text-main mb-4')
                    for i, step in enumerate(respuesta["segment_steps"]):
                        with ui.column().classes('w-full panel-card p-6 mb-4'):
                            with ui.row().classes('w-full justify-between items-start gap-2'):
                                op_tex = html.escape(step.get("operation_display") or f"\\text{{Paso {i+1}}}")
                                ui.html(f'<div class="math-scroll-container math-label text-lg font-bold">$$ {op_tex} $$</div>').classes('flex-1')
                                
                                if getattr(self, 'ai_panel', None):
                                    from src.frontend.components.glosa_chips import render_explain_button
                                    from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixOpsController
                                    tot = len(respuesta["segment_steps"])
                                    foc_step = MatrixOpsController.build_step_focus(step, i + 1, tot)
                                    render_explain_button(
                                        i + 1,
                                        tot,
                                        foc_step["op"],
                                        lambda idx, st=step, t=tot: self.ai_panel.trigger_explain_step(
                                            MatrixOpsController.build_step_focus(st, idx, t)
                                        ),
                                        is_loading=getattr(self.ai_panel, '_is_sending', False)
                                    )
                                    
                            with ui.row().classes('w-full items-center justify-center gap-4 py-4'):
                                sym = step.get("symbolic_matrix_latex")
                                res = step.get("result_matrix_latex")
                                if sym:
                                    ui.html(f'<div class="math-scroll-container math-label text-xl">$$ {sym} $$</div>')
                                if sym and res:
                                    ui.icon('arrow_forward', size='md').classes('text-sec')
                                if res:
                                    ui.html(f'<div class="math-scroll-container math-label text-xl">$$ {res} $$</div>')
                            
                            if step.get("cell_by_cell_steps"):
                                with ui.expansion('Ver detalle celda a celda', icon='visibility').classes('w-full mt-2 timeline-expansion').props('header-class="font-medium text-sec"'):
                                    for cell_step in step["cell_by_cell_steps"]:
                                        detail = cell_step.get("detail_latex")
                                        if not detail:
                                            continue
                                        ui.html(f'<div class="math-scroll-container math-label w-full py-1">$$ {detail} $$</div>')
                
                mostrar_resultado_final = len(respuesta.get("segment_steps", [])) != 1
                if mostrar_resultado_final and respuesta.get("final_variable") and respuesta.get("result_matrix_latex"):
                    ui.label('Resultado Final:').classes('font-bold text-xl text-main mt-6 mb-4')
                    with ui.row().classes('w-full justify-center items-center panel-card p-6 overflow-x-auto'):
                        ui.html(f'<div class="math-scroll-container math-label text-2xl font-bold">$$ {respuesta["final_variable"]} = {respuesta["result_matrix_latex"]} $$</div>')

        ui.run_javascript('typesetMathWhenReady();')
        ui.run_javascript("replayResultAnimation('resultados-ops');")
        ui.run_javascript("setTimeout(() => { const el = document.getElementById('resultados-ops'); if(el) el.scrollIntoView({behavior: 'smooth', block: 'start'}) }, MOTION.med);")

        from src.ai.context import fingerprint
        entrada = {
            "matrices": {name: dict(m.get('cache', {})) for name, m in self.capture_panel.matrices.items()},
            "expresion": (expresion or "").strip()
        }
        self._result_fp = fingerprint(entrada)
        p = getattr(self, 'ai_panel', None)
        if p and hasattr(p, 'schedule_context_refresh'):
            p.schedule_context_refresh()


    def _on_matrix_change(self):
        p = getattr(self, 'ai_panel', None)
        if p and hasattr(p, 'schedule_context_refresh'):
            p.schedule_context_refresh()

    def build(self):
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=route_of('matrices'))
        self.capture_panel.inject_scripts()
        self.capture_panel.on_data_change = self._on_matrix_change
        
        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4 view-root'):
            with ui.row().classes('w-full justify-between items-center mb-8 gap-4 flex-wrap'):
                ui.label('Matrices').classes('text-2xl font-bold text-main')

            with ui.element('div').classes('layout-split mb-8'):
                # Panel izquierdo (Matrices y expresión)
                with ui.column().classes('layout-pane'):
                    self.capture_panel.build_container()
                    
                    def do_invert(name, mat):
                        if mat['m'] != mat['n']:
                            ui.notify(f"La matriz {name} debe ser cuadrada para invertirla.", type='warning')
                            return
                        if mat['m'] > 10:
                            ui.notify(f"La herramienta de inversa admite hasta 10x10. La matriz {name} es de {mat['m']}x{mat['n']}.", type='warning')
                            return
                        
                        data = []
                        for r in range(mat['m']):
                            row = []
                            for c in range(mat['n']):
                                val = str(mat['cache'].get((r, c), '0')).strip()
                                if not val: val = '0'
                                row.append(val)
                            data.append(row)
                        
                        from src.frontend.components.handoff import put_matrix, handoff_url
                        from src.frontend.navigation import route_of
                        token = put_matrix('matrices', data)
                        ui.navigate.to(handoff_url(route_of('inversa'), token))

                    self.capture_panel.on_invert = do_invert
                    
                    with ui.column().classes('w-full panel-card p-6 mt-4'):
                        ui.label('Expresión Matemática').classes('text-lg font-bold text-main mb-2')
                        self.input_expresion = ui.input(placeholder='Ej. A + B * C').classes('matrix-input w-full text-xl py-2').props('borderless autocomplete="new-password"')
                        self.input_expresion.on_value_change(lambda _: self._on_matrix_change())
                        
                        ui.button('Evaluar', icon='calculate', on_click=lambda e: self.evaluar_expresion(e.sender), color=None).classes('btn-primary w-full py-3 mt-4').props('ripple=false')

                # Panel derecho (Resultados)
                with ui.column().classes('layout-pane'):
                    self.contenedor_resultados = ui.column().classes('w-full panel-card p-6 items-center justify-center min-h-[400px]').props('id="resultados-ops"')
                    self.reset_resultados()
                    
        self.ai_panel.build()

    def get_ai_context(self):
        from src.ai.context import AIContext, describe_matrix, sanitize_user_string, is_stale, window_note_from
        
        try:
            mats = self.capture_panel.get_matrices_dict()
        except Exception:
            mats = {}
            
        expr_val = self.input_expresion.value if hasattr(self, 'input_expresion') and self.input_expresion else ""
        empty = not bool(mats) and not bool(expr_val)
        if empty:
            return AIContext("matrix_ops", "Matrices", "Operaciones", {}, empty=True)
            
        input_data = {}
        descs = []
        for k, v in mats.items():
            if "data" in v:
                sanitized_data = [[sanitize_user_string(c, 32) for c in r] for r in v["data"]]
                d = describe_matrix(sanitized_data)
                input_data[k] = d
                descs.append(d)
                
        if expr_val:
            input_data["expresion"] = sanitize_user_string(expr_val, 200)
            
        ctx = AIContext("matrix_ops", "Matrices", "Matrices y Expresión", input_data)
        ctx.window_note = window_note_from(*descs)
        
        entrada_actual = {
            "matrices": {name: dict(m.get('cache', {})) for name, m in self.capture_panel.matrices.items()},
            "expresion": (expr_val or "").strip()
        }
        ctx.stale = is_stale(entrada_actual, getattr(self, '_result_fp', None))
        
        if getattr(self, 'last_result', None):
            if ctx.stale:
                ctx.result = None
            else:
                res = self.last_result
                ctx.result = {
                    "status": res.get("status", "ERROR"),
                    "message": res.get("message", "")
                }
                if res.get("final_variable"):
                    ctx.result["final_variable"] = res["final_variable"]
                    
        return ctx

    def get_ai_signals(self):
        from src.frontend.suggestions import Signals, first_invalid_cell
        import re
        try:
            state = "none"
            flags = set()
            invalid = None
            
            expr = self.input_expresion.value.strip() if hasattr(self, 'input_expresion') and self.input_expresion and self.input_expresion.value else ""
            
            has_nonzero = False
            items = []
            for name, m in self.capture_panel.matrices.items():
                cache = m.get('cache', {})
                for (r, c), val in cache.items():
                    val_str = str(val).strip()
                    if val_str and val_str not in ('0', '0.0'):
                        has_nonzero = True
                    items.append((f"{name}[{r+1},{c+1}]", val))
            
            if not has_nonzero and not expr:
                state = "empty"
                
            invalid = first_invalid_cell(items)
            
            res = getattr(self, 'last_result', None)
            if res and not getattr(self.get_ai_context(), 'stale', True):
                st = res.get("status")
                if st == "SUCCESS":
                    state = "ok"
                    if re.search(r'[A-Z)]\s*\*?\s*[A-Z(]', expr):
                        flags.add("has_product")
                elif st == "ERROR":
                    msg = res.get("message", "").lower()
                    if "dimensi" in msg or "tamaño" in msg:
                        state = "dim_error"
                    else:
                        state = "error"
                        
            return Signals(tool="matrices", state=state, flags=frozenset(flags), invalid=invalid)
        except Exception:
            return None
