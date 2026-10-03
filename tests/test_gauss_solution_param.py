from fractions import Fraction
import pytest

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver


def _solve(data):
    m = len(data)
    n = len(data[0])
    return GaussSolver(Matrix(m, n, data)).solve()


def test_t1_unique_free_cols_empty():
    r = _solve([[1, 0, 2], [0, 1, 3]])
    sp = r["solution_param"]
    assert sp["num_vars"] == 2
    assert sp["free_cols"] == []
    assert sp["param_names"] == []
    assert sp["particular"] == [Fraction(2), Fraction(3)]
    assert sp["directions"] == []
    assert sp["particular"] == r["solution_exact"]


def test_t2_single_free_variable():
    r = _solve([[1, 1, 2]])
    sp = r["solution_param"]
    assert sp["free_cols"] == [1]
    assert sp["param_names"] == ["t"]
    assert sp["particular"] == [Fraction(2), Fraction(0)]
    assert sp["directions"] == [[Fraction(-1), Fraction(1)]]


def test_t3_two_free_variables():
    r = _solve([[1, 1, 1, 1]])
    sp = r["solution_param"]
    assert sp["free_cols"] == [1, 2]
    assert sp["param_names"] == ["t", "s"]
    assert sp["particular"] == [Fraction(1), Fraction(0), Fraction(0)]
    assert sp["directions"] == [
        [Fraction(-1), Fraction(1), Fraction(0)],
        [Fraction(-1), Fraction(0), Fraction(1)],
    ]


def test_t4_fractional_coefficients():
    r = _solve([[2, 3, 1]])
    sp = r["solution_param"]
    assert sp["particular"] == [Fraction(1, 2), Fraction(0)]
    assert sp["directions"] == [[Fraction(-3, 2), Fraction(1)]]


def test_t5_no_solution_returns_none():
    r = _solve([[1, 1, 1], [1, 1, 2]])
    assert r["status"] == "NO_SOLUTION"
    assert r["solution_param"] is None


def test_t6_large_denominator_not_truncated():
    r = _solve([[1001, 1]])
    sp = r["solution_param"]
    assert sp["particular"] == [Fraction(1, 1001)]
    assert sp["directions"] == []


def test_t7_zero_row_keeps_free_column():
    r = _solve([[1, 0, 2], [0, 0, 0]])
    sp = r["solution_param"]
    assert sp["free_cols"] == [1]
    assert sp["particular"] == [Fraction(2), Fraction(0)]
    assert sp["directions"] == [[Fraction(0), Fraction(1)]]


def test_t8_free_column_not_trailing():
    r = _solve([[0, 1, 5], [0, 0, 0]])
    sp = r["solution_param"]
    assert sp["free_cols"] == [0]
    assert sp["particular"] == [Fraction(0), Fraction(5)]
    assert sp["directions"] == [[Fraction(1), Fraction(0)]]


def test_t9_many_params_uses_t_6_naming():
    r = _solve([[1, 1, 1, 1, 1, 1, 1, 1]])
    sp = r["solution_param"]
    assert sp["num_vars"] == 7
    assert sp["free_cols"] == [1, 2, 3, 4, 5, 6]
    assert sp["param_names"] == ["t", "s", "r", "u", "v", "t_6"]


def test_t10_property_ax_equals_b_and_directions_in_kernel():
    """A·particular == b y A·directions[k] == 0, con Fraction exactos."""
    from src.backend.models.matrix import Matrix as M
    data = [[1, 1, 1, 1]]
    r = _solve(data)
    sp = r["solution_param"]
    A = M(1, 3, [[1, 1, 1]])  # solo las columnas de variables
    b = Fraction(1)

    # particular
    lhs = sum(A.get(0, j) * sp["particular"][j] for j in range(3))
    assert lhs == b

    # directions en el kernel
    for d in sp["directions"]:
        assert sum(A.get(0, j) * d[j] for j in range(3)) == 0


def test_t11_gauss_and_gauss_jordan_agree():
    """Gauss y Gauss-Jordan devuelven el mismo solution_param."""
    for data in (
        [[1, 0, 2], [0, 1, 3]],
        [[1, 1, 2]],
        [[1, 1, 1, 1]],
        [[2, 3, 1]],
        [[0, 1, 5], [0, 0, 0]],
    ):
        m, n = len(data), len(data[0])
        r_gauss = GaussSolver(Matrix(m, n, data)).solve()
        r_gj = GaussJordanSolver(Matrix(m, n, data)).solve()
        assert r_gauss["solution_param"] == r_gj["solution_param"], data


def test_invariants_hold_on_random_systems():
    """Barrido defensivo de invariantes sobre varios tamaños."""
    casos = [
        [[1, 2, 3, 4]],
        [[1, 0, 0, 1], [0, 1, 0, 2], [0, 0, 0, 0]],
        [[1, 1, 1, 1, 1, 1, 1, 1]],
    ]
    for data in casos:
        m, n = len(data), len(data[0])
        r = GaussSolver(Matrix(m, n, data)).solve()
        sp = r["solution_param"]
        if sp is None:
            continue
        for k, fc in enumerate(sp["free_cols"]):
            assert sp["directions"][k][fc] == 1
            assert sp["particular"][fc] == 0
            for j, fc_j in enumerate(sp["free_cols"]):
                if j != k:
                    assert sp["directions"][k][fc_j] == 0


def test_existing_keys_still_present():
    """Regresión: solution, solution_exact, free_cols, steps no desaparecen."""
    r = _solve([[1, 0, 2], [0, 1, 3]])
    for key in ("solution", "solution_exact", "free_cols", "solution_param",
                "steps", "back_substitution_steps", "status", "classification",
                "message", "echelon_matrix"):
        assert key in r, f"Falta la clave '{key}'"