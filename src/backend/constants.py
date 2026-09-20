"""Tolerancias numéricas centralizadas — nunca usar magic numbers sueltos."""

ZERO_EPSILON = 1e-9
FRACTION_MATCH_TOLERANCE = 1e-6
DISPLAY_DECIMALS = 4
SOLUTION_VERIFICATION_TOLERANCE = 1e-4

# Límite del denominador al reconstruir una fracción desde float/string en backend.
FRACTION_RECONSTRUCTION_LIMIT = 1000

# Límites de visualización (formatters).
FRACTION_DISPLAY_LIMIT = 1000
LATEX_DENOMINATOR_LIMIT = 100