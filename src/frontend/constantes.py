"""Constantes numéricas y límites operativos para la interfaz de Scalaris."""

# Límites de dimensión para captura de matrices y sistemas
DIMENSION_MAXIMA_SISTEMAS = 10
DIMENSION_MAXIMA_MATRICES = 10
DIMENSION_MAXIMA_INVERSA = 50

# Temporizadores de anti-rebote (debounce) en segundos
DEBOUNCE_IA_SEGUNDOS = 0.25
DEBOUNCE_VISTA_PREVIA_SEGUNDOS = 0.3
DEBOUNCE_GEOMETRIA_SEGUNDOS = 0.35

# Límite de mensajes retenidos en memoria de sesión para Glosa
MAX_HISTORIAL = 60
MAX_HISTORIAL_GLOSA = 60

# Ventana de anti-rebote para envíos sucesivos a Glosa
ANTI_REBOTE_GLOSA_SEGUNDOS = 1.5

# Parámetros del almacén volátil de transferencias entre herramientas (handoff)
TTL_HANDOFF_SEGUNDOS = 120
MAX_ENTRADAS_HANDOFF = 64
