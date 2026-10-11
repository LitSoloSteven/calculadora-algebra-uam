"""Clase base compartida para los resolutores vectoriales."""

from src.backend.excepciones import ErrorVectorInvalido
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.trazado import TrazadorPasos


class BaseResolutorVectores(TrazadorPasos):
    """Utilidades compartidas por los resolutores de vectores en R^n."""

    @staticmethod
    def es_vector_columna(m: Matriz) -> bool:
        """Indica si la matriz es un vector columna (n×1)."""
        return m.columnas == 1

    @staticmethod
    def es_vector_fila(m: Matriz) -> bool:
        """Indica si la matriz es un vector fila (1×n)."""
        return m.filas == 1

    @classmethod
    def es_vector(cls, m: Matriz) -> bool:
        """Indica si la matriz es un vector columna o fila."""
        return cls.es_vector_columna(m) or cls.es_vector_fila(m)

    @classmethod
    def dimension_vector(cls, m: Matriz) -> int:
        """Dimensión n del vector."""
        return m.filas if cls.es_vector_columna(m) else m.columnas

    @classmethod
    def validar_vector(cls, m: object, nombre: str) -> None:
        """Exige que el objeto sea una Matriz con forma de vector."""
        if not isinstance(m, Matriz):
            raise ErrorVectorInvalido(
                f"{nombre}: se esperaba una Matriz, recibido {type(m).__name__}."
            )
        if not cls.es_vector(m):
            raise ErrorVectorInvalido(
                f"{nombre}: se esperaba un vector (n×1 o 1×n), recibido {m.filas}×{m.columnas}."
            )

    @classmethod
    def validar_vector_columna(cls, m: object, nombre: str) -> None:
        """Exige estrictamente que el objeto sea un vector columna n×1."""
        if not isinstance(m, Matriz):
            raise ErrorVectorInvalido(
                f"{nombre}: se esperaba una Matriz, recibido {type(m).__name__}."
            )
        if not cls.es_vector_columna(m):
            raise ErrorVectorInvalido(
                f"{nombre}: se esperaba vector columna n×1, recibido {m.filas}×{m.columnas}."
            )

    @staticmethod
    def transponer(m: Matriz) -> Matriz:
        """Devuelve la matriz transpuesta."""
        nuevos_datos = [
            [m.obtener(i, j) for i in range(m.filas)]
            for j in range(m.columnas)
        ]
        return Matriz(m.columnas, m.filas, nuevos_datos)

    def armonizar_dimensiones(
        self,
        v1: Matriz,
        v2: Matriz,
        nombre1: str,
        nombre2: str,
        estricto: bool,
    ) -> tuple[Matriz, Matriz, str | None]:
        """Alinea las orientaciones de dos vectores para operaciones binarias."""
        if v1.filas == v2.filas and v1.columnas == v2.columnas:
            return v1, v2, None

        dim1 = self.dimension_vector(v1)
        dim2 = self.dimension_vector(v2)
        if dim1 != dim2:
            raise ErrorVectorInvalido(
                f"Dimensiones incompatibles: {nombre1} tiene dim {dim1}, {nombre2} tiene dim {dim2}."
            )

        if estricto:
            raise ErrorVectorInvalido(
                f"{nombre2}: se esperaba forma {v1.filas}×{v1.columnas} para coincidir con {nombre1}; "
                f"recibido {v2.filas}×{v2.columnas} (estricto=True)."
            )

        v2_t = self.transponer(v2)
        orient_orig = "fila" if self.es_vector_fila(v2) else "columna"
        msg = (
            f"Ajuste de orientación: {nombre2} era {orient_orig} "
            f"y se transpone a {v2_t.filas}×{v2_t.columnas} para coincidir con {nombre1}."
        )
        return v1, v2_t, msg
