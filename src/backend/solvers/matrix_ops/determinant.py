"""
Solver para Determinantes: Laplace (Cofactores) y Triangulacion (LU / Gauss).
Incluye motor de recomendacion segun tamano y estructura.
"""
from fractions import Fraction
from typing import List, Dict, Any
from src.backend.models.matrix import Matrix


class DeterminantSolver:
    """
    Calcula determinantes por cofactores o triangulacion y ofrece recomendaciones heuristicas.
    """

    @classmethod
    def recomendar_metodo(cls, datos: List[List[Any]]) -> Dict[str, Any]:
        n = len(datos)
        if n <= 2:
            return {
                "metodo_recomendado": "laplace",
                "nombre_legible": "Expansion por Cofactores (Directo)",
                "justificacion": f"Para matrices de orden {n}x{n}, la formula directa de cofactores es optima e inmediata."
            }

        max_ceros = 0
        for fila in datos:
            max_ceros = max(max_ceros, sum(1 for x in fila if Fraction(x) == 0))
        for j in range(n):
            col_ceros = sum(1 for i in range(n) if Fraction(datos[i][j]) == 0)
            max_ceros = max(max_ceros, col_ceros)

        if max_ceros >= n - 1:
            return {
                "metodo_recomendado": "laplace",
                "nombre_legible": "Expansion por Cofactores (Laplace)",
                "justificacion": f"Existe una linea con {max_ceros} ceros. Laplace reduce drasticamente el numero de subdeterminantes."
            }

        return {
            "metodo_recomendado": "lu",
            "nombre_legible": "Triangulacion Gaussiana / LU",
            "justificacion": f"Para orden {n}x{n} denso, la triangulacion tiene complejidad polinomica O(n^3) frente a O(n!) de cofactores."
        }

    @classmethod
    def resolver_laplace(cls, matriz: Matrix) -> Dict[str, Any]:
        filas = matriz.filas
        cols = matriz.columnas
        if filas != cols:
            raise ValueError("El determinante requiere una matriz cuadrada.")

        datos = [[matriz.obtener(i, j) for j in range(cols)] for i in range(filas)]

        def _det_recursivo(m_datos: List[List[Fraction]]) -> Fraction:
            orden = len(m_datos)
            if orden == 1:
                return m_datos[0][0]
            if orden == 2:
                return m_datos[0][0] * m_datos[1][1] - m_datos[0][1] * m_datos[1][0]

            mejor_fila = 0
            max_ceros = -1
            for i, f in enumerate(m_datos):
                c = sum(1 for val in f if val == 0)
                if c > max_ceros:
                    max_ceros = c
                    mejor_fila = i

            det_acum = Fraction(0)
            for j in range(orden):
                elem = m_datos[mejor_fila][j]
                if elem == 0:
                    continue
                signo = (-1) ** (mejor_fila + j)
                sub_matriz = [
                    [m_datos[r][c_idx] for c_idx in range(orden) if c_idx != j]
                    for r in range(orden) if r != mejor_fila
                ]
                sub_det = _det_recursivo(sub_matriz)
                det_acum += Fraction(signo) * elem * sub_det

            return det_acum

        det_final = _det_recursivo(datos)
        return {
            "metodo": "laplace",
            "determinante": det_final,
            "es_singular": det_final == 0,
            "pasos": [f"Determinante calculado por cofactores: {det_final}"]
        }

    @classmethod
    def resolver_lu(cls, matriz: Matrix) -> Dict[str, Any]:
        n = matriz.filas
        if n != matriz.columnas:
            raise ValueError("El determinante requiere una matriz cuadrada.")

        copia = [[matriz.obtener(i, j) for j in range(n)] for i in range(n)]
        signo = 1
        pasos = []

        for col in range(n):
            pivote_fila = col
            while pivote_fila < n and copia[pivote_fila][col] == 0:
                pivote_fila += 1

            if pivote_fila == n:
                return {
                    "metodo": "lu",
                    "determinante": Fraction(0),
                    "es_singular": True,
                    "pasos": ["Se encontro un pivote nulo sin posibilidad de intercambio. La matriz es singular (det = 0)."]
                }

            if pivote_fila != col:
                copia[col], copia[pivote_fila] = copia[pivote_fila], copia[col]
                signo *= -1
                pasos.append(f"Intercambio de Fila {col + 1} con Fila {pivote_fila + 1}")

            pivote = copia[col][col]
            for f in range(col + 1, n):
                factor = copia[f][col] / pivote
                if factor != 0:
                    for c_idx in range(col, n):
                        copia[f][c_idx] -= factor * copia[col][c_idx]
                    pasos.append(f"Fila {f + 1} = Fila {f + 1} - ({factor}) * Fila {col + 1}")

        det = Fraction(signo)
        for i in range(n):
            det *= copia[i][i]

        return {
            "metodo": "lu",
            "determinante": det,
            "es_singular": det == 0,
            "pasos": pasos + [f"Producto diagonal * signo = {det}"]
        }