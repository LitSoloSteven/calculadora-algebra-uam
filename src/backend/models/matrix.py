from fractions import Fraction
from typing import Union

Numeric = Union[float, Fraction, int]

class Matrix:    
    def __init__(self, rows: int, cols: int, data: list[list[Numeric]] | None = None):
        self.rows = rows
        self.cols = cols
        if data is not None:
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
            if abs(float(frac) - float(value)) < 1e-9:
                return frac
        except (ValueError, OverflowError):
            pass
        return float(value)

    def get(self, row: int, col: int) -> Numeric:
        return self.data[row][col]

    def set(self, row: int, col: int, value: Numeric) -> None:
        self.data[row][col] = self._normalize_val(value)

    def clone(self) -> 'Matrix':
        new_data = [row[:] for row in self.data]
        return Matrix(self.rows, self.cols, new_data)

    def swap_rows(self, r1: int, r2: int) -> None:
        if r1 != r2:
            self.data[r1], self.data[r2] = self.data[r2], self.data[r1]

    def add_scaled_row(self, target_r: int, source_r: int, scalar: Numeric) -> None:
        s_norm = self._normalize_val(scalar)
        for c in range(self.cols):
            curr = self.data[target_r][c]
            src = self.data[source_r][c]
            self.data[target_r][c] = self._normalize_val(curr + s_norm * src)

    def __str__(self) -> str:
        from src.backend.utils.formatters import format_fraction_str
        res = []
        for row in self.data:
            formatted_row = [f"{format_fraction_str(val):>8}" for val in row]
            res.append("[ " + " ".join(formatted_row) + " ]")
        return "\n".join(res)