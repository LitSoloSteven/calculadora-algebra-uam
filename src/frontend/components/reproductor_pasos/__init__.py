"""API pública del reproductor interactivo de pasos."""

from src.frontend.components.reproductor_pasos.catalogo import (
    CATALOGO_TIPOS,
    STACKED_FRAC_MAX_N,
    VELOCIDADES_AUTOREPRODUCCION,
    html_chip_tipo,
)
from src.frontend.components.reproductor_pasos.cuerpos import render_latex
from src.frontend.components.reproductor_pasos.html_tablas import (
    etiqueta_variable_html,
    formatear_decimal,
    formatear_valor,
    html_tabla_aumentada,
    html_tabla_matriz,
)
from src.frontend.components.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from src.frontend.components.reproductor_pasos.reproductor import ReproductorPasos

__all__ = [
    "CATALOGO_TIPOS",
    "GrupoReproductor",
    "PasoReproductor",
    "ReproductorPasos",
    "STACKED_FRAC_MAX_N",
    "VELOCIDADES_AUTOREPRODUCCION",
    "etiqueta_variable_html",
    "formatear_decimal",
    "formatear_valor",
    "html_chip_tipo",
    "html_tabla_aumentada",
    "html_tabla_matriz",
    "render_latex",
]
