"""Resolutor de determinantes mediante expansion por cofactores (Laplace) y LU."""

from fractions import Fraction
from typing import Any

from src.backend.excepciones import ErrorDiscrepanciaDimension
from src.backend.modelos.matriz import Matriz


class ResolutorDeterminante:
    """Calcula determinantes por cofactores o triangulacion LU con recomendaciones."""

    @classmethod
    def recomendar_metodo(cls, datos: list[list[Any]]) -> dict[str, Any]:
        """Sugiere el metodo optimo (Laplace vs LU) segun tamano y dispersion."""
        n = len(datos)
        if n <= 2:
            return {
                "metodo_recomendado": "laplace",
                "nombre_legible": "Expansion por Cofactores (Directo)",
                "justificacion": f"Para matrices de orden {n}x{n}, la formula directa de cofactores es optima e inmediata.",
            }

        max_ceros = max(sum(1 for x in fila if Fraction(x) == 0) for fila in datos)
        for j in range(n):
            col_ceros = sum(1 for i in range(n) if Fraction(datos[i][j]) == 0)
            max_ceros = max(max_ceros, col_ceros)

        if max_ceros >= n - 1:
            return {
                "metodo_recomendado": "laplace",
                "nombre_legible": "Expansion por Cofactores (Laplace)",
                "justificacion": f"Existe una linea con {max_ceros} ceros. Laplace reduce drasticamente el numero de subdeterminantes.",
            }

        return {
            "metodo_recomendado": "lu",
            "nombre_legible": "Triangulacion Gaussiana / LU",
            "justificacion": f"Para orden {n}x{n} denso, la triangulacion tiene complejidad polinomica O(n^3) frente a O(n!) de cofactores.",
        }

    @staticmethod
    def _seleccionar_mejor_fila_ceros(m_datos: list[list[Fraction]]) -> int:
        """Encuentra la fila con mayor cantidad de ceros para expansion de Laplace."""
        mejor_fila = 0
        max_ceros = -1
        for i, fila in enumerate(m_datos):
            ceros = sum(1 for val in fila if val == 0)
            if ceros > max_ceros:
                max_ceros = ceros
                mejor_fila = i
        return mejor_fila

    @classmethod
    def _det_recursivo(cls, m_datos: list[list[Fraction]]) -> Fraction:
        """Calcula el determinante por cofactores de manera recursiva."""
        orden = len(m_datos)
        if orden == 1:
            return m_datos[0][0]
        if orden == 2:
            return m_datos[0][0] * m_datos[1][1] - m_datos[0][1] * m_datos[1][0]

        mejor_fila = cls._seleccionar_mejor_fila_ceros(m_datos)
        det_acum = Fraction(0)
        for j in range(orden):
            elem = m_datos[mejor_fila][j]
            if elem == 0:
                continue
            signo = (-1) ** (mejor_fila + j)
            sub_matriz = [
                [m_datos[r][c] for c in range(orden) if c != j]
                for r in range(orden) if r != mejor_fila
            ]
            det_acum += Fraction(signo) * elem * cls._det_recursivo(sub_matriz)
        return det_acum

    @classmethod
    def resolver_laplace(cls, matriz: Matriz) -> dict[str, Any]:
        """Calcula el determinante aplicando expansion por cofactores de Laplace."""
        if matriz.filas != matriz.columnas:
            raise ErrorDiscrepanciaDimension(
                "determinante", (matriz.filas, matriz.columnas), (matriz.filas, matriz.filas)
            )

        datos = [[matriz.obtener(i, j) for j in range(matriz.columnas)] for i in range(matriz.filas)]
        det_final = cls._det_recursivo(datos)
        return {
            "metodo": "laplace",
            "determinante": det_final,
            "es_singular": det_final == 0,
            "pasos": [f"Determinante calculado por cofactores: {det_final}"],
        }

    @staticmethod
    def _buscar_pivote_no_nulo(copia: list[list[Fraction]], col: int, n: int) -> int:
        """Encuentra el índice de la primera fila con pivote no nulo."""
        pivote_fila = col
        while pivote_fila < n and copia[pivote_fila][col] == 0:
            pivote_fila += 1
        return pivote_fila

    @staticmethod
    def _restar_multiplo_fila(
        copia: list[list[Fraction]],
        f: int,
        col: int,
        factor: Fraction,
    ) -> None:
        """Resta factor * copia[col] a copia[f] desde la columna col."""
        n = len(copia)
        for c_idx in range(col, n):
            copia[f][c_idx] -= factor * copia[col][c_idx]

    @classmethod
    def _triangular(cls, copia: list[list[Fraction]], n: int) -> tuple[int, list[str], bool]:
        """Reduce la matriz a triangular superior registrando intercambios y operaciones."""
        signo = 1
        pasos = []
        for col in range(n):
            pivote_fila = cls._buscar_pivote_no_nulo(copia, col, n)
            if pivote_fila == n:
                pasos.append(
                    "Se encontro un pivote nulo sin posibilidad de intercambio. La matriz es singular (det = 0)."
                )
                return 0, pasos, True

            if pivote_fila != col:
                copia[col], copia[pivote_fila] = copia[pivote_fila], copia[col]
                signo *= -1
                pasos.append(f"Intercambio de Fila {col + 1} con Fila {pivote_fila + 1}")

            pivote = copia[col][col]
            for f in range(col + 1, n):
                factor = copia[f][col] / pivote
                if factor != 0:
                    cls._restar_multiplo_fila(copia, f, col, factor)
                    pasos.append(f"Fila {f + 1} = Fila {f + 1} - ({factor}) * Fila {col + 1}")
        return signo, pasos, False

    @classmethod
    def resolver_lu(cls, matriz: Matriz) -> dict[str, Any]:
        """Calcula el determinante reduciendo la matriz a forma triangular."""
        n = matriz.filas
        if n != matriz.columnas:
            raise ErrorDiscrepanciaDimension(
                "determinante", (n, matriz.columnas), (n, n)
            )

        copia = [[Fraction(matriz.obtener(i, j)) for j in range(n)] for i in range(n)]
        signo, pasos, es_singular = cls._triangular(copia, n)
        if es_singular:
            return {
                "metodo": "lu",
                "determinante": Fraction(0),
                "es_singular": True,
                "pasos": pasos,
            }

        det = Fraction(signo)
        for i in range(n):
            det *= copia[i][i]

        return {
            "metodo": "lu",
            "determinante": det,
            "es_singular": det == 0,
            "pasos": pasos + [f"Producto diagonal * signo = {det}"],
        }
