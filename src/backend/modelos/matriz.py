"""Modelo matricial con aritmética exacta basada en Fraction."""

from fractions import Fraction
from typing import Union

from src.backend.constantes import (
    CERO_EPSILON,
    LIMITE_RECONSTRUCCION_FRACCION,
    LONGITUD_MAXIMA_CADENA_NUMERO,
    MSJ_NOTACION_CIENTIFICA_NO_SOPORTADA,
    MSJ_NUMERO_DEMASIADO_LARGO,
)
from src.backend.excepciones import ErrorDatosMatriz

Numerico = Union[float, Fraction, int]
NumericoSimilar = Union[Numerico, str]


class Matriz:
    """Estructura de datos matricial con soporte de operaciones elementales."""

    def __init__(
        self,
        filas: int,
        columnas: int,
        datos: list[list[Numerico]] | None = None,
    ):
        """Inicializa la matriz verificando dimensiones y normalizando datos."""
        if not isinstance(filas, int) or not isinstance(columnas, int):
            raise ErrorDatosMatriz(
                f"Las dimensiones deben ser enteros (filas={filas!r}, columnas={columnas!r})."
            )
        if filas <= 0 or columnas <= 0:
            raise ErrorDatosMatriz(
                f"Las dimensiones deben ser positivas (recibido {filas}×{columnas})."
            )

        self.filas = filas
        self.columnas = columnas

        if datos is not None:
            if len(datos) != filas:
                raise ErrorDatosMatriz(
                    f"Se esperaban {filas} filas; datos trae {len(datos)}."
                )
            for i, fila in enumerate(datos):
                if len(fila) != columnas:
                    raise ErrorDatosMatriz(
                        f"Fila {i + 1} tiene {len(fila)} columnas; se esperaban {columnas}."
                    )
            self.datos = [[self._normalizar_valor(val) for val in fila] for fila in datos]
        else:
            self.datos = [[Fraction(0) for _ in range(columnas)] for _ in range(filas)]

    @staticmethod
    def _normalizar_cadena(valor: str) -> Numerico:
        """Convierte una cadena a fracción aplicando guardas DoS."""
        val_limpio = valor.strip()
        if not val_limpio:
            return Fraction(0)
        if "e" in val_limpio or "E" in val_limpio:
            raise ErrorDatosMatriz(MSJ_NOTACION_CIENTIFICA_NO_SOPORTADA)
        if len(val_limpio) > LONGITUD_MAXIMA_CADENA_NUMERO:
            raise ErrorDatosMatriz(MSJ_NUMERO_DEMASIADO_LARGO)
        try:
            return Fraction(val_limpio)
        except (ValueError, ZeroDivisionError):
            raise ErrorDatosMatriz(f"Valor no parseable como número: '{valor}'.")

    @staticmethod
    def _normalizar_valor(valor: NumericoSimilar) -> Numerico:
        """Normaliza cadenas, flotantes y enteros a fracciones exactas."""
        if isinstance(valor, (Fraction, int)):
            return valor
        if isinstance(valor, str):
            return Matriz._normalizar_cadena(valor)
        if isinstance(valor, float):
            try:
                frac = Fraction(valor).limit_denominator(LIMITE_RECONSTRUCCION_FRACCION)
                if abs(float(frac) - valor) < CERO_EPSILON:
                    return frac
            except (ValueError, OverflowError):
                pass
            return valor
        raise ErrorDatosMatriz(f"Tipo no soportado en celda: {type(valor).__name__}.")

    def _verificar_limites(self, fila: int, columna: int) -> None:
        """Verifica que las coordenadas pertenezcan al rango de la matriz."""
        if not (0 <= fila < self.filas and 0 <= columna < self.columnas):
            raise IndexError(
                f"Índice [{fila},{columna}] fuera de rango para matriz {self.filas}×{self.columnas}."
            )

    def obtener(self, fila: int, columna: int) -> Numerico:
        """Devuelve el valor numérico en la coordenada indicada."""
        self._verificar_limites(fila, columna)
        return self.datos[fila][columna]

    def establecer(self, fila: int, columna: int, valor: Numerico) -> None:
        """Asigna un valor numérico normalizado en la coordenada indicada."""
        self._verificar_limites(fila, columna)
        self.datos[fila][columna] = self._normalizar_valor(valor)

    def clonar(self) -> 'Matriz':
        """Devuelve una copia profunda de la matriz actual."""
        nuevos_datos = [fila[:] for fila in self.datos]
        return Matriz(self.filas, self.columnas, nuevos_datos)

    def intercambiar_filas(self, fila1: int, fila2: int) -> None:
        """Intercambia dos filas dentro de la matriz."""
        self._verificar_limites(fila1, 0)
        self._verificar_limites(fila2, 0)
        if fila1 != fila2:
            self.datos[fila1], self.datos[fila2] = self.datos[fila2], self.datos[fila1]

    def sumar_fila_escalada(
        self,
        fila_destino: int,
        fila_origen: int,
        escalar: Numerico,
    ) -> None:
        """Suma a la fila destino el múltiplo escalar de la fila origen."""
        self._verificar_limites(fila_destino, 0)
        self._verificar_limites(fila_origen, 0)
        escalar_norm = self._normalizar_valor(escalar)
        for c in range(self.columnas):
            actual = self.datos[fila_destino][c]
            origen = self.datos[fila_origen][c]
            self.datos[fila_destino][c] = self._normalizar_valor(
                actual + escalar_norm * origen
            )

    def __eq__(self, otro: object) -> bool:
        """Compara la igualdad numérica exacta de dos matrices."""
        if not isinstance(otro, Matriz):
            return NotImplemented
        if self.filas != otro.filas or self.columnas != otro.columnas:
            return False
        return all(
            abs(float(self.datos[r][c]) - float(otro.datos[r][c])) < CERO_EPSILON
            for r in range(self.filas)
            for c in range(self.columnas)
        )

    def __str__(self) -> str:
        """Genera una representación en texto con números formateados."""
        from src.backend.utilidades.formateadores import formatear_fraccion_str

        filas_str = []
        for fila in self.datos:
            fila_formateada = [f"{formatear_fraccion_str(val):>8}" for val in fila]
            filas_str.append("[ " + " ".join(fila_formateada) + " ]")
        return "\n".join(filas_str)
