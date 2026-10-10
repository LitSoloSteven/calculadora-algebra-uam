"""Mixin de renderizado de resultados y pasos para Operaciones con Vectores."""

from __future__ import annotations

import html
from nicegui import ui

from ._pasos_reproductor import (
    construir_pasos_combinacion_lineal,
    construir_pasos_vector_basico,
)
from .steps_mixin import VectorOpsStepsMixin


class VectorOpsResultsMixin(VectorOpsStepsMixin):
    """Maneja la visualización de estados vacíos, resultados y procedimientos de vectores."""

    def render_empty_state(self) -> None:
        """Limpia el panel de resultados y detiene cualquier reproductor activo."""
        if getattr(self, "reproductor_pasos", None) is not None:
            self.reproductor_pasos.detener()
        if not self.right_panel:
            return
        self.right_panel.clear()
        with self.right_panel:
            with ui.column().classes("w-full h-full justify-center items-center text-center opacity-50"):
                ui.icon("functions", size="4rem").classes("mb-4")
                ui.label("Ingresa los vectores y presiona Calcular").classes("text-lg")

    def render_result(self, res: dict) -> None:
        """Pinta el resultado de la operación activa coordinando insignias, resúmenes y pasos."""
        if getattr(self, "reproductor_pasos", None) is not None:
            self.reproductor_pasos.detener()
        self.right_panel.clear()

        with self.right_panel:
            status = res.get("status", "ERROR")
            msg = res.get("message", "")

            if status == "ERROR":
                self._render_error_badge(msg)
                if getattr(self, "ai_panel", None):
                    self.ai_panel.render_inline_chips()
                return

            self._render_success_badge(status, msg)
            if getattr(self, "ai_panel", None):
                self.ai_panel.render_inline_chips()

            if self.active_op in ["add_sub", "scalar"]:
                self.render_steps_and_result(res)
            else:
                self.render_linear_combination_result(res)

            self._render_visualizer_button(res)

    def _render_error_badge(self, msg: str) -> None:
        """Pinta la insignia de error."""
        with ui.row().classes("items-center gap-2 px-4 py-2 badge-error mb-6 w-fit"):
            ui.icon("close", size="sm")
            ui.label(msg).classes("font-bold")

    def _render_success_badge(self, status: str, msg: str) -> None:
        """Pinta la insignia informativa según el estado de la operación."""
        if self.active_op == "lin_comb":
            if status == "UNIQUE":
                badge_class, icon = "badge-success", "check"
            elif status == "INFINITE":
                badge_class, icon = "badge-warning", "warning_amber"
            else:
                badge_class, icon = "badge-error", "close"
        else:
            badge_class, icon = "badge-success", "check"

        with ui.row().classes(f"items-center gap-2 px-4 py-2 {badge_class} mb-6 w-fit"):
            ui.icon(icon, size="sm")
            ui.label(msg).classes("font-bold")

    def render_steps_and_result(self, res: dict) -> None:
        """Muestra el vector resultado y monta el reproductor si hay más de un paso."""
        final_latex = res.get("result_vector_latex")
        if not final_latex and "latex_details" in res and res["latex_details"]:
            final_latex = res["latex_details"][-1]

        if final_latex:
            ui.label("Resultado").classes("text-xl font-bold mb-4 text-main")
            with ui.card().classes("panel-card w-full p-6 mb-6 items-center justify-center"):
                ui.html(f'<div class="math-scroll-container math-label p-4 text-lg text-center">$$ {final_latex} $$</div>')

        pasos, grupos = construir_pasos_vector_basico(res)
        if len(pasos) > 1:
            self._render_vector_player(
                pasos,
                grupos,
                uid="vector-basico",
                titulo="Procedimiento paso a paso",
                tipos_leyenda=("inicial", "ajuste", "componente", "resultado"),
            )

    def render_linear_combination_result(self, res: dict) -> None:
        """Muestra los coeficientes o variables libres y monta el reproductor por fases."""
        status = res.get("status")

        if status == "UNIQUE":
            coef_str = ", ".join(res.get("coeficientes_str", []))
            safe_coef = html.escape(coef_str)
            ui.html(f'<div class="math-scroll-container mb-4"><strong>Coeficientes:</strong> <code class="font-mono text-sm">{safe_coef}</code></div>')

        elif status == "INFINITE":
            sol_str = ", ".join(res.get("solucion_parametrica", []))
            safe_sol = html.escape(sol_str)
            params_str = ", ".join(res.get("parametros_libres", []))
            safe_params = html.escape(params_str)
            ui.html(f'<div class="math-scroll-container mb-4"><strong>Solución paramétrica:</strong> <code class="font-mono text-sm">{safe_sol}</code></div>')
            ui.html(f'<div class="math-scroll-container mb-4"><strong>Variables libres:</strong> <code class="font-mono text-sm">{safe_params}</code></div>')

        pasos, grupos = construir_pasos_combinacion_lineal(res)
        if pasos:
            self._render_vector_player(
                pasos,
                grupos,
                uid="vector-lin-comb",
                titulo="Procedimiento paso a paso",
                tipos_leyenda=("planteamiento", "eliminacion", "sustitucion", "verificacion"),
            )

    def _render_visualizer_button(self, res: dict) -> None:
        """Pinta el botón para transferir los vectores al visualizador 2D/3D si aplica."""
        if self.active_op not in ["add_sub", "lin_comb"] or res.get("status") == "ERROR":
            return

        from src.frontend.components.handoff import handoff_url, put_vectors
        from src.frontend.navigation import route_of

        payload_vectors, scene_name = self._preparar_datos_visualizador()
        if not payload_vectors:
            return

        def _go_to_visualizador():
            token = put_vectors("vectores", scene_name, payload_vectors)
            url = handoff_url(route_of("visualizador"), token) + f"&escena={scene_name}"
            ui.navigate.to(url)

        with ui.row().classes("mt-6"):
            ui.button(
                "Ver en el Visualizador", icon="explore", color=None,
                on_click=_go_to_visualizador
            ).classes("btn-ghost").props("ripple=false")

    def _preparar_datos_visualizador(self) -> tuple[list, str]:
        """Extrae las dimensiones y datos de vectores compatibles con el visualizador."""
        try:
            vecs = self.vector_panel.get_vectors_dict()
        except ValueError:
            return [], ""

        if not vecs:
            return [], ""

        if self.active_op == "add_sub":
            v_list = list(vecs.values())
            if len(v_list) == 2:
                v1_data, v2_data = v_list[0]["data"], v_list[1]["data"]
                dim = len(v1_data)
                if dim in (2, 3) and len(v2_data) == dim:
                    return [v1_data, v2_data], "vectores"

        elif self.active_op == "lin_comb":
            if 2 <= len(vecs) <= 5 and "b" in vecs:
                b_data = vecs["b"]["data"]
                dim = len(b_data)
                others = [v["data"] for k, v in vecs.items() if k != "b"]
                if dim in (2, 3) and all(len(o) == dim for o in others):
                    return [b_data] + others, "combinacion"

        return [], ""
