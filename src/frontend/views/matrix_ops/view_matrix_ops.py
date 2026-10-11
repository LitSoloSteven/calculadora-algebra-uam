"""Vista interactiva para evaluación de expresiones matriciales en Scalaris."""

from __future__ import annotations

import logging

from nicegui import ui

from src.frontend.components.ai_panel import AIPanel
from src.frontend.components.app_shell import create_app_shell
from src.frontend.components.matrix_capture import MatrixCapturePanel
from src.frontend.navigation import route_of
from src.frontend.views.matrix_ops.results_mixin import MatrixOpsResultsMixin

logger = logging.getLogger(__name__)


class MatrixOpsUI(MatrixOpsResultsMixin):
    """Controlador de vista modular para el cálculo y paso a paso de matrices."""

    def __init__(self):
        self.capture_panel = MatrixCapturePanel()
        self.contenedor_resultados = None
        self.input_expresion = None
        self.reproductor_pasos = None

    def reset_resultados(self):
        """Limpia los resultados y detiene cualquier reproducción activa."""
        if getattr(self, 'reproductor_pasos', None) is not None:
            self.reproductor_pasos.detener()
            self.reproductor_pasos = None

        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.icon('data_object', size='4rem').classes('text-placeholder mb-4')
            ui.label('Sin resultados').classes('text-xl font-bold text-main')
            ui.label(
                'Añade matrices y escribe una expresión matemática para empezar'
            ).classes('text-sm text-sec mt-2 text-center')

    def _on_matrix_change(self):
        """Notifica al panel de Glosa cuando cambian los datos de las matrices."""
        p = getattr(self, 'ai_panel', None)
        if p and hasattr(p, 'schedule_context_refresh'):
            p.schedule_context_refresh()

    def build(self):
        """Construye los paneles de captura, expresión y resultados."""
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
                            ui.notify(
                                f"La matriz {name} debe ser cuadrada para invertirla.",
                                type='warning',
                            )
                            return
                        if mat['m'] > 10:
                            ui.notify(
                                f"La herramienta de inversa admite hasta 10x10. La matriz {name} es de {mat['m']}x{mat['n']}.",
                                type='warning',
                            )
                            return

                        data = []
                        for r in range(mat['m']):
                            row = []
                            for c in range(mat['n']):
                                val = str(mat['cache'].get((r, c), '0')).strip()
                                if not val:
                                    val = '0'
                                row.append(val)
                            data.append(row)

                        from src.frontend.components.handoff import handoff_url, put_matrix
                        from src.frontend.navigation import route_of

                        token = put_matrix('matrices', data)
                        ui.navigate.to(handoff_url(route_of('inversa'), token))

                    self.capture_panel.on_invert = do_invert

                    with ui.column().classes('w-full panel-card p-6 mt-4'):
                        ui.label('Expresión Matemática').classes('text-lg font-bold text-main mb-2')
                        self.input_expresion = ui.input(
                            placeholder='Ej. A + B * C'
                        ).classes('matrix-input w-full text-xl py-2').props(
                            'borderless autocomplete="new-password"'
                        )
                        self.input_expresion.on_value_change(
                            lambda _: self._on_matrix_change()
                        )

                        ui.button(
                            'Evaluar',
                            icon='calculate',
                            on_click=lambda e: self.evaluar_expresion(e.sender),
                            color=None,
                        ).classes('btn-primary w-full py-3 mt-4').props('ripple=false')

                # Panel derecho (Resultados)
                with ui.column().classes('layout-pane'):
                    self.contenedor_resultados = ui.column().classes(
                        'w-full panel-card p-6 items-center justify-center min-h-[400px]'
                    ).props('id="resultados-ops"')
                    self.reset_resultados()

        self.ai_panel.build()

    def get_ai_context(self):
        """Proporciona el contexto serializado al asistente Glosa."""
        from src.ai.context import AIContext, describir_matriz, is_stale, sanitize_user_string, window_note_from

        try:
            mats = self.capture_panel.get_matrices_dict()
        except Exception:
            mats = {}

        expr_val = (
            self.input_expresion.value
            if hasattr(self, 'input_expresion') and self.input_expresion
            else ""
        )
        empty = not bool(mats) and not bool(expr_val)
        if empty:
            return AIContext("matrix_ops", "Matrices", "Operaciones", {}, empty=True)

        input_data = {}
        descs = []
        for k, v in mats.items():
            if "data" in v:
                sanitized_data = [
                    [sanitize_user_string(c, 32) for c in r] for r in v["data"]
                ]
                d = describir_matriz(sanitized_data)
                input_data[k] = d
                descs.append(d)

        if expr_val:
            input_data["expresion"] = sanitize_user_string(expr_val, 200)

        ctx = AIContext("matrix_ops", "Matrices", "Matrices y Expresión", input_data)
        ctx.window_note = window_note_from(*descs)

        entrada_actual = {
            "matrices": {
                name: dict(m.get('cache', {}))
                for name, m in self.capture_panel.matrices.items()
            },
            "expresion": (expr_val or "").strip(),
        }
        ctx.stale = is_stale(entrada_actual, getattr(self, '_result_fp', None))

        if getattr(self, 'last_result', None):
            if ctx.stale:
                ctx.result = None
            else:
                res = self.last_result
                ctx.result = {
                    "status": res.get("status", "ERROR"),
                    "message": res.get("message", ""),
                }
                if res.get("final_variable"):
                    ctx.result["final_variable"] = res["final_variable"]

        return ctx

    def get_ai_signals(self):
        """Calcula señales heurísticas para sugerencias proactivas."""
        import re
        from src.frontend.suggestions import Signals, first_invalid_cell

        try:
            state = "none"
            flags = set()

            expr = (
                self.input_expresion.value.strip()
                if hasattr(self, 'input_expresion')
                and self.input_expresion
                and self.input_expresion.value
                else ""
            )

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

            return Signals(
                tool="matrices",
                state=state,
                flags=frozenset(flags),
                invalid=invalid,
            )
        except Exception:
            return None
