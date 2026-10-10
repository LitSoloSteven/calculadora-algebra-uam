"""Renderizado y coordinación de la vista previa de sistemas lineales."""

import asyncio
import html
import itertools
import logging

from nicegui import ui

from ._vista_previa import (
    MAX_CELDAS_SISTEMA,
    ResultadoVistaPrevia,
    analizar_ecuaciones,
    latex_matriz_aumentada,
    latex_sistema,
    matriz_desde_celdas,
)

logger = logging.getLogger(__name__)


class LinearSystemsPreviewMixin:
    """Actualiza y dibuja la vista previa de los modos Matriz y Ecuaciones."""

    _contador_ids_preview = itertools.count()

    def _trigger_live_preview(self):
        """Programa una actualización cancelando la tarea anterior."""
        contenedor = getattr(self, "preview_container", None)
        if contenedor is None or contenedor.is_deleted:
            return
        tarea = getattr(self, "preview_task", None)
        if tarea and not tarea.done():
            tarea.cancel()
        self.preview_task = asyncio.create_task(self._update_preview())

    async def _update_preview(self):
        """Espera el debounce y actualiza el modo de vista previa activo."""
        contenedor = getattr(self, "preview_container", None)
        if contenedor is None or contenedor.is_deleted:
            return
        await asyncio.sleep(0.3)
        if contenedor.is_deleted or contenedor is not self.preview_container:
            return
        try:
            contenedor.clear()
            with contenedor:
                if self.mode_tabs.value == "Ecuaciones":
                    self._actualizar_preview_ecuaciones()
                else:
                    self._actualizar_preview_matriz()
        except Exception as error:
            logger.error("Error al actualizar vista previa", exc_info=error)
            if not contenedor.is_deleted:
                with contenedor:
                    self._pintar_mensaje("No se pudo generar la vista previa.")

    def _actualizar_preview_matriz(self):
        """Prepara la matriz aumentada y sus ecuaciones desde las celdas."""
        matriz_a, vector_b = self.grid.get_matrix_data()
        resultado = matriz_desde_celdas(matriz_a, vector_b)
        if resultado.estado == "vacio":
            self._pintar_mensaje("La matriz está vacía.")
            return
        self._pintar_bloques(resultado)

    def _actualizar_preview_ecuaciones(self):
        """Analiza y presenta las ecuaciones escritas por la persona."""
        lineas = [entrada.value or "" for entrada in self.ecuaciones_inputs]
        resultado = analizar_ecuaciones(lineas)
        if resultado.estado == "vacio":
            self._pintar_mensaje("Escribe al menos una ecuación para ver la vista previa.")
            return
        if resultado.estado == "error":
            self._pintar_mensaje(resultado.mensaje, error=True)
            return
        self._pintar_bloques(resultado)

    def _pintar_bloques(self, resultado: ResultadoVistaPrevia):
        """Renderiza bloques matemáticos y el estado de validación."""
        matriz = resultado.matriz
        if matriz is None:
            return
        identificador = next(self._contador_ids_preview)
        id_matriz = f"preview-matrix-{identificador}"
        id_sistema = f"preview-system-{identificador}"
        latex_matriz = html.escape(latex_matriz_aumentada(matriz, len(resultado.variables)))
        ui.html(self._bloque_latex(id_matriz, latex_matriz, "mb-6"))
        if resultado.mensaje:
            self._pintar_mensaje(resultado.mensaje, error=True)
        if len(matriz) * len(resultado.variables) > MAX_CELDAS_SISTEMA:
            self._pintar_mensaje("Sistema demasiado grande para vista previa en ecuaciones.")
        elif resultado.estado == "ok":
            latex_ecuaciones = html.escape(latex_sistema(matriz, resultado.variables))
            ui.html(self._bloque_latex(id_sistema, latex_ecuaciones, ""))
        ui.run_javascript(f"typesetMathWhenReady(['{id_matriz}', '{id_sistema}']);")

    @staticmethod
    def _bloque_latex(identificador: str, contenido: str, margen: str) -> str:
        """Construye un bloque MathJax contenido en su propio scroll."""
        return (
            f'<div id="{identificador}" class="math-scroll-container math-label '
            f'text-lg w-full text-center {margen}">$$ {contenido} $$</div>'
        )

    @staticmethod
    def _pintar_mensaje(mensaje: str, error: bool = False):
        """Muestra una orientación o un error de validación."""
        clase = "badge-error" if error else "text-sec italic text-sm"
        ui.label(mensaje).classes(f"{clase} mt-4 text-center")
