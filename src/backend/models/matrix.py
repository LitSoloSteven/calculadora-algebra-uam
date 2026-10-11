from fractions import Fraction
from typing import Union

from src.backend.constants import (
    ZERO_EPSILON,
    FRACTION_RECONSTRUCTION_LIMIT,
    MAX_NUMBER_STRING_LENGTH,
    MSG_SCI_NOTATION_NOT_SUPPORTED,
    MSG_NUMBER_TOO_LONG,
)
from src.backend.exceptions import MatrixDataError

from src.backend.modelos.matriz import Matriz

Numeric = Union[float, Fraction, int]
NumericLike = Union[Numeric, str]


class Matrix(Matriz):
    def __init__(self, rows: int, cols: int, data: list[list[Numeric]] | None = None):
        if not isinstance(rows, int) or not isinstance(cols, int):
            raise MatrixDataError(
                f"Las dimensiones deben ser enteros (recibido rows={rows!r}, cols={cols!r})."
            )
        if rows <= 0 or cols <= 0:
            raise MatrixDataError(
                f"Las dimensiones deben ser positivas (recibido {rows}×{cols})."
            )

        super().__init__(filas=rows, columnas=cols, datos=data)
        self.rows = self.filas
        self.cols = self.columnas
        self.data = self.datos

    @staticmethod
    def _normalizar_valor(valor: NumericLike) -> Numeric:
        """Conserva Fraction/int intactos. Parsea strings como Fraction exacto
        (formato 'a/b' o decimal). Convierte float simple a Fraction.

        Los strings NO pasan por limit_denominator: si el usuario escribió
        '1/1001', se respeta el denominador 1001, no se trunca a 1/1000.

        Rechaza (DoS):
          - Strings con 'e'/'E' → notación científica, prohibida.
          - Strings con longitud > MAX_NUMBER_STRING_LENGTH.

        Ambos chequeos se aplican ANTES de tocar Fraction, en O(1).
        """
        if isinstance(valor, (Fraction, int)):
            return valor

        if isinstance(valor, str):
            val_limpio = valor.strip()
            if not val_limpio:
                return Fraction(0)
            if "e" in val_limpio or "E" in val_limpio:
                raise MatrixDataError(MSG_SCI_NOTATION_NOT_SUPPORTED)
            if len(val_limpio) > MAX_NUMBER_STRING_LENGTH:
                raise MatrixDataError(MSG_NUMBER_TOO_LONG)
            try:
                return Fraction(val_limpio)
            except (ValueError, ZeroDivisionError):
                raise MatrixDataError(f"Valor no parseable como número: '{valor}'.")

        if isinstance(valor, float):
            try:
                frac = Fraction(valor).limit_denominator(FRACTION_RECONSTRUCTION_LIMIT)
                if abs(float(frac) - valor) < ZERO_EPSILON:
                    return frac
            except (ValueError, OverflowError):
                pass
            return valor

        raise MatrixDataError(f"Tipo no soportado en celda: {type(valor).__name__}.")

    _normalize_val = _normalizar_valor

    def _verificar_limites(self, fila: int, columna: int) -> None:
        if not (0 <= fila < self.rows and 0 <= columna < self.cols):
            raise IndexError(
                f"Índice [{fila},{columna}] fuera de rango para una matriz {self.rows}×{self.cols}."
            )

    _check_bounds = _verificar_limites

    @property
    def rows(self) -> int:
        return self.filas

    @rows.setter
    def rows(self, valor: int) -> None:
        self.filas = valor

    @property
    def cols(self) -> int:
        return self.columnas

    @cols.setter
    def cols(self, valor: int) -> None:
        self.columnas = valor

    @property
    def data(self) -> list[list[Numeric]]:
        return self.datos

    @data.setter
    def data(self, valor: list[list[Numeric]]) -> None:
        self.datos = valor

    def obtener(self, fila: int, columna: int) -> Numeric:
        self._verificar_limites(fila, columna)
        return self.data[fila][columna]

    get = obtener

    def establecer(self, fila: int, columna: int, valor: Numeric) -> None:
        self._verificar_limites(fila, columna)
        self.data[fila][columna] = self._normalizar_valor(valor)

    set = establecer

    def clonar(self) -> 'Matrix':
        nuevos_datos = [fila[:] for fila in self.data]
        return Matrix(self.rows, self.cols, nuevos_datos)

    clone = clonar

    def intercambiar_filas(self, f1: int, f2: int) -> None:
        # Usamos _verificar_limites sobre la primera columna para validar ambos índices de fila.
        self._verificar_limites(f1, 0)
        self._verificar_limites(f2, 0)
        if f1 != f2:
            self.data[f1], self.data[f2] = self.data[f2], self.data[f1]

    swap_rows = intercambiar_filas

    def sumar_fila_escalada(self, fila_destino: int, fila_origen: int, escalar: Numeric) -> None:
        self._verificar_limites(fila_destino, 0)
        self._verificar_limites(fila_origen, 0)
        s_norm = self._normalizar_valor(escalar)
        for c in range(self.cols):
            actual = self.data[fila_destino][c]
            origen = self.data[fila_origen][c]
            self.data[fila_destino][c] = self._normalizar_valor(actual + s_norm * origen)

    add_scaled_row = sumar_fila_escalada

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Matrix):
            return NotImplemented
        if self.rows != otro.rows or self.cols != otro.cols:
            return False
        return all(
            abs(float(self.data[r][c]) - float(otro.data[r][c])) < ZERO_EPSILON
            for r in range(self.rows)
            for c in range(self.cols)
        )

    def __str__(self) -> str:
        from src.backend.utils.formatters import format_fraction_str
        res = []
        for fila in self.data:
            fila_formateada = [f"{format_fraction_str(val):>8}" for val in fila]
            res.append("[ " + " ".join(fila_formateada) + " ]")
        return "\n".join(res)