"""Mixin para renderizado de resultados y reproductor interactivo de números romanos."""

from __future__ import annotations

import html
from typing import Any, Sequence

from nicegui import ui

from src.frontend.components.reproductor_pasos import ReproductorPasos
from src.frontend.components.reproductor_pasos.modelo import (
    GrupoReproductor,
    PasoReproductor,
)
from .roman_steps import construir_pasos_romanos


class RomanResultMixin:
    """Maneja la presentación del resultado de operaciones romanas y el reproductor de pasos."""

    def _render_hero_result_card(
        self,
        val_a: str,
        val_b: str,
        simbolo_op: str,
        nombre_op: str,
        res_rom: str,
    ) -> None:
        """Pinta la tarjeta destacada con la ecuación romana en display grande."""
        with ui.column().classes("w-full panel-card p-6 rounded-2xl gap-4"):
            with ui.row().classes("w-full justify-between items-center"):
                with ui.row().classes("items-center gap-2"):
                    ui.label("RESULTADO DE LA OPERACIÓN").classes("text-xs font-bold tracking-widest text-sec")
                    ui.label(nombre_op.upper()).classes(
                        "text-[10px] font-extrabold px-2.5 py-0.5 rounded border"
                    ).style(
                        "background: var(--bg-elevated); box-shadow: var(--elev-inset); color: var(--accent); border-color: var(--border-input);"
                    )
                ui.button(
                    icon="content_copy",
                    on_click=lambda: self.copiar(res_rom),
                    color=None,
                ).classes("btn-neo-icon w-9 h-9 p-0 text-sec").props(
                    'flat round aria-label="Copiar resultado romano"'
                ).tooltip("Copiar resultado romano")

            with ui.row().classes("w-full items-center justify-center gap-4 py-4 flex-wrap text-center"):
                ui.label(val_a).classes("text-3xl md:text-4xl font-extrabold text-sec font-mono")
                ui.label(simbolo_op).classes("text-2xl font-bold text-sec")
                ui.label(val_b).classes("text-3xl md:text-4xl font-extrabold text-sec font-mono")
                ui.label("=").classes("text-2xl font-bold text-sec")
                ui.label(res_rom).classes(
                    "text-4xl md:text-5xl font-black font-mono tracking-wider px-6 py-2.5 rounded-xl border"
                ).style(
                    "background: var(--bg-elevated); box-shadow: var(--elev-inset); color: var(--accent); border-color: var(--border-input);"
                )

    def _render_roman_player(self, res: Any, op: str) -> None:
        """Construye y monta el reproductor interactivo con las fases de la operación."""
        if getattr(self, "reproductor", None) is not None:
            self.reproductor.detener()

        pasos, grupos = construir_pasos_romanos(res, op)
        if not pasos:
            return

        accion_glosa = (
            self._crear_accion_glosa_romanos(pasos)
            if getattr(self, "ai_panel", None)
            else None
        )

        self.reproductor = ReproductorPasos(
            pasos,
            grupos,
            renderizar_cuerpo=self._renderizar_cuerpo_romanos,
            uid="romanos",
            titulo="Procedimiento paso a paso",
            lineas_ayuda=_LINEAS_AYUDA_ROMANOS,
            tipos_leyenda=(
                "decodificacion",
                "operacion",
                "validacion",
                "definicion",
                "iteracion",
                "producto",
                "construccion",
                "resultado",
            ),
            al_explicar=accion_glosa,
            esta_ocupado=lambda: bool(
                getattr(getattr(self, "ai_panel", None), "_is_sending", False)
            ),
        )
        self.reproductor.construir()

    def _renderizar_cuerpo_romanos(self, paso: PasoReproductor, contenedor: Any) -> None:
        """Pinta el cuerpo del paso dentro del contenedor activo."""
        with contenedor:
            if callable(paso.cuerpo):
                paso.cuerpo()
            elif isinstance(paso.cuerpo, str):
                ui.html(paso.cuerpo)

    def _crear_accion_glosa_romanos(self, pasos: Sequence[PasoReproductor]):
        """Crea el callback para explicar el paso actual con el panel de Glosa."""
        def explicar(paso: PasoReproductor) -> None:
            if not getattr(self, "ai_panel", None):
                return
            meta = paso.meta_explicar or {}
            self.ai_panel.trigger_explain_step({
                "index": paso.indice + 1,
                "total": len(pasos),
                **meta,
            })

        return explicar


_LINEAS_AYUDA_ROMANOS = (
    "• Decodificación: convierte los números romanos a su valor decimal equivalente.",
    "• Operación: realiza el cálculo aritmético (en multiplicación mediante sumas sucesivas).",
    "• Construcción canónica: resta vorazmente los símbolos romanos de mayor a menor valor.",
    "• Puedes avanzar paso a paso o utilizar la reproducción automática.",
)
