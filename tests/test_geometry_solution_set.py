"""Tests for geometry _solution_set module."""
from fractions import Fraction

from src.frontend.controllers.geometry._solution_set import (
    SolutionKind,
    SolutionSet,
    classify,
    from_gauss_result,
    has_solution_param,
)


def test_classify_empty():
    assert classify(None, ()) == SolutionKind.EMPTY


def test_classify_point():
    assert classify((Fraction(1), Fraction(2)), ()) == SolutionKind.POINT


def test_classify_line():
    dirs = ((Fraction(1), Fraction(0)),)
    assert classify((Fraction(0), Fraction(0)), dirs) == SolutionKind.LINE


def test_classify_plane():
    dirs = ((Fraction(1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(1), Fraction(0)))
    assert classify((Fraction(0), Fraction(0), Fraction(0)), dirs) == SolutionKind.PLANE


def test_classify_affine_subspace():
    dirs = tuple((Fraction(i), Fraction(0), Fraction(0)) for i in range(3))
    assert classify((Fraction(0),) * 3, dirs) == SolutionKind.AFFINE_SUBSPACE


def test_from_gauss_unique():
    from src.backend.models.matrix import Matrix
    from src.backend.solvers.linear_systems.gauss import GaussSolver

    # x + y = 3, x - y = 1 => (2, 1)
    data = [[Fraction(1), Fraction(1), Fraction(3)],
            [Fraction(1), Fraction(-1), Fraction(1)]]
    matrix = Matrix(2, 3, data)
    result = GaussSolver(matrix).solve()
    ss = from_gauss_result(result)
    assert ss is not None
    assert ss.kind == SolutionKind.POINT
    assert ss.point == (Fraction(2), Fraction(1))


def test_from_gauss_no_solution():
    from src.backend.models.matrix import Matrix
    from src.backend.solvers.linear_systems.gauss import GaussSolver

    # x + y = 1, x + y = 2 => inconsistent
    data = [[Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(1), Fraction(1), Fraction(2)]]
    matrix = Matrix(2, 3, data)
    result = GaussSolver(matrix).solve()
    ss = from_gauss_result(result)
    assert ss is not None
    assert ss.kind == SolutionKind.EMPTY


def test_from_gauss_infinite_returns_none():
    from src.backend.models.matrix import Matrix
    from src.backend.solvers.linear_systems.gauss import GaussSolver

    # x + y = 1 (single equation, 2 variables)
    data = [[Fraction(1), Fraction(1), Fraction(1)]]
    matrix = Matrix(1, 3, data)
    result = GaussSolver(matrix).solve()
    ss = from_gauss_result(result)
    assert ss is None


def test_has_solution_param_true():
    assert has_solution_param({"solution_param": "something"})


def test_has_solution_param_false():
    assert not has_solution_param({"status": "OK"})


def test_has_solution_param_key_present_does_not_break():
    """Presence of solution_param key doesn't break from_gauss_result."""
    result = {
        "status": "INFINITE_SOLUTIONS",
        "solution_param": "x = 1 + t",
        "solution": ["1 + t"],
        "solution_exact": None,
        "free_cols": [1],
    }
    ss = from_gauss_result(result)
    # Should still return None for INFINITE
    assert ss is None
    assert has_solution_param(result)
