"""Reproductor interactivo reutilizable para secuencias didácticas."""

from __future__ import annotations

import html
import itertools
import json
from collections.abc import Callable, Sequence
from typing import Any

from nicegui import ui

from src.frontend.components.reproductor_pasos.catalogo import (
    VELOCIDADES_AUTOREPRODUCCION,
    html_chip_tipo,
)
from src.frontend.components.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from src.frontend.components.reproductor_pasos.vista import construir_vista


_CONTADOR_EXPLICACION = itertools.count()


class ReproductorPasos:
    """Gestiona navegación, renderizado y reproducción automática de pasos."""

    def __init__(
        self,
        pasos: Sequence[PasoReproductor],
        grupos: Sequence[GrupoReproductor],
        *,
        renderizar_cuerpo: Callable[[PasoReproductor, Any], None],
        uid: str,
        titulo: str = "Procedimiento paso a paso",
        lineas_ayuda: Sequence[str] = (),
        tipos_leyenda: Sequence[str] = (),
        al_explicar: Callable[[PasoReproductor], None] | None = None,
        esta_ocupado: Callable[[], bool] = lambda: False,
    ) -> None:
        """Guarda los pasos y callbacks que controlan el reproductor.

        Args: pasos y grupos; callback de cuerpo; uid; textos de título, ayuda y leyenda;
        callback de Glosa y callback de estado ocupado.
        Returns: ``None``; conserva la configuración en esta instancia.
        """
        self.pasos = tuple(pasos)
        self.grupos = tuple(grupos)
        self.renderizar_cuerpo = renderizar_cuerpo
        self.uid = uid
        self.id_tarjeta = f"step-card-{uid}"
        self.titulo = titulo
        self.lineas_ayuda = tuple(lineas_ayuda)
        self.tipos_leyenda = tuple(tipos_leyenda)
        self.al_explicar = al_explicar
        self.esta_ocupado = esta_ocupado
        self.indice_actual = 0
        self.timer = None
        self.slider = None
        self.boton_reproducir = None
        self.grupos_cargados: set[int] = set()
        self.tarjeta = None

    def construir(self) -> None:
        """Dibuja la ayuda, la tarjeta del paso y el índice por fases.

        Returns:
            ``None``; crea la interfaz en el contexto activo de NiceGUI.
        """
        if not self.pasos:
            return
        self.detener()
        self.grupos_cargados.clear()
        construir_vista(self)

    def detener(self) -> None:
        """Detiene y elimina el timer asociado a esta secuencia.

        Returns:
            ``None``; no deja una reproducción activa.
        """
        if self.timer is not None:
            if not self.timer.is_deleted:
                self.timer.active = False
                self.timer.delete()
            self.timer = None
        if self.boton_reproducir is not None and not self.boton_reproducir.is_deleted:
            self.boton_reproducir.props('icon=play_arrow')

    def ir_a(self, indice: int, *, autoreproduccion: bool = False) -> None:
        """Navega a un paso y actualiza sus metadatos, explicación y cuerpo.

        Args:
            indice: Índice objetivo, acotado a la secuencia disponible.
            autoreproduccion: Evita la escritura animada durante autoplay.

        Returns:
            ``None``; actualiza la interfaz activa.
        """
        if not self.pasos or self.tarjeta is None or self.tarjeta.is_deleted:
            return
        self.indice_actual = max(0, min(indice, len(self.pasos) - 1))
        paso = self.pasos[self.indice_actual]
        self._actualizar_encabezado(paso)
        self._actualizar_explicacion(paso, autoreproduccion)
        self._actualizar_glosa(paso)
        self.contenedor_cuerpo.clear()
        self.renderizar_cuerpo(paso, self.contenedor_cuerpo)
        ui.run_javascript(
            f"window.scalarisPasos.destellar({json.dumps(self.id_tarjeta)});"
        )
        if autoreproduccion and self.indice_actual == len(self.pasos) - 1:
            self._pausar_reproduccion()

    def _actualizar_encabezado(self, paso: PasoReproductor) -> None:
        """Actualiza índice, chip, fase y barra de progreso."""
        self.etiqueta_indice.set_text(f"Paso {self.indice_actual + 1} de {len(self.pasos)}")
        self.chip.set_content(html_chip_tipo(paso.tipo, paso.etiqueta_tipo))
        if 0 <= paso.indice_grupo < len(self.grupos):
            self.fase.set_text(self.grupos[paso.indice_grupo].titulo)
        else:
            self.fase.set_text("")
        self.progreso.set_value((self.indice_actual + 1) / len(self.pasos))
        if self.slider is not None and self.slider.value != self.indice_actual:
            self.slider.value = self.indice_actual

    def _actualizar_explicacion(self, paso: PasoReproductor, autoreproduccion: bool) -> None:
        """Muestra la explicación, con escritura animada fuera de autoplay."""
        texto = paso.explicacion
        identificador = f"repro-expl-{next(_CONTADOR_EXPLICACION)}"
        if autoreproduccion:
            contenido = html.escape(texto)
            self.explicacion.set_content(
                f'<span class="text-sec text-sm leading-relaxed">{contenido}</span>'
            )
            return
        self.explicacion.set_content(
            f'<span id="{identificador}" class="text-sec text-sm leading-relaxed"></span>'
        )
        llamada = (
            f"window.scalarisPasos.revelar({json.dumps(identificador)}, "
            f"{json.dumps(texto)});"
        )
        ui.run_javascript(llamada)

    def _actualizar_glosa(self, paso: PasoReproductor) -> None:
        """Renderiza el botón de Glosa si el paso tiene metadatos explicables."""
        self.contenedor_glosa.clear()
        if not self.al_explicar or not paso.meta_explicar:
            return
        from src.frontend.components.glosa_chips import render_explain_button

        with self.contenedor_glosa:
            render_explain_button(
                self.indice_actual + 1,
                len(self.pasos),
                paso.descripcion,
                lambda indice: self.al_explicar(paso),
                is_loading=self.esta_ocupado(),
            )

    def _avanzar(self) -> None:
        """Avanza un paso o cancela el timer si la tarjeta ya fue eliminada."""
        if self.tarjeta is None or self.tarjeta.is_deleted:
            self.detener()
        elif self.indice_actual < len(self.pasos) - 1:
            self.ir_a(self.indice_actual + 1, autoreproduccion=True)
        else:
            self._pausar_reproduccion()

    def _alternar_reproduccion(self) -> None:
        """Inicia o pausa la secuencia y reinicia desde el principio al final."""
        if self.timer is None or self.timer.is_deleted:
            return
        if self.timer.active:
            self._pausar_reproduccion()
            return
        if self.indice_actual == len(self.pasos) - 1:
            self.ir_a(0)
        self.timer.active = True
        self.boton_reproducir.props('icon=pause')

    def _pausar_reproduccion(self) -> None:
        """Pausa el timer conservando su instancia para una próxima reproducción."""
        if self.timer is not None and not self.timer.is_deleted:
            self.timer.active = False
        if self.boton_reproducir is not None and not self.boton_reproducir.is_deleted:
            self.boton_reproducir.props('icon=play_arrow')

    def _cambiar_velocidad(self, evento) -> None:
        """Actualiza el intervalo del timer con la velocidad seleccionada."""
        if self.timer is not None and not self.timer.is_deleted:
            self.timer.interval = VELOCIDADES_AUTOREPRODUCCION.get(
                evento.value, VELOCIDADES_AUTOREPRODUCCION["Normal"]
            )

    def _cambiar_slider(self, evento) -> None:
        """Navega al paso elegido en el slider."""
        self.ir_a(int(evento.value))

    def _seleccionar_desde_indice(self, indice: int) -> None:
        """Navega desde el índice y desplaza el reproductor a la vista."""
        self.ir_a(indice)
        ui.run_javascript(
            "const e=document.getElementById(" + json.dumps(self.id_tarjeta) + ");"
            "if(e)e.scrollIntoView({behavior:window.scalarisMotionOK?.()?'smooth':'auto',block:'center'});"
        )
