"""Adaptador entre los resultados de vectores y el reproductor interactivo."""

from __future__ import annotations

from typing import Any, Sequence

from nicegui import ui

from src.frontend.components.reproductor_pasos import ReproductorPasos
from src.frontend.components.reproductor_pasos.cuerpos import render_latex
from src.frontend.components.reproductor_pasos.modelo import (
    GrupoReproductor,
    PasoReproductor,
)


class VectorOpsStepsMixin:
    """Configura el reproductor compartido para las operaciones vectoriales."""

    def _render_vector_player(
        self,
        pasos: Sequence[PasoReproductor],
        grupos: Sequence[GrupoReproductor],
        *,
        uid: str,
        titulo: str = "Procedimiento paso a paso",
        lineas_ayuda: Sequence[str] = (),
        tipos_leyenda: Sequence[str] = (),
    ) -> None:
        """Instancia y monta el reproductor interactivo de pasos."""
        if getattr(self, "reproductor_pasos", None) is not None:
            self.reproductor_pasos.detener()

        accion_glosa = (
            self._crear_accion_glosa_vectores(pasos)
            if getattr(self, "ai_panel", None)
            else None
        )

        self.reproductor_pasos = ReproductorPasos(
            pasos,
            grupos,
            renderizar_cuerpo=self._renderizar_cuerpo_vectores,
            uid=uid,
            titulo=titulo,
            lineas_ayuda=lineas_ayuda or _LINEAS_AYUDA_VECTORES,
            tipos_leyenda=tipos_leyenda,
            al_explicar=accion_glosa,
            esta_ocupado=lambda: bool(
                getattr(getattr(self, "ai_panel", None), "_is_sending", False)
            ),
        )
        self.reproductor_pasos.construir()

    def _renderizar_cuerpo_vectores(self, paso: PasoReproductor, contenedor: Any) -> None:
        """Pinta el cuerpo del paso (tabla aumentada HTML, bloque LaTeX o texto)."""
        with contenedor:
            cuerpo = paso.cuerpo
            if callable(cuerpo):
                cuerpo()
            elif isinstance(cuerpo, str):
                if cuerpo.strip().startswith("<"):
                    ui.html(cuerpo)
                else:
                    render_latex(cuerpo)
            else:
                render_latex(str(cuerpo))

    def _crear_accion_glosa_vectores(self, pasos: Sequence[PasoReproductor]):
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


_LINEAS_AYUDA_VECTORES = (
    "• Cada paso evalúa una componente o fase de la operación vectorial.",
    "• En combinación lineal se formula el sistema, se escalona [A | b] y se comprueba y = b.",
    "• Colores: fila resaltada = fila modificada · celda con borde = pivote.",
    "• Puedes usar los controles de navegación o reproducir automáticamente.",
)
