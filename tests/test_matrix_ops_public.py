"""Tests de las operaciones matriciales públicas de MatrixOpsSolver.

Cubre `scalar_multiply`, que complementa la terna add/subtract/multiply
ya expuesta. Se sigue la convención del proyecto: Fraction exacto en
todo el cómputo, coordenadas en los mensajes de error, y preservación
de denominadores grandes.
"""
from fractions import Fraction

import pytest

from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver


# ---------------------------------------------------------------------------
# Casos básicos
# ---------------------------------------------------------------------------

def test_scalar_multiply_simple():
    """3 · [[2, -1], [3, 4]] = [[6, -3], [9, 12]] — ejemplo del PPT."""
    A = Matrix(2, 2, [[2, -1], [3, 4]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply(3, A)

    assert res["status"] == "SUCCESS"
    assert res["result_matrix"].data == [[6, -3], [9, 12]]
    assert res["result_matrix"].rows == 2
    assert res["result_matrix"].cols == 2


def test_scalar_multiply_zero_scalar():
    """0 · A = matriz nula, sin importar A."""
    A = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply(0, A)

    assert res["status"] == "SUCCESS"
    assert res["result_matrix"].data == [[0, 0, 0], [0, 0, 0]]


def test_scalar_multiply_negative_scalar():
    """(-1) · A = -A. Cada entrada cambia de signo."""
    A = Matrix(2, 2, [[1, -2], [3, -4]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply(-1, A)

    assert res["result_matrix"].data == [[-1, 2], [-3, 4]]


def test_scalar_multiply_preserves_order():
    """Rectangular m×n sigue siendo m×n después de multiplicar."""
    A = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply(2, A)

    assert res["result_matrix"].rows == 2
    assert res["result_matrix"].cols == 3


# ---------------------------------------------------------------------------
# Precisión exacta
# ---------------------------------------------------------------------------

def test_scalar_multiply_fraction_scalar():
    """(1/2) · [[1, 2], [3, 4]] = [[1/2, 1], [3/2, 2]] exacto."""
    A = Matrix(2, 2, [[1, 2], [3, 4]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply(Fraction(1, 2), A)

    assert res["result_matrix"].data == [
        [Fraction(1, 2), Fraction(2, 2)],
        [Fraction(3, 2), Fraction(4, 2)],
    ]


def test_scalar_multiply_string_scalar_is_parsed_exact():
    """El escalar puede venir como string ('3/4') desde el frontend."""
    A = Matrix(2, 2, [[4, 8], [12, 16]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply("3/4", A)

    assert res["status"] == "SUCCESS"
    assert res["result_matrix"].data == [[3, 6], [9, 12]]


def test_scalar_multiply_preserves_large_denominator():
    """Un denominador > 1000 no se trunca al multiplicar."""
    A = Matrix(2, 1, [[Fraction(1, 1001)], [Fraction(1, 1001)]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply(1001, A)

    assert res["result_matrix"].data == [[1], [1]]


def test_scalar_multiply_float_scalar_returns_fraction_when_exact():
    """0.5 se recupera como Fraction(1,2) y el producto queda exacto."""
    A = Matrix(1, 2, [[3, 5]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply(0.5, A)

    assert res["result_matrix"].data == [[Fraction(3, 2), Fraction(5, 2)]]


# ---------------------------------------------------------------------------
# Errores
# ---------------------------------------------------------------------------

def test_scalar_multiply_invalid_string_returns_error():
    """'abc' no es un escalar parseable → ERROR, sin excepción."""
    A = Matrix(2, 2, [[1, 2], [3, 4]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply("abc", A)

    assert res["status"] == "ERROR"
    assert res["result_matrix"] is None
    assert "Escalar inválido" in res["message"]


def test_scalar_multiply_empty_string_returns_error():
    """'' no es un escalar válido."""
    A = Matrix(2, 2, [[1, 2], [3, 4]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply("", A)

    assert res["status"] == "ERROR"


def test_scalar_multiply_division_by_zero_returns_error():
    """'1/0' se reporta como error, no como ZeroDivisionError."""
    A = Matrix(2, 2, [[1, 2], [3, 4]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply("1/0", A)

    assert res["status"] == "ERROR"
    assert "cero" in res["message"].lower() or "inválido" in res["message"].lower()


# ---------------------------------------------------------------------------
# Trazabilidad
# ---------------------------------------------------------------------------

def test_scalar_multiply_produces_one_step_per_cell():
    """Cada celda genera su propio paso, más un paso inicial."""
    A = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply(2, A)

    # 1 paso inicial + 6 celdas = 7
    assert len(res["steps"]) == 1 + 2 * 3


def test_scalar_multiply_latex_details_count_matches_cells():
    A = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply(2, A)

    assert len(res["latex_details"]) == 2 * 3


def test_scalar_multiply_steps_include_result_matrix():
    """Los pasos a partir del segundo llevan el estado acumulado."""
    A = Matrix(1, 2, [[1, 2]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply(3, A)

    # Paso 0: inicial, sin matriz. Paso 1 y 2: con matriz.
    assert res["steps"][0]["matrix"] is None
    assert res["steps"][1]["matrix"] is not None
    assert res["steps"][2]["matrix"] is not None


def test_scalar_multiply_fraction_latex_uses_parentheses():
    """El detalle LaTeX de fracciones las envuelve en \\frac sin ambigüedad."""
    A = Matrix(1, 1, [[Fraction(1, 2)]])
    solver = MatrixOpsSolver()
    res = solver.scalar_multiply(Fraction(1, 3), A)

    detail = res["latex_details"][0]
    assert "\\frac" in detail
    assert "C_{1,1}" in detail