import json
import asyncio
import logging
from nicegui import ui

logger = logging.getLogger(__name__)
from src.frontend.components.navbar import create_navbar
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
            ui.label('Añadí matrices y escribí una expresión matemática para empezar').classes('text-sm text-sec mt-2 text-center')

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

        self.contenedor_resultados.classes(add='animate-slide-up')
        self.contenedor_resultados.clear()

        with self.contenedor_resultados:
            self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
            
            if respuesta.get("status") == "ERROR":
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                    ui.icon('close', size='sm')
                    ui.label(respuesta.get("message", "Error desconocido")).classes('font-bold')
            else:
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-success mb-6 w-fit'):
                    ui.icon('check', size='sm')
                    ui.label(respuesta.get("message", "Éxito")).classes('font-bold')

                if respuesta.get("segment_steps"):
                    ui.label('Evaluación paso a paso:').classes('font-bold text-xl text-main mb-4')
                    for i, step in enumerate(respuesta["segment_steps"]):
                        with ui.column().classes('w-full panel-card p-6 mb-4'):
                            ui.label(step.get("operation_display", f"Paso {i+1}")).classes('text-lg font-bold text-sec mb-2')
                            
                            with ui.row().classes('w-full items-center justify-center gap-4 py-4'):
                                ui.html(f'<div class="math-scroll-container math-label text-xl">$$ {step.get("symbolic_matrix_latex", "")} $$</div>')
                                ui.icon('arrow_forward', size='md').classes('text-sec')
                                ui.html(f'<div class="math-scroll-container math-label text-xl">$$ {step.get("result_matrix_latex", "")} $$</div>')
                            
                            if step.get("cell_by_cell_steps"):
                                with ui.expansion('Ver detalle celda a celda', icon='visibility').classes('w-full mt-2 timeline-expansion').props('header-class="font-medium text-sec"'):
                                    for cell_step in step["cell_by_cell_steps"]:
                                        ui.html(f'<div class="math-scroll-container math-label w-full py-1">$$ {cell_step.get("detail_latex", "")} $$</div>')
                
                if respuesta.get("final_variable") and respuesta.get("result_matrix_latex"):
                    ui.label('Resultado Final:').classes('font-bold text-xl text-main mt-6 mb-4')
                    with ui.row().classes('w-full justify-center items-center panel-card p-6 overflow-x-auto'):
                        ui.html(f'<div class="math-scroll-container math-label text-2xl font-bold">$$ {respuesta["final_variable"]} = {respuesta["result_matrix_latex"]} $$</div>')

        ui.run_javascript('typesetMathWhenReady();')
        ui.run_javascript('setTimeout(() => { const res = document.getElementById("' + str(self.contenedor_resultados.id) + '"); if(res) res.classList.remove("animate-slide-up"); }, MOTION.slow);')
        ui.run_javascript("setTimeout(() => { const el = document.getElementById('resultados-ops'); if(el) el.scrollIntoView({behavior: 'smooth', block: 'start'}) }, MOTION.med);")


    def build(self):
        self.ai_panel = AIPanel(self)
        create_navbar(self, active_route='/operaciones-matrices')
        self.capture_panel.inject_scripts()
        
        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4'):
            with ui.row().classes('w-full justify-between items-center mb-8 gap-4 flex-wrap'):
                ui.label('Operaciones con Matrices').classes('text-2xl font-bold text-main')

            with ui.row().classes('w-full flex-col lg:flex-row items-stretch gap-8 mb-8'):
                # Panel izquierdo (Matrices y expresión)
                with ui.column().classes('w-full lg:w-1/2 lg:flex-1'):
                    self.capture_panel.build_container()
                    
                    with ui.column().classes('w-full panel-card p-6 mt-4'):
                        ui.label('Expresión Matemática').classes('text-lg font-bold text-main mb-2')
                        self.input_expresion = ui.input(placeholder='Ej. A + B * C').classes('matrix-input w-full text-xl py-2').props('borderless autocomplete="new-password"')
                        
                        ui.button('Evaluar', icon='calculate', on_click=lambda e: self.evaluar_expresion(e.sender), color=None).classes('btn-primary w-full py-3 mt-4').props('ripple=false')

                # Panel derecho (Resultados)
                with ui.column().classes('w-full lg:w-1/2 lg:flex-1'):
                    self.contenedor_resultados = ui.column().classes('w-full panel-card p-6 items-center justify-center min-h-[400px]').props('id="resultados-ops"')
                    self.reset_resultados()
                    
        self.ai_panel.build()
