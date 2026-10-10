"""Mixin de evaluación y presentación de resultados para Operaciones de Matrices."""

from __future__ import annotations

import asyncio
import json
import logging

from nicegui import ui

from src.frontend.components.reproductor_pasos import ReproductorPasos, render_latex
from src.frontend.components.reproductor_pasos.modelo import PasoReproductor
from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixOpsController
from src.frontend.views.matrix_ops._pasos_reproductor import construir_pasos_matrices

logger = logging.getLogger(__name__)


class MatrixOpsResultsMixin:
    """Gestiona la ejecución y el renderizado interactivo de operaciones matriciales."""

    async def evaluar_expresion(self, btn):
        """Valida la expresión y coordina el botón de carga."""
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
        """Muestra un mensaje accesible ante excepciones imprevistas."""
        logger.error("Error inesperado al evaluar la expresión", exc_info=exc)
        self.contenedor_resultados.clear()
        self.contenedor_resultados.classes(
            remove='items-center justify-center', add='items-start justify-start'
        )
        with self.contenedor_resultados:
            with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                ui.icon('close', size='sm')
                ui.label(
                    'Ocurrió un error inesperado al evaluar la expresión. Revisa los datos e inténtalo de nuevo.'
                ).classes('font-bold')
        ui.notify('Error inesperado', type='negative', position='top')

    def _obtener_matrices_json(self) -> str | None:
        """Extrae el diccionario de matrices del panel de captura como JSON."""
        try:
            matrices_dict = self.capture_panel.get_matrices_dict()
            return json.dumps(matrices_dict)
        except Exception as e:
            ui.notify(str(e), type='negative')
            return None

    async def _evaluar_core(self, btn, expresion):
        """Ejecuta el cálculo en el controller y dibuja la interfaz de resultados."""
        await asyncio.sleep(0.1)

        matrices_json = self._obtener_matrices_json()
        if matrices_json is None:
            return

        respuesta_json_str = MatrixOpsController.process_expression(
            expresion, matrices_json
        )
        respuesta = json.loads(respuesta_json_str)
        self.last_result = respuesta

        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            self.contenedor_resultados.classes(
                remove='items-center justify-center', add='items-start justify-start'
            )
            self._render_estado_y_chips(respuesta)
            self._render_steps_section(respuesta)
            self._render_resultado_final(respuesta)

        ui.run_javascript('typesetMathWhenReady();')
        ui.run_javascript("replayResultAnimation('resultados-ops');")
        ui.run_javascript(
            "setTimeout(() => { const el = document.getElementById('resultados-ops'); "
            "if(el) el.scrollIntoView({behavior: 'smooth', block: 'start'}) }, MOTION.med);"
        )

        self._actualizar_fingerprint_ia(expresion)

    def _actualizar_fingerprint_ia(self, expresion: str):
        """Calcula el fingerprint de entrada y programa la actualización de Glosa."""
        from src.ai.context import fingerprint

        entrada = {
            "matrices": {
                name: dict(m.get('cache', {}))
                for name, m in self.capture_panel.matrices.items()
            },
            "expresion": (expresion or "").strip(),
        }
        self._result_fp = fingerprint(entrada)
        p = getattr(self, 'ai_panel', None)
        if p and hasattr(p, 'schedule_context_refresh'):
            p.schedule_context_refresh()

    def _render_estado_y_chips(self, respuesta: dict):
        """Pinta las insignias de estado y los chips contextuales de Glosa."""
        if respuesta.get("status") == "ERROR":
            with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                ui.icon('close', size='sm')
                ui.label(respuesta.get("message", "Error desconocido")).classes('font-bold')
        else:
            with ui.row().classes('items-center gap-2 px-4 py-2 badge-success mb-6 w-fit'):
                ui.icon('check', size='sm')
                ui.label(respuesta.get("message", "Éxito")).classes('font-bold')

        if getattr(self, 'ai_panel', None):
            self.ai_panel.render_inline_chips()

    def _render_steps_section(self, respuesta: dict):
        """Monta el reproductor interactivo si la expresión produjo suboperaciones."""
        if getattr(self, "reproductor_pasos", None) is not None:
            self.reproductor_pasos.detener()

        pasos, grupos = construir_pasos_matrices(respuesta)
        if not pasos:
            return

        accion_glosa = (
            self._crear_accion_glosa_matrices(pasos)
            if getattr(self, "ai_panel", None)
            else None
        )

        self.reproductor_pasos = ReproductorPasos(
            pasos,
            grupos,
            renderizar_cuerpo=self._renderizar_cuerpo_matrices,
            uid="matrices",
            titulo="Evaluación paso a paso",
            lineas_ayuda=_LINEAS_AYUDA_MATRICES,
            tipos_leyenda=("operacion",),
            al_explicar=accion_glosa,
            esta_ocupado=lambda: bool(
                getattr(getattr(self, "ai_panel", None), "_is_sending", False)
            ),
        )
        self.reproductor_pasos.construir()

    def _renderizar_cuerpo_matrices(self, paso: PasoReproductor, contenedor) -> None:
        """Pinta la operación, la fila simbólica/resultado y el detalle celda a celda."""
        step = paso.cuerpo or {}
        with contenedor:
            op_tex = step.get("operation_display") or f"\\text{{Paso {paso.indice + 1}}}"
            with ui.row().classes('w-full items-center justify-center py-2'):
                render_latex(op_tex)

            sym = step.get("symbolic_matrix_latex")
            res = step.get("result_matrix_latex")
            with ui.row().classes('w-full items-center justify-center gap-4 py-3 flex-wrap'):
                if sym:
                    render_latex(sym)
                if sym and res:
                    ui.icon('arrow_forward', size='md').classes('text-sec')
                if res:
                    render_latex(res)

            cell_steps = step.get("cell_by_cell_steps")
            if cell_steps:
                with ui.expansion('Ver detalle celda a celda', icon='visibility').classes(
                    'w-full mt-2 timeline-expansion'
                ).props('header-class="font-medium text-sec"') as expansion:
                    contenedor_detalle = ui.column().classes('w-full py-1')
                    cargado = False

                    def cargar_detalle(e, cs=cell_steps, cont=contenedor_detalle):
                        nonlocal cargado
                        if e.value and not cargado:
                            cargado = True
                            with cont:
                                for cell_step in cs:
                                    detail = cell_step.get("detail_latex")
                                    if detail:
                                        render_latex(detail)

                    expansion.on_value_change(cargar_detalle)

    def _render_resultado_final(self, respuesta: dict):
        """Muestra el resultado final si la evaluación incluyó más de una suboperación."""
        mostrar_resultado_final = len(respuesta.get("segment_steps", [])) != 1
        if (
            mostrar_resultado_final
            and respuesta.get("final_variable")
            and respuesta.get("result_matrix_latex")
        ):
            ui.label('Resultado Final:').classes('font-bold text-xl text-main mt-6 mb-4')
            with ui.row().classes('w-full justify-center items-center panel-card p-6 overflow-x-auto'):
                ui.html(
                    f'<div class="math-scroll-container math-label text-2xl font-bold">'
                    f'$$ {respuesta["final_variable"]} = {respuesta["result_matrix_latex"]} $$'
                    f'</div>'
                )

    def _crear_accion_glosa_matrices(self, pasos: tuple[PasoReproductor, ...]):
        """Crea el callback para explicar el paso actual con el panel de Glosa."""
        def explicar(paso: PasoReproductor) -> None:
            meta = paso.meta_explicar or {}
            self.ai_panel.trigger_explain_step({
                "index": paso.indice + 1,
                "total": len(pasos),
                **meta,
            })

        return explicar


_LINEAS_AYUDA_MATRICES = (
    "• Cada paso muestra una suboperación de la expresión evaluada.",
    "• La flecha indica la transición de la forma simbólica a la matriz resultante.",
    "• Puedes desplegar el detalle celda a celda para consultar las operaciones aritméticas.",
)
