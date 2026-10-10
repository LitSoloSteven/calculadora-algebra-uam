"""Adaptador entre los resultados de sistemas lineales y el reproductor interactivo."""

from __future__ import annotations

from nicegui import ui

from src.frontend.components.reproductor_pasos import ReproductorPasos
from src.frontend.components.reproductor_pasos.cuerpos import render_latex
from src.frontend.components.reproductor_pasos.modelo import PasoReproductor
from src.frontend.views.linear_systems._pasos_reproductor import construir_pasos_reproductor


class LinearSystemsStepsMixin:
    """Configura el reproductor compartido para los pasos de sistemas lineales."""

    def _render_steps_section(self, result: dict) -> None:
        """Adapta los datos del controller y construye el reproductor interactivo."""
        if getattr(self, "reproductor_pasos", None) is not None:
            self.reproductor_pasos.detener()

        metodo = (
            getattr(self.method_tabs, "value", "gauss")
            if getattr(self, "method_tabs", None)
            else None
        )
        pasos, grupos = construir_pasos_reproductor(result, metodo=metodo)
        if not pasos:
            return

        accion_glosa = (
            self._crear_accion_glosa_sistema(pasos)
            if getattr(self, "ai_panel", None)
            else None
        )

        self.reproductor_pasos = ReproductorPasos(
            pasos,
            grupos,
            renderizar_cuerpo=self._renderizar_cuerpo_sistema,
            uid="sistemas",
            titulo="Procedimiento paso a paso",
            lineas_ayuda=_LINEAS_AYUDA_SISTEMAS,
            tipos_leyenda=(
                "inicial",
                "intercambio",
                "pivote",
                "eliminacion",
                "normalizacion",
                "sustitucion",
                "verificacion",
            ),
            al_explicar=accion_glosa,
            esta_ocupado=lambda: bool(
                getattr(getattr(self, "ai_panel", None), "_is_sending", False)
            ),
        )
        self.reproductor_pasos.construir()

    def _renderizar_cuerpo_sistema(self, paso: PasoReproductor, contenedor) -> None:
        """Pinta la tabla aumentada o el bloque matemático según el tipo de paso."""
        with contenedor:
            if callable(paso.cuerpo):
                paso.cuerpo()
            elif paso.tipo in ("sustitucion", "verificacion"):
                render_latex(str(paso.cuerpo))
            else:
                ui.html(str(paso.cuerpo))

    def _crear_accion_glosa_sistema(self, pasos: tuple[PasoReproductor, ...]):
        """Crea el callback para explicar el paso actual con el panel de Glosa."""
        def explicar(paso: PasoReproductor) -> None:
            meta = paso.meta_explicar or {}
            self.ai_panel.trigger_explain_step({
                "index": paso.indice + 1,
                "total": len(pasos),
                **meta,
            })

        return explicar


_LINEAS_AYUDA_SISTEMAS = (
    "• La tabla es la matriz aumentada [A | b]: los coeficientes a la izquierda y el vector b a la derecha. La línea verde los separa.",
    "• Cada paso aplica una operación elemental de fila a la fila completa de [A | b].",
    "• Colores: fila resaltada = fila modificada · celda con borde = pivote · ámbar = filas intercambiadas.",
    "• Al finalizar la eliminación, se realizan la sustitución y la comprobación del sistema.",
)
