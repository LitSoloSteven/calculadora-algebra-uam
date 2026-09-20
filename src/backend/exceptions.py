class AlgebraLinealError(ValueError):
    """Excepción base para errores de dominio del backend.

    Hereda de ValueError para retrocompatibilidad: código existente que
    hace 'except ValueError' sigue capturando estos errores.
    """


class DimensionMismatchError(AlgebraLinealError):
    def __init__(self, operation: str, shape_a: tuple[int, int], shape_b: tuple[int, int]):
        self.operation = operation
        self.shape_a = shape_a
        self.shape_b = shape_b
        super().__init__(
            f"Dimensiones incompatibles para {operation}: "
            f"A ({shape_a[0]}×{shape_a[1]}) vs B ({shape_b[0]}×{shape_b[1]})."
        )


class MatrixDataError(AlgebraLinealError):
    """Datos crudos inconsistentes con las dimensiones declaradas
    (filas irregulares, tamaño incorrecto, dimensiones no positivas)."""


class InvalidNumberError(AlgebraLinealError):
    def __init__(self, row: int, col: int, raw_value, reason: str):
        self.row = row
        self.col = col
        self.raw_value = raw_value
        super().__init__(f"Celda [{row+1},{col+1}] inválida ('{raw_value}'): {reason}")


class SingularSystemError(AlgebraLinealError):
    """El sistema no tiene solución única (rango deficiente / matriz singular)."""