"""Tests para el soporte de múltiples RHS en GaussSolver.

Verifica que:
- num_rhs=1 (default) mantiene el comportamiento previo intacto.
- solve() rechaza num_rhs > 1 (contrato explícito).
- solve_reduction() corre eliminación sin back-substitution y
  devuelve la matriz reducida, rank, pivot_cols y steps.
- Gauss-Jordan sobre [A|I] produce [I|A⁻¹] (casos 2x2 y 3x3 Lay).
- Matriz singular da rank < n (el caller detecta SINGULAR).
"""
from fractions import Fraction

import pytest

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver


def _augmented_ai(A_vals, n):
    """Construye [A | I] a partir de A (lista de listas n×n) y n."""
    rows = []
    for i in range(n):
        row = [Fraction(v) for v in A_vals[i]]
        for j in range(n):
            row.append(Fraction(1) if i == j else Fraction(0))
        rows.append(row)
    return Matrix(n, 2 * n, rows)


# ---------------------------------------------------------------------------
# num_rhs: validación y default
# ---------------------------------------------------------------------------

def test_num_rhs_default_is_one():
    A = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    assert GaussSolver(A).num_rhs == 1


def test_num_rhs_must_be_positive_integer():
    A = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    with pytest.raises(ValueError, match="num_rhs"):
        GaussSolver(A, num_rhs=0)
    with pytest.raises(ValueError, match="num_rhs"):
        GaussSolver(A, num_rhs=-1)
    with pytest.raises(ValueError, match="num_rhs"):
        GaussSolver(A, num_rhs=1.5)


def test_solve_raises_with_num_rhs_greater_than_one():
    A = Matrix(2, 4, [[1, 2, 1, 0], [3, 4, 0, 1]])
    solver = GaussJordanSolver(A, num_rhs=2)
    with pytest.raises(ValueError, match="num_rhs"):
        solver.solve()


# ---------------------------------------------------------------------------
# solve_reduction: caso 2x2 invertible
# ---------------------------------------------------------------------------

def test_solve_reduction_2x2_invertible():
    # A = [[4,6],[3,8]], det=14, A^-1 = 1/14 [[8,-6],[-3,4]]
    M = _augmented_ai([[4, 6], [3, 8]], 2)
    solver = GaussJordanSolver(M, num_rhs=2)
    result = solver.solve_reduction()

    reduced = result["reduced_matrix"]
    assert result["rank"] == 2
    assert result["pivot_cols"] == [0, 1]

    # Bloque izquierdo = I
    for i in range(2):
        for j in range(2):
            expected = Fraction(1) if i == j else Fraction(0)
            assert reduced.get(i, j) == expected

    # Bloque derecho = A^-1
    assert reduced.get(0, 2) == Fraction(4, 7)
    assert reduced.get(0, 3) == Fraction(-3, 7)
    assert reduced.get(1, 2) == Fraction(-3, 14)
    assert reduced.get(1, 3) == Fraction(2, 7)


# ---------------------------------------------------------------------------
# solve_reduction: caso 3x3 Lay (PPT Inversa, pág. 10)
# ---------------------------------------------------------------------------

def test_solve_reduction_3x3_lay_example():
    # A = [[0,1,2],[1,0,3],[4,-3,8]]
    # A^-1 = [[-9/2, 7, -3/2], [-2, 4, -1], [3/2, -2, 1/2]]
    M = _augmented_ai([[0, 1, 2], [1, 0, 3], [4, -3, 8]], 3)
    solver = GaussJordanSolver(M, num_rhs=3)
    result = solver.solve_reduction()

    reduced = result["reduced_matrix"]
    assert result["rank"] == 3

    expected_inv = [
        [Fraction(-9, 2), Fraction(7), Fraction(-3, 2)],
        [Fraction(-2), Fraction(4), Fraction(-1)],
        [Fraction(3, 2), Fraction(-2), Fraction(1, 2)],
    ]
    for i in range(3):
        for j in range(3):
            assert reduced.get(i, 3 + j) == expected_inv[i][j]


# ---------------------------------------------------------------------------
# solve_reduction: matriz singular → rank < n
# ---------------------------------------------------------------------------

def test_solve_reduction_singular_rank_deficient():
    # A = [[1,2],[2,4]], rank 1
    M = _augmented_ai([[1, 2], [2, 4]], 2)
    solver = GaussJordanSolver(M, num_rhs=2)
    result = solver.solve_reduction()

    assert result["rank"] < 2
    reduced = result["reduced_matrix"]
    # El bloque izquierdo no llega a I
    assert reduced.get(0, 0) == Fraction(1)
    assert reduced.get(1, 0) == Fraction(0)
    assert reduced.get(1, 1) == Fraction(0)


# ---------------------------------------------------------------------------
# solve_reduction: estructura de retorno
# ---------------------------------------------------------------------------

def test_solve_reduction_returns_steps_and_metadata():
    M = _augmented_ai([[4, 6], [3, 8]], 2)
    solver = GaussJordanSolver(M, num_rhs=2)
    result = solver.solve_reduction()

    assert "steps" in result
    assert len(result["steps"]) > 0
    assert "inicial" in result["steps"][0]["description"].lower()
    assert "reduced_matrix" in result
    assert "rank" in result
    assert "pivot_cols" in result


# ---------------------------------------------------------------------------
# No regresión del modo single-RHS
# ---------------------------------------------------------------------------

def test_single_rhs_solve_still_works():
    """num_rhs=1 sigue funcionando exactamente igual que antes."""
    A = Matrix(3, 4, [
        [2, 1, -1, 8],
        [-3, -1, 2, -11],
        [-2, 1, 2, -3],
    ])
    result = GaussSolver(A).solve()
    assert result["status"] == "UNIQUE_SOLUTION"
    assert result["solution_exact"] == [Fraction(2), Fraction(3), Fraction(-1)]


def test_solve_reduction_preserves_large_denominator():
    M = _augmented_ai([[1001, 0], [0, 1001]], 2)
    solver = GaussJordanSolver(M, num_rhs=2)
    result = solver.solve_reduction()
    reduced = result["reduced_matrix"]
    assert reduced.get(0, 2) == Fraction(1, 1001)
    assert reduced.get(1, 3) == Fraction(1, 1001)


def test_solve_reduction_does_not_mutate_original_matrix():
    """El solver clona internamente; el Matrix original no se toca."""
    M = _augmented_ai([[4, 6], [3, 8]], 2)
    snapshot = M.clone()
    GaussJordanSolver(M, num_rhs=2).solve_reduction()
    assert M == snapshot