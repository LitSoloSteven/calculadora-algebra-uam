"""Tests para MatrixOpsSolver.determinant.

Determinante vía eliminación a forma triangular superior con pivoteo
parcial + producto de la diagonal × (-1)^(swaps). NO usa cofactores
recursivos (O(n!), inviable para n>10 — ver PPT Determinantes, pág. 15-16).

Cobertura:
- Casos base por tamaño (1x1, 2x2 directo, 3x3, 4x4 con pivoteo).
- Triangulares (producto diagonal directo).
- Singularidad (det = 0).
- Identidad (det = 1).
- Propiedades: swap → cambia signo; det(AB) = det(A)·det(B);
  det(A) = det(Aᵀ).
- Exactitud con Fraction y denominadores grandes.
- Errores: no cuadrada.
- No mutación del input.
"""
from fractions import Fraction

import pytest

from src.backend.exceptions import DimensionMismatchError
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver


@pytest.fixture
def solver():
    return MatrixOpsSolver()


# ---------------------------------------------------------------------------
# Casos base por tamaño
# ---------------------------------------------------------------------------

def test_determinant_1x1(solver):
    A = Matrix(1, 1, [[5]])
    assert solver.determinant(A) == Fraction(5)


def test_determinant_2x2_ad_bc(solver):
    # PPT Determinantes, pág. 3: B = [[4,6],[3,8]], det = 14
    A = Matrix(2, 2, [[4, 6], [3, 8]])
    assert solver.determinant(A) == Fraction(14)


def test_determinant_2x2_negative(solver):
    A = Matrix(2, 2, [[1, 2], [3, 4]])
    assert solver.determinant(A) == Fraction(-2)


def test_determinant_3x3(solver):
    # det([[1,2,3],[0,1,4],[5,6,0]]) = 1
    A = Matrix(3, 3, [[1, 2, 3], [0, 1, 4], [5, 6, 0]])
    assert solver.determinant(A) == Fraction(1)


def test_determinant_3x3_ppt_page_20(solver):
    # PPT Determinantes, pág. 20: det = 15
    A = Matrix(3, 3, [
        [1, -4, 2],
        [-2, 8, -9],
        [-1, 7, 0],
    ])
    assert solver.determinant(A) == Fraction(15)


def test_determinant_4x4_with_pivoting(solver):
    # Requiere swap en la primera columna (A[0,0] = 0).
    # det = 2 (expandiendo por última fila/columna).
    A = Matrix(4, 4, [
        [0, 1, 1, 0],
        [1, 0, 1, 0],
        [1, 1, 0, 0],
        [0, 0, 0, 1],
    ])
    assert solver.determinant(A) == Fraction(2)


# ---------------------------------------------------------------------------
# Casos especiales
# ---------------------------------------------------------------------------

def test_determinant_triangular_superior(solver):
    A = Matrix(3, 3, [[1, 2, 3], [0, 4, 5], [0, 0, 6]])
    assert solver.determinant(A) == Fraction(24)


def test_determinant_triangular_inferior(solver):
    A = Matrix(3, 3, [[1, 0, 0], [2, 3, 0], [4, 5, 6]])
    assert solver.determinant(A) == Fraction(18)


def test_determinant_singular_dependent_rows_is_zero(solver):
    A = Matrix(3, 3, [[1, 2, 3], [2, 4, 6], [7, 8, 9]])
    assert solver.determinant(A) == Fraction(0)


def test_determinant_singular_duplicate_rows_is_zero(solver):
    A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [1, 2, 3]])
    assert solver.determinant(A) == Fraction(0)


def test_determinant_singular_zero_column_is_zero(solver):
    A = Matrix(3, 3, [[1, 0, 3], [4, 0, 6], [7, 0, 9]])
    assert solver.determinant(A) == Fraction(0)


def test_determinant_identity_is_one(solver):
    A = Matrix(4, 4, [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ])
    assert solver.determinant(A) == Fraction(1)


# ---------------------------------------------------------------------------
# Propiedades
# ---------------------------------------------------------------------------

def test_determinant_row_swap_flips_sign(solver):
    A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
    B = A.clone()
    B.swap_rows(0, 1)
    assert solver.determinant(B) == -solver.determinant(A)


def test_determinant_product_property(solver):
    # PPT Determinantes, pág. 27: det(AB) = det(A)·det(B)
    A = Matrix(2, 2, [[6, 1], [3, 2]])
    B = Matrix(2, 2, [[4, 3], [1, 2]])
    det_A = solver.determinant(A)
    det_B = solver.determinant(B)
    AB = solver.multiply(A, B)["result_matrix"]
    assert solver.determinant(AB) == det_A * det_B


def test_determinant_transpose_property(solver):
    # PPT Determinantes, pág. 27: det(Aᵀ) = det(A)
    A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
    AT = solver.transpose(A)
    assert solver.determinant(AT) == solver.determinant(A)


# ---------------------------------------------------------------------------
# Exactitud
# ---------------------------------------------------------------------------

def test_determinant_fractions_exact(solver):
    A = Matrix(2, 2, [
        [Fraction(1, 2), Fraction(1, 3)],
        [Fraction(1, 4), Fraction(1, 5)],
    ])
    # (1/2)(1/5) - (1/3)(1/4) = 1/10 - 1/12 = 1/60
    assert solver.determinant(A) == Fraction(1, 60)


def test_determinant_preserves_large_denominator(solver):
    A = Matrix(2, 2, [
        [Fraction(1, 1001), 0],
        [0, Fraction(1, 1001)],
    ])
    assert solver.determinant(A) == Fraction(1, 1001 * 1001)


def test_determinant_string_inputs_parsed_exact(solver):
    A = Matrix(2, 2, [["1/3", "2"], ["3", "1/4"]])
    # (1/3)(1/4) - 2·3 = 1/12 - 6 = -71/12
    assert solver.determinant(A) == Fraction(-71, 12)


# ---------------------------------------------------------------------------
# Errores y no mutación
# ---------------------------------------------------------------------------

def test_determinant_non_square_raises(solver):
    A = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    with pytest.raises(DimensionMismatchError):
        solver.determinant(A)


def test_determinant_does_not_mutate_input(solver):
    A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
    original = A.clone()
    solver.determinant(A)
    assert A == original