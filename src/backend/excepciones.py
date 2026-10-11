"""Excepciones de dominio para el módulo de álgebra lineal."""


class AlgebraLinealError(ValueError):
    """Excepción base para errores matemáticos y de dominio en el backend."""


class ErrorDiscrepanciaDimension(AlgebraLinealError):
    """Indica que las dimensiones de dos matrices o vectores no son compatibles."""

    def __init__(
        self,
        operacion: str = "",
        forma_a: tuple[int, int] = (0, 0),
        forma_b: tuple[int, int] = (0, 0),
        **opciones,
    ):
        """Inicializa el error con la operación y las formas de los operandos."""
        op = opciones.get("operation", operacion)
        fa = opciones.get("shape_a", forma_a)
        fb = opciones.get("shape_b", forma_b)
        self.operacion = op
        self.forma_a = fa
        self.forma_b = fb
        setattr(self, "operation", op)
        setattr(self, "shape_a", fa)
        setattr(self, "shape_b", fb)
        super().__init__(
            f"Dimensiones incompatibles para {op}: "
            f"A ({fa[0]}×{fa[1]}) vs B ({fb[0]}×{fb[1]})."
        )


class ErrorDatosMatriz(AlgebraLinealError):
    """Indica datos inconsistentes con las dimensiones declaradas de la matriz."""


class ErrorNumeroInvalido(AlgebraLinealError):
    """Indica un valor numérico no convertible o fuera de dominio en una celda."""

    def __init__(
        self,
        fila: int = 0,
        columna: int = 0,
        valor_crudo: object = None,
        motivo: str = "",
        **opciones,
    ):
        """Inicializa el error especificando celda, valor recibido y motivo."""
        f = opciones.get("row", fila)
        c = opciones.get("col", columna)
        v = opciones.get("raw_value", valor_crudo)
        m = opciones.get("reason", motivo)
        self.fila = f
        self.columna = c
        self.valor_crudo = v
        self.motivo = m
        setattr(self, "row", f)
        setattr(self, "col", c)
        setattr(self, "raw_value", v)
        setattr(self, "reason", m)
        super().__init__(
            f"Celda [{f + 1},{c + 1}] inválida ('{v}'): {m}"
        )


class ErrorSistemaSingular(AlgebraLinealError):
    """Indica que el sistema lineal carece de solución única por rango deficiente."""


class ErrorVectorInvalido(AlgebraLinealError):
    """Indica que la estructura no representa un vector unidimensional válido."""
