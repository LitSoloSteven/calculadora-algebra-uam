"""Regresión de precisión en MatrixExpressionEvaluator.

Cubre:
- Literales numéricos como Fraction, no float (commit 4ae547b)
- Negación unaria preservando Fraction
- Rechazo explícito de expresiones que devuelven escalar puro
"""
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator


def test_literal_preserves_fraction_precision():
    """Regresión: '3A' con A = [[1/3]] debe dar Fraction(1), no 0.9999..."""
    A = Matrix(1, 1, [[Fraction(1, 3)]])
    ev = MatrixExpressionEvaluator()
    res = ev.evaluate("3A", {"A": A})
    valor = res["result_matrix"].get(0, 0)
    assert valor == Fraction(1, 1), f"Esperado Fraction(1), obtenido {valor!r}"
    assert isinstance(valor, Fraction), f"Tipo esperado Fraction, obtenido {type(valor).__name__}"


def test_scalar_multiplication_preserves_types():
    """Multiplicación por escalar preserva Fraction en todas las celdas."""
    B = Matrix(2, 2, [[1, 2], [3, 4]])
    ev = MatrixExpressionEvaluator()
    res = ev.evaluate("2B", {"B": B})
    assert res["status"] == "SUCCESS"
    esperado = [[Fraction(2), Fraction(4)], [Fraction(6), Fraction(8)]]
    for r in range(2):
        for c in range(2):
            got = res["result_matrix"].get(r, c)
            assert got == esperado[r][c], f"[{r},{c}]: esperado {esperado[r][c]}, obtenido {got}"
            assert isinstance(got, Fraction), f"[{r},{c}]: se esperaba Fraction, es {type(got).__name__}"


def test_matrix_addition_preserves_types():
    """Suma de matrices preserva Fraction."""
    A3 = Matrix(2, 2, [[1, 0], [0, 1]])
    B3 = Matrix(2, 2, [[1, 2], [3, 4]])
    ev = MatrixExpressionEvaluator()
    res = ev.evaluate("A3 + B3", {"A3": A3, "B3": B3})
    assert res["status"] == "SUCCESS"
    esperado = [[Fraction(2), Fraction(2)], [Fraction(3), Fraction(5)]]
    for r in range(2):
        for c in range(2):
            got = res["result_matrix"].get(r, c)
            assert got == esperado[r][c], f"[{r},{c}]: esperado {esperado[r][c]}, obtenido {got}"


def test_scalar_only_expression_is_rejected():
    """Regresión: '_is_scalar(final_val)' reemplaza a 'isinstance(final_val, float)'."""
    ev = MatrixExpressionEvaluator()
    res = ev.evaluate("3 * 4", {})
    assert res["status"] == "ERROR"
    assert "escalar" in res["message"].lower()


def test_unary_negation_preserves_fraction():
    """Regresión: la negación unaria debe usar Fraction(-1), no -1.0."""
    C = Matrix(1, 1, [[Fraction(1, 3)]])
    ev = MatrixExpressionEvaluator()
    res = ev.evaluate("-C", {"C": C})
    valor = res["result_matrix"].get(0, 0)
    assert valor == Fraction(-1, 3), f"Esperado Fraction(-1/3), obtenido {valor!r}"
    assert isinstance(valor, Fraction), f"Tipo esperado Fraction, obtenido {type(valor).__name__}"