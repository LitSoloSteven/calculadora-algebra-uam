"""Construcción del encabezado, ayuda y tarjeta del reproductor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nicegui import ui

from src.frontend.components.reproductor_pasos.catalogo import html_chip_tipo
from src.frontend.components.reproductor_pasos.controles import construir_controles
from src.frontend.components.reproductor_pasos.indice import construir_indice

if TYPE_CHECKING:
    from src.frontend.components.reproductor_pasos.reproductor import ReproductorPasos


def construir_vista(reproductor: ReproductorPasos) -> None:
    """Dibuja la ayuda, la tarjeta principal y el índice de pasos."""
    _construir_ayuda(reproductor)
    _construir_tarjeta(reproductor)
    construir_indice(reproductor)
    reproductor.ir_a(0)


def _construir_ayuda(reproductor: ReproductorPasos) -> None:
    """Renderiza el título, la orientación y la leyenda de tipos."""
    ui.label(reproductor.titulo).classes('font-bold mt-6 text-xl text-main')
    if not reproductor.lineas_ayuda and not reproductor.tipos_leyenda:
        return
    with ui.expansion('¿Cómo leer los pasos?', icon='help_outline').classes(
        'w-full panel-card mt-2'
    ).props('default-opened header-class="font-bold text-main"'):
        with ui.column().classes('p-4 gap-2 text-sm'):
            for linea in reproductor.lineas_ayuda:
                ui.label(linea).classes('text-main')
            _construir_leyenda(reproductor)


def _construir_leyenda(reproductor: ReproductorPasos) -> None:
    """Renderiza la leyenda opcional con los tipos configurados."""
    if not reproductor.tipos_leyenda:
        return
    with ui.row().classes('items-center gap-3 flex-wrap mt-3 pt-3 border-t border-[var(--border-input)]'):
        ui.label('Leyenda de operaciones:').classes('font-bold text-sec text-xs mr-2')
        for tipo in reproductor.tipos_leyenda:
            ui.html(html_chip_tipo(tipo))


def _construir_tarjeta(reproductor: ReproductorPasos) -> None:
    """Crea la tarjeta con metadatos, cuerpo y controles del paso actual."""
    with ui.column().classes('w-full panel-card p-4 gap-3 mt-4').props(
        f'id="{reproductor.id_tarjeta}"'
    ) as tarjeta:
        reproductor.tarjeta = tarjeta
        _construir_cabecera(reproductor)
        reproductor.progreso = ui.linear_progress(value=0, show_value=False).classes(
            'inv-progress w-full'
        )
        _construir_descripcion(reproductor)
        _construir_cuerpo(reproductor)
        construir_controles(reproductor)
        if len(reproductor.pasos) > 1:
            from src.frontend.components.reproductor_pasos.catalogo import VELOCIDADES_AUTOREPRODUCCION
            reproductor.timer = ui.timer(
                VELOCIDADES_AUTOREPRODUCCION['Normal'], reproductor._avanzar, active=False
            )


def _construir_cabecera(reproductor: ReproductorPasos) -> None:
    """Crea la fila del índice, el chip y el título de fase."""
    with ui.row().classes('w-full justify-between items-center flex-wrap gap-2'):
        with ui.row().classes('items-center gap-3'):
            reproductor.etiqueta_indice = ui.label('').classes(
                'font-bold text-main text-base font-mono'
            )
            reproductor.chip = ui.html('')
        reproductor.fase = ui.label('').classes('text-sec fs-small font-medium')


def _construir_descripcion(reproductor: ReproductorPasos) -> None:
    """Crea la fila de descripción, explicación y botón de Glosa."""
    with ui.row().classes('w-full justify-between items-start gap-2'):
        with ui.column().classes('flex-1 gap-1'):
            reproductor.descripcion = ui.label('').classes('font-semibold text-main text-sm')
            reproductor.explicacion = ui.html('').classes('w-full')
        reproductor.contenedor_glosa = ui.row()


def _construir_cuerpo(reproductor: ReproductorPasos) -> None:
    """Crea el área desplazable que recibirá el cuerpo de cada paso."""
    with ui.column().classes('w-full items-center my-2'):
        reproductor.contenedor_cuerpo = ui.column().classes('w-full items-center repro-cuerpo')
