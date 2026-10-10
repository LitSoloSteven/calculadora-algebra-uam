from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.determinant import DeterminantSolver


def test_determinante_casos_base_2x2():
    mat = Matrix(2, 2, [[1, 2], [3, 4]])
    res_laplace = DeterminantSolver.resolver_laplace(mat)
    res_lu = DeterminantSolver.resolver_lu(mat)

    assert res_laplace["determinante"] == Fraction(-2)
    assert res_lu["determinante"] == Fraction(-2)
    assert res_laplace["es_singular"] is False


def test_determinante_matriz_singular():
    mat = Matrix(3, 3, [[1, 2, 3], [2, 4, 6], [1, 1, 1]])
    res_lu = DeterminantSolver.resolver_lu(mat)
    res_laplace = DeterminantSolver.resolver_laplace(mat)

    assert res_lu["determinante"] == Fraction(0)
    assert res_laplace["determinante"] == Fraction(0)
    assert res_lu["es_singular"] is True


def test_recomendacion_heuristica():
    mat_densa_4x4 = [[1, 2, 3, 4], [5, 6, 7, 8], [2, 1, 0, 3], [4, 3, 2, 1]]
    rec = DeterminantSolver.recomendar_metodo(mat_densa_4x4)
    assert rec["metodo_recomendado"] == "lu"

    mat_con_ceros = [[1, 0, 0], [2, 3, 4], [5, 6, 7]]
    rec2 = DeterminantSolver.recomendar_metodo(mat_con_ceros)
    assert rec2["metodo_recomendado"] == "laplace"