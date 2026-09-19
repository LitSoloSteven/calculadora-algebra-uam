from fractions import Fraction
from typing import Union

from src.backend.constants import ZERO_EPSILON
from src.backend.exceptions import MatrixDataError

Numeric = Union[float, Fraction, int]


class Matrix:
    def __init__(self, rows: int, cols: int, data: list[list[Numeric]] | None = None):
        if not isinstance(rows, int) or not isinstance(cols, int):
            raise MatrixDataError(
                f"Las dimensiones deben ser enteros (recibido rows={rows!r}, cols={cols!r})."
            )
        if rows <= 0 or cols <= 0:
            raise MatrixDataError(
                f"Las dimensiones deben ser positivas (recibido {rows}×{cols})."
            )

        self.rows = rows
        self.cols = cols

        if data is not None:
            if len(data) != rows:
                raise MatrixDataError(
                    f"Se esperaban {rows} filas; 'data' trae {len(data)}."
                )
            for i, row in enumerate(data):
                if len(row) != cols:
                    raise MatrixDataError(
                        f"Fila {i + 1} tiene {len(row)} columnas; se esperaban {cols}."
                    )
            self.data = [[self._normalize_val(val) for val in row] for row in data]
        else:
            self.data = [[Fraction(0) for _ in range(cols)] for _ in range(rows)]

    @staticmethod
    def _normalize_val(value: Numeric) -> Numeric:
        """Conserva Fraction e int intactos, o convierte float con precisión equivalente a Fraction."""
        if isinstance(value, (Fraction, int)):
            return value
        try:
            frac = Fraction(value).limit_denominator(1000)
            if abs(float(frac) - float(value)) < ZERO_EPSILON:
                return frac
        except (ValueError, OverflowError):
            pass
        return float(value)

    def _check_bounds(self, row: int, col: int) -> None:
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise IndexError(
                f"Índice [{row},{col}] fuera de rango para una matriz {self.rows}×{self.cols}."
            )

    def get(self, row: int, col: int) -> Numeric:
        self._check_bounds(row, col)
        return self.data[row][col]

    def set(self, row: int, col: int, value: Numeric) -> None:
        self._check_bounds(row, col)
        self.data[row][col] = self._normalize_val(value)

    def clone(self) -> 'Matrix':
        new_data = [row[:] for row in self.data]
        return Matrix(self.rows, self.cols, new_data)

    def swap_rows(self, r1: int, r2: int) -> None:
        # Usamos _check_bounds sobre la primera columna para validar ambos índices de fila.
        self._check_bounds(r1, 0)
        self._check_bounds(r2, 0)
        if r1 != r2:
            self.data[r1], self.data[r2] = self.data[r2], self.data[r1]

    def add_scaled_row(self, target_r: int, source_r: int, scalar: Numeric) -> None:
        self._check_bounds(target_r, 0)
        self._check_bounds(source_r, 0)
        s_norm = self._normalize_val(scalar)
        for c in range(self.cols):
            curr = self.data[target_r][c]
            src = self.data[source_r][c]
            self.data[target_r][c] = self._normalize_val(curr + s_norm * src)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return NotImplemented
        if self.rows != other.rows or self.cols != other.cols:
            return False
        return all(
            abs(float(self.data[r][c]) - float(other.data[r][c])) < ZERO_EPSILON
            for r in range(self.rows)
            for c in range(self.cols)
        )

    def __str__(self) -> str:
        from src.backend.utils.formatters import format_fraction_str
        res = []
        for row in self.data:
            formatted_row = [f"{format_fraction_str(val):>8}" for val in row]
            res.append("[ " + " ".join(formatted_row) + " ]")
        return "\n".join(res)