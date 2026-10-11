"""Constantes del módulo de inteligencia artificial.

Define límites de contexto, tiempos de espera, políticas de reintento,
códigos transitorios y modelos por defecto para el cliente de IA.
"""

# Límites de serialización de contexto
MAXIMO_CARACTERES_CONTEXTO = 4000
MAXIMO_MATRIZ_COMPLETA = 8
TAMANIO_VENTANA_MATRIZ = 6
LONGITUD_MAXIMA_NUMERO = 14
LONGITUD_MAXIMA_CADENA_USUARIO = 200
LONGITUD_TEXTO_CORTO = 40
LONGITUD_ETIQUETA_FALLBACK = 60
COLUMNAS_MAXIMAS_RECORTE = 12

# Caché de respuestas
TIEMPO_VIDA_CACHE_SEGUNDOS = 3600
CAPACIDAD_MAXIMA_CACHE = 128

# Tiempos límite y red
LIMITE_TIEMPO_TOTAL_SEGUNDOS = 40.0
TIEMPO_MINIMO_RESTANTE_SEGUNDOS = 2.0
TIMEOUT_CONEXION_MAXIMO_SEGUNDOS = 5.0
TIMEOUT_LECTURA_MAXIMO_SEGUNDOS = 25.0
TIEMPO_ESPERA_REINTENTO_SEGUNDOS = 1.0
TIEMPO_RESTANTE_MINIMO_PARA_REINTENTO = 8.0

# Códigos HTTP transitorios que ameritan reintento o fallback
CODIGOS_ESTADO_TRANSITORIOS = {
    429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526
}

# Configuración de modelos OpenRouter
MODELO_PRIMARIO_DEFECTO = "nex-agi/nex-n2.5-pro:free"
URL_OPENROUTER = "https://openrouter.ai/api/v1/chat/completions"
MAXIMO_HISTORIAL_MENSAJES = 6
