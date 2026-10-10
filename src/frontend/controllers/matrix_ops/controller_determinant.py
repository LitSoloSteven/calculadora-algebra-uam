"""
Controlador frontend para el modulo de Determinantes.
"""
from typing import Dict, Any, List
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.determinant import DeterminantSolver


class DeterminantController:
    """Gestiona la recomendacion y calculo de determinantes."""

    @staticmethod
    def obtener_recomendacion(datos_matriz: List[List[Any]]) -> Dict[str, Any]:
        return DeterminantSolver.recomendar_metodo(datos_matriz)

    @staticmethod
    def procesar(datos_matriz: List[List[Any]], metodo: str = "auto") -> Dict[str, Any]:
        n = len(datos_matriz)
        matriz = Matrix(n, n, datos_matriz)
        rec = DeterminantSolver.recomendar_metodo(datos_matriz)

        if metodo == "auto":
            metodo = rec["metodo_recomendado"]

        if metodo == "laplace":
            res = DeterminantSolver.resolver_laplace(matriz)
        else:
            res = DeterminantSolver.resolver_lu(matriz)

        res["recomendacion"] = rec
        return res