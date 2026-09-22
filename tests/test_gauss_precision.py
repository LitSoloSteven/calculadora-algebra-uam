"""Regresión de precisión en GaussSolver.

Cubre:
- Bug de limit_denominator(1000) redundante en _back_substitute (commit e28a8e9)
- Preservación de variables libres en sistemas indeterminados
"""
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver


def test_back_substitution_preserves_exact_fractions():
    """Regresión: no se debe truncar con limit_denominator(1000)."""
    A = Matrix(2, 3, [[7, 0, 1], [0, 13, 1]])
    res = GaussSolver(A).solve()
    assert res["solution"][0] == "1/7", f"Esperado 1/7, obtenido {res['solution'][0]}"
    assert res["solution"][1] == "1/13", f"Esperado 1/13, obtenido {res['solution'][1]}"


def test_infinite_solutions_preserves_parametrization():
    """Regresión: la reescritura de _back_substitute rompía los sistemas indeterminados."""
    B = Matrix(2, 4, [[1, 1, 1, 3], [2, 2, 2, 6]])
    res = GaussSolver(B).solve()
    assert res["status"] == "INFINITE_SOLUTIONS"
    assert res["solution"] is not None
    # La solución paramétrica debe incluir las variables libres t y s
    assert any("t" in s for s in res["solution"])