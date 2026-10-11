"""Excepciones de dominio para el módulo de álgebra lineal."""


class AlgebraLinealError(ValueError):
    """Excepción base para errores matemáticos y de dominio en el backend."""


class ErrorDiscrepanciaDimension(AlgebraLinealError):
    """Indica que las dimensiones de dos matrices o vectores no son compatibles."""

    def __init__(
        self,
        operacion: str,
        forma_a: tuple[int, int],
        forma_b: tuple[int, int],
    ):
        """Inicializa el error con la operación y las formas de los operandos."""
        self.operacion = operacion
        self.forma_a = forma_a
        self.forma_b = forma_b
        super().__init__(
            f"Dimensiones incompatibles para {operacion}: "
            f"A ({forma_a[0]}×{forma_a[1]}) vs B ({forma_b[0]}×{forma_b[1]})."
        )


class ErrorDatosMatriz(AlgebraLinealError):
    """Indica datos inconsistentes con las dimensiones declaradas de la matriz."""


class ErrorNumeroInvalido(AlgebraLinealError):
    """Indica un valor numérico no convertible o fuera de dominio en una celda."""

    def __init__(self, fila: int, columna: int, valor_crudo: object, motivo: str):
        """Inicializa el error especificando celda, valor recibido y motivo."""
        self.fila = fila
        self.columna = columna
        self.valor_crudo = valor_crudo
        super().__init__(
            f"Celda [{fila + 1},{columna + 1}] inválida ('{valor_crudo}'): {motivo}"
        )


class ErrorSistemaSingular(AlgebraLinealError):
    """Indica que el sistema lineal carece de solución única por rango deficiente."""


class ErrorVectorInvalido(AlgebraLinealError):
    """Indica que la estructura no representa un vector unidimensional válido."""
