"""Mixin para visualización interactiva del procedimiento de conversión de bases."""

from __future__ import annotations

from typing import Any, Sequence

from nicegui import ui

from src.frontend.components.reproductor_pasos import ReproductorPasos
from src.frontend.components.reproductor_pasos.modelo import PasoReproductor
from ._pasos_bases import construir_pasos_bases


class NumericSystemsProcedureMixin:
    """Gestiona la renderización del procedimiento matemático mediante ReproductorPasos."""

    def _mostrar_procedimiento(self) -> None:
        """Pinta el procedimiento paso a paso de la conversión activa."""
        if not hasattr(self, "resultados_completos") or "pasos" not in self.resultados_completos:
            ui.notify("Realiza una conversión válida primero", type="warning")
            return

        if getattr(self, "reproductor", None) is not None:
            self.reproductor.detener()

        self.pasos_container.clear()
        self.pasos_container.classes(remove="hidden")

        with self.pasos_container:
            ui.label("Procedimiento Matemático").classes("text-2xl font-bold text-main mt-4")

            pasos_raw = self.resultados_completos.get("pasos", [])
            if not pasos_raw:
                ui.label("El número ya se encuentra en el sistema destino seleccionado.").classes(
                    "text-sec italic text-sm mb-2"
                )
                return

            self._montar_reproductor_bases(pasos_raw)

    def _montar_reproductor_bases(self, pasos_raw: list[dict]) -> None:
        """Construye y monta la instancia de ReproductorPasos para las conversiones calculadas."""
        pasos, grupos = construir_pasos_bases(pasos_raw)
        if not pasos:
            return

        accion_glosa = (
            self._crear_accion_glosa_bases(pasos)
            if getattr(self, "ai_panel", None)
            else None
        )

        self.reproductor = ReproductorPasos(
            pasos,
            grupos,
            renderizar_cuerpo=self._renderizar_cuerpo_bases,
            uid="bases",
            titulo="Procedimiento de conversión",
            lineas_ayuda=_LINEAS_AYUDA_BASES,
            tipos_leyenda=("expansion", "division", "resultado", "lectura"),
            al_explicar=accion_glosa,
            esta_ocupado=lambda: bool(
                getattr(getattr(self, "ai_panel", None), "_is_sending", False)
            ),
        )
        self.reproductor.construir()

    def _renderizar_cuerpo_bases(self, paso: PasoReproductor, contenedor: Any) -> None:
        """Ejecuta el cuerpo del paso dentro del contenedor activo."""
        with contenedor:
            if callable(paso.cuerpo):
                paso.cuerpo()
            elif isinstance(paso.cuerpo, str):
                ui.html(paso.cuerpo)

    def _crear_accion_glosa_bases(self, pasos: Sequence[PasoReproductor]):
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


_LINEAS_AYUDA_BASES = (
    "• Expansión posicional: cada dígito se multiplica por la base elevada a su posición.",
    "• Divisiones sucesivas: se divide el número repetidamente entre la base de destino.",
    "• Lectura: los residuos se leen en orden inverso (de abajo hacia arriba) para formar el resultado.",
    "• Puedes navegar paso a paso o utilizar la reproducción automática.",
)
