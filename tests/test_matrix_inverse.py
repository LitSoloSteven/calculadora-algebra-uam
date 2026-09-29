"""Tests para MatrixInverseSolver.

Cubre:
- Inversa de 1x1, 2x2, 3x3 (ejemplo Lay del PPT Inversa, pág. 10).
- Identidad → inversa = identidad.
- Singular (filas duplicadas/dependientes, matriz nula) → status SINGULAR.
- No cuadrada → status ERROR.
- Verificaciones: A·A⁻¹ = I, A⁻¹·A = I, (Aᵀ)⁻¹ = (A⁻¹)ᵀ.
- Steps con detail_latex; primer paso describe [A|I] (no [A|b]).
- Preservación de fracciones exactas con denominadores > 1000.
- Contrato JSON completo (todas las keys siempre presentes).
- No mutación del input.
"""
from fractions import Fraction

import pytest

from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.inverse import MatrixInverseSolver


@pytest.fixture
def solver():
    return MatrixInverseSolver()


def _identity(n):
    return Matrix(n, n, [
        [Fraction(1) if i == j else Fraction(0) for j in range(n)]
        for i in range(n)
    ])


# ---------------------------------------------------------------------------
# Casos base
# ---------------------------------------------------------------------------

def test_inverse_1x1(solver):
    A = Matrix(1, 1, [[4]])
    res = solver.solve(A)
    assert res["status"] == "SUCCESS"
    assert res["inverse"].get(0, 0) == Fraction(1, 4)
    assert res["determinant"] == Fraction(4)


def test_inverse_2x2_simple(solver):
    # A = [[4,6],[3,8]], det = 14, A^-1 = [[4/7,-3/7],[-3/14,2/7]]
    A = Matrix(2, 2, [[4, 6], [3, 8]])
    res = solver.solve(A)
    assert res["status"] == "SUCCESS"
    inv = res["inverse"]
    assert inv.get(0, 0) == Fraction(4, 7)
    assert inv.get(0, 1) == Fraction(-3, 7)
    assert inv.get(1, 0) == Fraction(-3, 14)
    assert inv.get(1, 1) == Fraction(2, 7)
    assert res["determinant"] == Fraction(14)


def test_inverse_3x3_lay_ppt_page_10(solver):
    # PPT Inversa de una Matriz, pág. 10
    A = Matrix(3, 3, [[0, 1, 2], [1, 0, 3], [4, -3, 8]])
    res = solver.solve(A)
    assert res["status"] == "SUCCESS"
    inv = res["inverse"]
    expected = [
        [Fraction(-9, 2), Fraction(7), Fraction(-3, 2)],
        [Fraction(-2), Fraction(4), Fraction(-1)],
        [Fraction(3, 2), Fraction(-2), Fraction(1, 2)],
    ]
    for i in range(3):
        for j in range(3):
            assert inv.get(i, j) == expected[i][j], f"Fallo en ({i},{j})"
    assert res["determinant"] == Fraction(-2)


def test_inverse_identity_is_identity(solver):
    res = solver.solve(_identity(3))
    assert res["status"] == "SUCCESS"
    assert res["inverse"] == _identity(3)
    assert res["determinant"] == Fraction(1)


# ---------------------------------------------------------------------------
# Casos de error y singularidad
# ---------------------------------------------------------------------------

def test_inverse_singular_duplicate_rows(solver):
    A = Matrix(2, 2, [[1, 2], [1, 2]])
    res = solver.solve(A)
    assert res["status"] == "SINGULAR"
    assert res["inverse"] is None
    assert res["determinant"] == Fraction(0)
    assert res["verification_step"] is None
    assert res["verification_reverse_step"] is None
    assert res["transpose_property_step"] is None


def test_inverse_singular_dependent_rows_3x3(solver):
    A = Matrix(3, 3, [[1, 2, 3], [2, 4, 6], [7, 8, 9]])
    res = solver.solve(A)
    assert res["status"] == "SINGULAR"
    assert res["inverse"] is None


def test_inverse_zero_matrix_is_singular(solver):
    A = Matrix(2, 2, [[0, 0], [0, 0]])
    res = solver.solve(A)
    assert res["status"] == "SINGULAR"


def test_inverse_non_square_is_error(solver):
    A = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    res = solver.solve(A)
    assert res["status"] == "ERROR"
    assert res["inverse"] is None
    assert "cuadrada" in res["message"].lower()


# ---------------------------------------------------------------------------
# Verificaciones
# ---------------------------------------------------------------------------

def test_verification_step_present_and_correct(solver):
    A = Matrix(2, 2, [[4, 6], [3, 8]])
    res = solver.solve(A)
    assert res["verification_step"] is not None
    assert res["verification_step"]["coincide"] is True


def test_verification_reverse_step_present_and_correct(solver):
    A = Matrix(2, 2, [[4, 6], [3, 8]])
    res = solver.solve(A)
    assert res["verification_reverse_step"] is not None
    assert res["verification_reverse_step"]["coincide"] is True


def test_transpose_property_holds(solver):
    A = Matrix(2, 2, [[4, 6], [3, 8]])
    res = solver.solve(A)
    assert res["transpose_property_step"] is not None
    assert res["transpose_property_step"]["coincide"] is True


def test_transpose_property_holds_3x3(solver):
    A = Matrix(3, 3, [[0, 1, 2], [1, 0, 3], [4, -3, 8]])
    res = solver.solve(A)
    assert res["transpose_property_step"]["coincide"] is True


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def test_steps_have_detail_latex(solver):
    A = Matrix(2, 2, [[4, 6], [3, 8]])
    res = solver.solve(A)
    assert len(res["steps"]) > 0
    for step in res["steps"]:
        assert "description" in step
        assert "matrix" in step
        assert "detail_latex" in step
        assert step["detail_latex"] is not None


def test_first_step_describes_augmented_with_identity(solver):
    A = Matrix(2, 2, [[4, 6], [3, 8]])
    res = solver.solve(A)
    desc = res["steps"][0]["description"]
    # El primer paso del Gauss-Jordan habla de la matriz aumentada.
    # Para inversa debe decir [A|I], no [A|b].
    assert "[A|I]" in desc
    assert "[A|b]" not in desc


def test_augmented_initial_latex_present(solver):
    A = Matrix(2, 2, [[4, 6], [3, 8]])
    res = solver.solve(A)
    latex = res["augmented_initial_latex"]
    assert latex is not None
    assert "array" in latex
    # La barra divisoria debe estar presente (col_spec cc|cc)
    assert "|" in latex


# ---------------------------------------------------------------------------
# Exactitud con fracciones
# ---------------------------------------------------------------------------

def test_inverse_preserves_large_denominator(solver):
    A = Matrix(2, 2, [[Fraction(1, 1001), 0], [0, Fraction(1, 1001)]])
    res = solver.solve(A)
    assert res["status"] == "SUCCESS"
    assert res["inverse"].get(0, 0) == Fraction(1001)
    assert res["inverse"].get(1, 1) == Fraction(1001)


def test_inverse_fractions_exact(solver):
    A = Matrix(2, 2, [
        [Fraction(1, 2), Fraction(1, 3)],
        [Fraction(1, 4), Fraction(1, 5)],
    ])
    res = solver.solve(A)
    assert res["status"] == "SUCCESS"
    inv = res["inverse"]
    # det = 1/60, A^-1 = 60 · [[1/5,-1/3],[-1/4,1/2]] = [[12,-20],[-15,30]]
    assert inv.get(0, 0) == Fraction(12)
    assert inv.get(0, 1) == Fraction(-20)
    assert inv.get(1, 0) == Fraction(-15)
    assert inv.get(1, 1) == Fraction(30)


# ---------------------------------------------------------------------------
# Contrato JSON y no mutación
# ---------------------------------------------------------------------------

_EXPECTED_KEYS = {
    "status", "message", "determinant", "augmented_initial_latex",
    "inverse", "inverse_latex", "steps",
    "verification_step", "verification_reverse_step",
    "transpose_property_step",
}


def test_success_contract_keys(solver):
    res = solver.solve(Matrix(2, 2, [[4, 6], [3, 8]]))
    assert set(res.keys()) == _EXPECTED_KEYS


def test_error_contract_keys(solver):
    res = solver.solve(Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]))
    assert set(res.keys()) == _EXPECTED_KEYS


def test_singular_contract_keys(solver):
    res = solver.solve(Matrix(2, 2, [[1, 2], [1, 2]]))
    assert set(res.keys()) == _EXPECTED_KEYS


def test_inverse_latex_present_on_success(solver):
    res = solver.solve(Matrix(2, 2, [[4, 6], [3, 8]]))
    assert res["inverse_latex"] is not None
    assert "bmatrix" in res["inverse_latex"]


def test_inverse_does_not_mutate_input(solver):
    A = Matrix(2, 2, [[4, 6], [3, 8]])
    snapshot = A.clone()
    solver.solve(A)
    assert A == snapshot