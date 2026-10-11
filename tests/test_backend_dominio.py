"""Pruebas de dominio para Gauss e inversión de matrices."""

from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.matrix_ops.inverse import MatrixInverseSolver
from src.backend.utilidades.validadores import ValidadorMatriz


def test_gauss_modulo():
    """Valida la resolución de un sistema compatible determinado por Gauss."""
    datos_crudos = [
        [2.0, 1.0, -1.0, 8.0],
        [-3.0, -1.0, 2.0, -11.0],
        [-2.0, 1.0, 2.0, -3.0],
    ]

    dim_valida, _ = ValidadorMatriz.validar_dimensiones(3, 4)
    datos_validos, _ = ValidadorMatriz.validar_datos_matriz(datos_crudos, 3, 4)
    assert dim_valida and datos_validos

    matriz_aumentada = Matrix(3, 4, datos_crudos)
    resolutor = GaussSolver(matriz_aumentada)
    resultado = resolutor.solve()

    assert resultado["status"] == "UNIQUE_SOLUTION"
    assert len(resultado["steps"]) > 0
    assert resultado["solution"] is not None
    assert resultado["solution"] == ["2", "3", "-1"]


def test_gauss_con_fracciones():
    """Valida la resolución de Gauss a partir de cadenas fraccionarias exactas."""
    datos_con_cadenas = [
        ["2", "1/3", "-1", "8"],
        ["-3/2", "-1", "2", "-11"],
        ["-2", "1", "2/5", "-3"],
    ]

    valido, datos_parseados, _ = ValidadorMatriz.validar_y_parsear_matriz_cruda(
        datos_con_cadenas, 3, 4
    )
    assert valido

    matriz = Matrix(3, 4, datos_parseados)
    resolutor = GaussSolver(matriz)
    resultado = resolutor.solve()

    assert resultado["status"] == "UNIQUE_SOLUTION"
    assert len(resultado["steps"]) > 0


def test_resolutor_matriz_inversa():
    """Valida el cálculo de matriz inversa y sus propiedades matemáticas."""
    resolutor = MatrixInverseSolver()

    mat_2x2 = Matrix(2, 2, [[1, 2], [3, 4]])
    res_2x2 = resolutor.solve(mat_2x2)
    assert res_2x2["status"] == "SUCCESS"
    assert res_2x2["determinant"] == Fraction(-2)
    assert res_2x2["inverse"].data == [
        [Fraction(-2), Fraction(1)],
        [Fraction(3, 2), Fraction(-1, 2)],
    ]
    assert res_2x2["verification_step"]["coincide"] is True
    assert res_2x2["verification_reverse_step"]["coincide"] is True
    assert res_2x2["transpose_property_step"]["coincide"] is True
    assert len(res_2x2["steps"]) > 0

    mat_sing = Matrix(2, 2, [[1, 2], [2, 4]])
    res_sing = resolutor.solve(mat_sing)
    assert res_sing["status"] == "SINGULAR"
    assert res_sing["determinant"] == 0
    assert res_sing["inverse"] is None

    mat_1x1 = Matrix(1, 1, [[5]])
    res_1x1 = resolutor.solve(mat_1x1)
    assert res_1x1["status"] == "SUCCESS"
    assert res_1x1["inverse"].data == [[Fraction(1, 5)]]

    mat_2x3 = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    res_2x3 = resolutor.solve(mat_2x3)
    assert res_2x3["status"] == "ERROR"

    res_no_latex = resolutor.solve(mat_2x2, build_step_latex=False)
    assert res_no_latex["status"] == "SUCCESS"
    assert res_no_latex["inverse"].data == res_2x2["inverse"].data
    assert all(s["detail_latex"] is None for s in res_no_latex["steps"])
