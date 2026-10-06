import pytest
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver
from src.backend.solvers.matrix_ops.inverse import MatrixInverseSolver
from src.frontend.controllers._step_classifier import classify_step


def test_contract_gauss_3x3_with_row_swap():
    # 3x3 aumentada con intercambio de filas forzado (cero en pivote inicial)
    m = Matrix(3, 4, [
        [Fraction(0), Fraction(2), Fraction(1), Fraction(4)],
        [Fraction(3), Fraction(1), Fraction(-1), Fraction(2)],
        [Fraction(1), Fraction(-1), Fraction(2), Fraction(3)]
    ])
    solver = GaussSolver(m)
    res = solver.solve()
    assert res["status"] in ("UNIQUE_SOLUTION", "SUCCESS")
    assert len(solver.steps) > 0
    for s in solver.steps:
        desc = s["description"]
        classified = classify_step(desc)
        assert classified["kind"] != "otro", f"Paso no clasificado en Gauss 3x3 swap: '{desc}'"


def test_contract_gauss_jordan_4x4_dense():
    # 4x4 denso resuelto por Gauss-Jordan
    m = Matrix(4, 5, [
        [Fraction(2), Fraction(1), Fraction(-1), Fraction(1), Fraction(8)],
        [Fraction(-3), Fraction(-1), Fraction(2), Fraction(0), Fraction(-11)],
        [Fraction(-2), Fraction(1), Fraction(2), Fraction(4), Fraction(-3)],
        [Fraction(1), Fraction(2), Fraction(3), Fraction(4), Fraction(10)]
    ])
    solver = GaussJordanSolver(m)
    res = solver.solve()
    assert res["status"] == "UNIQUE_SOLUTION"
    assert len(solver.steps) > 0
    for s in solver.steps:
        desc = s["description"]
        classified = classify_step(desc)
        assert classified["kind"] != "otro", f"Paso no clasificado en GJ 4x4 denso: '{desc}'"


def test_contract_infinite_solutions():
    # Sistema con infinitas soluciones
    m = Matrix(3, 4, [
        [Fraction(1), Fraction(1), Fraction(1), Fraction(3)],
        [Fraction(2), Fraction(2), Fraction(2), Fraction(6)],
        [Fraction(3), Fraction(3), Fraction(3), Fraction(9)]
    ])
    # Probar con GaussSolver
    s_gauss = GaussSolver(m)
    res_g = s_gauss.solve()
    assert res_g["status"] == "INFINITE_SOLUTIONS"
    for s in s_gauss.steps:
        desc = s["description"]
        classified = classify_step(desc)
        assert classified["kind"] != "otro", f"Paso no clasificado en infinitas soluciones Gauss: '{desc}'"

    # Probar con GaussJordanSolver
    m_gj = Matrix(3, 4, [
        [Fraction(1), Fraction(1), Fraction(1), Fraction(3)],
        [Fraction(2), Fraction(2), Fraction(2), Fraction(6)],
        [Fraction(3), Fraction(3), Fraction(3), Fraction(9)]
    ])
    s_gj = GaussJordanSolver(m_gj)
    res_gj = s_gj.solve()
    assert res_gj["status"] == "INFINITE_SOLUTIONS"
    for s in s_gj.steps:
        desc = s["description"]
        classified = classify_step(desc)
        assert classified["kind"] != "otro", f"Paso no clasificado en infinitas soluciones GJ: '{desc}'"


def test_contract_no_solution():
    # Sistema sin solución (inconsistente)
    m = Matrix(3, 4, [
        [Fraction(1), Fraction(1), Fraction(1), Fraction(1)],
        [Fraction(2), Fraction(2), Fraction(2), Fraction(5)],
        [Fraction(1), Fraction(2), Fraction(3), Fraction(4)]
    ])
    s_gauss = GaussSolver(m)
    res_g = s_gauss.solve()
    assert res_g["status"] == "NO_SOLUTION"
    for s in s_gauss.steps:
        desc = s["description"]
        classified = classify_step(desc)
        assert classified["kind"] != "otro", f"Paso no clasificado en sin solución Gauss: '{desc}'"

    m_gj = Matrix(3, 4, [
        [Fraction(1), Fraction(1), Fraction(1), Fraction(1)],
        [Fraction(2), Fraction(2), Fraction(2), Fraction(5)],
        [Fraction(1), Fraction(2), Fraction(3), Fraction(4)]
    ])
    s_gj = GaussJordanSolver(m_gj)
    res_gj = s_gj.solve()
    assert res_gj["status"] == "NO_SOLUTION"
    for s in s_gj.steps:
        desc = s["description"]
        classified = classify_step(desc)
        assert classified["kind"] != "otro", f"Paso no clasificado en sin solución GJ: '{desc}'"


def test_contract_inverse_3x3():
    # Inversa de matriz 3x3 invertible
    m = Matrix(3, 3, [
        [Fraction(1), Fraction(2), Fraction(3)],
        [Fraction(0), Fraction(1), Fraction(4)],
        [Fraction(5), Fraction(6), Fraction(0)]
    ])
    inv_solver = MatrixInverseSolver()
    res = inv_solver.solve(m)
    assert res["status"] == "SUCCESS"
    assert len(res["steps"]) > 0
    for s in res["steps"]:
        desc = s["description"]
        classified = classify_step(desc)
        assert classified["kind"] != "otro", f"Paso no clasificado en Inversa 3x3: '{desc}'"
