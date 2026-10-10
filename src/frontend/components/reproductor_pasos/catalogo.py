"""Catálogo visual y velocidades disponibles para reproducir pasos."""

import html


CATALOGO_TIPOS = {
    "inicial": {"etiqueta": "Inicio", "icono": "grid_on"},
    "intercambio": {"etiqueta": "Intercambio", "icono": "swap_vert"},
    "pivote": {"etiqueta": "Pivote", "icono": "gps_fixed"},
    "eliminacion": {"etiqueta": "Eliminación", "icono": "exposure"},
    "normalizacion": {"etiqueta": "Normalización", "icono": "looks_one"},
    "otro": {"etiqueta": "Operación", "icono": "tune"},
    "final": {"etiqueta": "Resultado", "icono": "check_circle"},
    "planteamiento": {"etiqueta": "Planteamiento", "icono": "subject"},
    "sustitucion": {"etiqueta": "Sustitución", "icono": "swap_horiz"},
    "verificacion": {"etiqueta": "Verificación", "icono": "fact_check"},
    "operacion": {"etiqueta": "Operación", "icono": "tune"},
    "componente": {"etiqueta": "Componente", "icono": "call_split"},
    "ajuste": {"etiqueta": "Ajuste", "icono": "tune"},
    "expansion": {"etiqueta": "Expansión", "icono": "open_in_full"},
    "division": {"etiqueta": "División", "icono": "functions"},
    "lectura": {"etiqueta": "Lectura", "icono": "visibility"},
    "decodificacion": {"etiqueta": "Decodificación", "icono": "code"},
    "construccion": {"etiqueta": "Construcción", "icono": "build"},
    "resultado": {"etiqueta": "Resultado", "icono": "check_circle"},
}
VELOCIDADES_AUTOREPRODUCCION = {"Lenta": 1.2, "Normal": 0.6, "Rápida": 0.2}
STACKED_FRAC_MAX_N = 6


def html_chip_tipo(tipo: str, etiqueta: str | None = None) -> str:
    """Genera el HTML del chip con etiqueta escapada e icono del catálogo.

    Args:
        tipo: Clave del tipo de paso.
        etiqueta: Texto opcional que sustituye la etiqueta del catálogo.

    Returns:
        HTML del chip con sus clases y el icono correspondiente.
    """
    meta = CATALOGO_TIPOS.get(tipo, CATALOGO_TIPOS["otro"])
    clase = html.escape(tipo, quote=True)
    texto = html.escape(etiqueta if etiqueta is not None else meta["etiqueta"])
    return (
        f'<span class="chip-kind chip-{clase}">'
        f'<span class="material-icons">{meta["icono"]}</span>{texto}</span>'
    )
