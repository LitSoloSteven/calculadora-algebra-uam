"""Construcción de controles accesibles del reproductor de pasos."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nicegui import ui

from src.frontend.components.reproductor_pasos.catalogo import VELOCIDADES_AUTOREPRODUCCION

if TYPE_CHECKING:
    from src.frontend.components.reproductor_pasos.reproductor import ReproductorPasos


def construir_controles(reproductor: ReproductorPasos) -> None:
    """Dibuja los botones, la velocidad y el slider si existen varios pasos."""
    if len(reproductor.pasos) <= 1:
        return
    with ui.row().classes('w-full items-center justify-between gap-4 mt-2 flex-wrap'):
        with ui.row().classes('items-center gap-1'):
            _boton_primero(reproductor)
            _boton_anterior(reproductor)
            _boton_reproducir(reproductor)
            _boton_siguiente(reproductor)
            _boton_ultimo(reproductor)
            ui.select(
                list(VELOCIDADES_AUTOREPRODUCCION.keys()),
                value='Normal',
                on_change=reproductor._cambiar_velocidad,
            ).classes('neo-select w-28 text-xs').props(
                'dense popup-content-class="neo-select-menu" aria-label="Velocidad de reproducción"'
            )
        reproductor.slider = ui.slider(
            min=0,
            max=len(reproductor.pasos) - 1,
            step=1,
            value=0,
            on_change=reproductor._cambiar_slider,
        ).classes('inv-slider flex-1 min-w-[160px]').props('label aria-label="Paso actual"')


def _boton_primero(reproductor: ReproductorPasos):
    """Crea el control que navega al primer paso."""
    ui.button(icon='first_page', color=None, on_click=lambda: reproductor.ir_a(0)).classes(
        'btn-neo-icon w-9 h-9 p-0'
    ).props('ripple=false aria-label="Primer paso"').tooltip('Primer paso')


def _boton_anterior(reproductor: ReproductorPasos):
    """Crea el control que navega al paso anterior."""
    ui.button(icon='chevron_left', color=None, on_click=lambda: reproductor.ir_a(reproductor.indice_actual - 1)).classes(
        'btn-neo-icon w-9 h-9 p-0'
    ).props('ripple=false aria-label="Paso anterior"').tooltip('Paso anterior')


def _boton_reproducir(reproductor: ReproductorPasos):
    """Crea el control que inicia o pausa la reproducción."""
    reproductor.boton_reproducir = ui.button(
        icon='play_arrow', color=None, on_click=reproductor._alternar_reproduccion
    ).classes('btn-neo-icon w-9 h-9 p-0').props(
        'ripple=false aria-label="Reproducción automática"'
    ).tooltip('Reproducción automática')


def _boton_siguiente(reproductor: ReproductorPasos):
    """Crea el control que navega al paso siguiente."""
    ui.button(icon='chevron_right', color=None, on_click=lambda: reproductor.ir_a(reproductor.indice_actual + 1)).classes(
        'btn-neo-icon w-9 h-9 p-0'
    ).props('ripple=false aria-label="Paso siguiente"').tooltip('Paso siguiente')


def _boton_ultimo(reproductor: ReproductorPasos):
    """Crea el control que navega al último paso."""
    ultimo = len(reproductor.pasos) - 1
    ui.button(icon='last_page', color=None, on_click=lambda: reproductor.ir_a(ultimo)).classes(
        'btn-neo-icon w-9 h-9 p-0'
    ).props('ripple=false aria-label="Último paso"').tooltip('Último paso')
