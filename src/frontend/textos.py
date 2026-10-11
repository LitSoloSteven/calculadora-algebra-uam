"""Catálogo centralizado de textos y mensajes de interfaz de Scalaris."""

# Mensajes de transferencia entre herramientas (handoff)
MSJ_HANDOFF_DATOS_INVALIDOS = (
    "Los datos recibidos no son válidos, así que empezamos con la herramienta vacía."
)
MSJ_HANDOFF_CARGADO_SISTEMA = "Sistema cargado desde {origen}."
MSJ_HANDOFF_CARGADO_MATRIZ = "Cargamos A ({n}×{n}) desde {origen}."
MSJ_HANDOFF_CARGADO_VECTORES = "Vectores cargados desde {origen}."

# Mensajes de control y estado de Glosa
MSJ_ANTI_REBOTE_GLOSA = "Espera un momento antes de enviar otra pregunta."

# Encabezados y títulos comunes
TITULO_PROCEDIMIENTO_PASOS = "Procedimiento paso a paso"

# Avisos de configuración de servidor
MSJ_SECRETO_DEV_INSEGURO = "STORAGE_SECRET ausente. Usando secreto de desarrollo (inseguro)."
MSJ_ERROR_PRODUCCION_SIN_SECRETO = "ERROR CRÍTICO: SCALARIS_ENV es production pero falta STORAGE_SECRET."
