"""Clase base compartida para los solvers vectoriales.

Agrupa los helpers que tanto `VectorOpsSolver` (operaciones binarias:
add/subtract/scalar_multiply) como `LinearCombinationSolver`
(combinación lineal) necesitan::

- Trazabilidad de pasos (`_log_step`).
- Clasificación de shapes (`_is_column_vector`, `_is_row_vector`,
  `_is_vector`, `_vector_dim`).
- Validación de shapes (`_assert_vector`, `_assert_column_vector`).
- Ajuste de orientaciones (`_transpose`, `_harmonize_shapes`).

La clase NO contiene lógica de negocio: no sabe sumar, restar ni
resolver sistemas. Solo provee primitivas sobre las que los solvers
concretos construyen sus operaciones.

Vive separada de `operations.py` para que `linear_combination.py`
pueda heredar sin importar el módulo entero de operaciones binarias
(evitando un import circular en el split de la Fase 1).
"""
from src.backend.exceptions import InvalidVectorError
from src.backend.models.matrix import Matrix
from src.backend.solvers._tracing import StepTraceMixin


class _VectorOpsBase(StepTraceMixin):
    """Helpers compartidos por los solvers de vectores."""

    # ------------------------------------------------------------------
    # Clasificación de shapes
    # ------------------------------------------------------------------

    @staticmethod
    def _is_column_vector(m: Matrix) -> bool:
        return m.cols == 1

    @staticmethod
    def _is_row_vector(m: Matrix) -> bool:
        return m.rows == 1

    @classmethod
    def _is_vector(cls, m: Matrix) -> bool:
        return cls._is_column_vector(m) or cls._is_row_vector(m)

    @classmethod
    def _vector_dim(cls, m: Matrix) -> int:
        """Dimensión (n) del vector. Asume que m es vector."""
        return m.rows if cls._is_column_vector(m) else m.cols

    # ------------------------------------------------------------------
    # Validación de shapes
    # ------------------------------------------------------------------

    @classmethod
    def _assert_vector(cls, m, name: str) -> None:
        if not isinstance(m, Matrix):
            raise InvalidVectorError(
                f"{name}: se esperaba una Matrix, recibido {type(m).__name__}."
            )
        if not cls._is_vector(m):
            raise InvalidVectorError(
                f"{name}: se esperaba un vector (n×1 o 1×n), "
                f"recibido {m.rows}×{m.cols}."
            )

    @classmethod
    def _assert_column_vector(cls, m, name: str) -> None:
        """Exige estrictamente shape n×1.

        A diferencia de suma/resta (que aceptan filas con auto-transposición),
        la combinación lineal es estricta: la semántica algebraica es
        [v_1|...|v_k] · c = b, y tanto b como cada v_i deben ser columnas.
        """
        if not isinstance(m, Matrix):
            raise InvalidVectorError(
                f"{name}: se esperaba una Matrix, recibido {type(m).__name__}."
            )
        if not cls._is_column_vector(m):
            raise InvalidVectorError(
                f"{name}: se esperaba vector columna n×1, "
                f"recibido {m.rows}×{m.cols}."
            )

    # ------------------------------------------------------------------
    # Transformaciones de shape
    # ------------------------------------------------------------------

    @staticmethod
    def _transpose(m: Matrix) -> Matrix:
        new_data = [[m.get(i, j) for i in range(m.rows)] for j in range(m.cols)]
        return Matrix(m.cols, m.rows, new_data)

    def _harmonize_shapes(
        self,
        v1: Matrix,
        v2: Matrix,
        name1: str,
        name2: str,
        strict: bool,
    ) -> tuple[Matrix, Matrix, str | None]:
        """Alinea orientaciones de v1 y v2.

        Retorna (v1_orientado, v2_orientado, msg_ajuste_o_None).
        Lanza InvalidVectorError si las dimensiones no coinciden o si
        strict=True y las orientaciones difieren.
        """
        if v1.rows == v2.rows and v1.cols == v2.cols:
            return v1, v2, None

        dim1 = self._vector_dim(v1)
        dim2 = self._vector_dim(v2)

        if dim1 != dim2:
            raise InvalidVectorError(
                f"Dimensiones incompatibles: {name1} tiene dim {dim1}, "
                f"{name2} tiene dim {dim2}."
            )

        # Misma dim, distinta orientación (uno n×1, otro 1×n).
        if strict:
            raise InvalidVectorError(
                f"{name2}: se esperaba shape {v1.rows}×{v1.cols} para coincidir "
                f"con {name1}; recibido {v2.rows}×{v2.cols} (strict=True)."
            )

        v2_t = self._transpose(v2)
        orient_orig = "fila" if self._is_row_vector(v2) else "columna"
        msg = (
            f"Ajuste de orientación: {name2} era {orient_orig} "
            f"y se transpone a {v2_t.rows}×{v2_t.cols} para coincidir con {name1}."
        )
        return v1, v2_t, msg

    # Alias canónicos en castellano
    _es_vector_columna = _is_column_vector
    _es_vector_fila = _is_row_vector
    _es_vector = _is_vector
    _dimension_vector = _vector_dim
    _validar_vector = _assert_vector
    _validar_vector_columna = _assert_column_vector
    _transponer = _transpose
    _armonizar_dimensiones = _harmonize_shapes