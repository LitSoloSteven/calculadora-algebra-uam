"""Tolerancias numéricas centralizadas — nunca usar magic numbers sueltos."""

ZERO_EPSILON = 1e-9
FRACTION_MATCH_TOLERANCE = 1e-6
DISPLAY_DECIMALS = 4
SOLUTION_VERIFICATION_TOLERANCE = 1e-4
DISPLAY_FRACTION_TOLERANCE = 1e-4

# Límite del denominador al reconstruir una fracción desde float/string en backend.
FRACTION_RECONSTRUCTION_LIMIT = 1000

# Límites de visualización (formatters).
FRACTION_DISPLAY_LIMIT = 1000
LATEX_DENOMINATOR_LIMIT = 100

# Matriz inversa: tamaño máximo aceptado (UI y controller) y n máximo para usar MathJax.
INVERSE_MAX_DIMENSION = 50
INVERSE_LATEX_MAX_DIMENSION = 8

# ---------------------------------------------------------------------------
# Protección contra denegación de servicio en parseo numérico.
#
# Rationale: Fraction("1e999999999") materializa 10^999999999 y bloquea el
# hilo consumiendo GBs de RAM. Un string de entrada con >256 caracteres
# puede producir enteros igual de costosos. Ambos se rechazan en O(1) antes
# de tocar Fraction, en los validators del backend.
#
# Regla: PROHIBIDO añadir guardas de tamaño o filtrado en el frontend.
# La protección vive centralizada aquí.
# ---------------------------------------------------------------------------
MAX_NUMBER_STRING_LENGTH = 256

MSG_SCI_NOTATION_NOT_SUPPORTED = (
    "Notación científica no soportada. Escribe el número con decimales o fracción."
)
MSG_NUMBER_TOO_LONG = (
    f"El número excede la longitud máxima permitida ({MAX_NUMBER_STRING_LENGTH} caracteres)."
)