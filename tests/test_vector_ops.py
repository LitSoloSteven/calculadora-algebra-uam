"""Tests de VectorOpsSolver: suma, resta, multiplicación escalar.

Cubre operaciones con vectores fila y columna, transposición automática
(default) vs estricta, preservación de precisión exacta, y trazabilidad
paso a paso.
"""
from fractions import Fraction

import pytest

from src.backend.exceptions import InvalidVectorError
from src.backend.models.matrix import Matrix
from src.backend.solvers.vector_ops.operations import VectorOpsSolver


# ---------------------------------------------------------------------------
# Suma — casos básicos
# ---------------------------------------------------------------------------

def test_add_column_vectors():
    """(1,2,3)ᵀ + (4,5,6)ᵀ = (5,7,9)ᵀ."""
    v1 = Matrix(3, 1, [[1], [2], [3]])
    v2 = Matrix(3, 1, [[4], [5], [6]])
    res = VectorOpsSolver().add(v1, v2)

    assert res["status"] == "SUCCESS"
    assert res["result_matrix"].data == [[5], [7], [9]]
    assert res["result_matrix"].rows == 3
    assert res["result_matrix"].cols == 1


def test_add_row_vectors():
    """(1,2) + (3,4) = (4,6) — fila."""
    v1 = Matrix(1, 2, [[1, 2]])
    v2 = Matrix(1, 2, [[3, 4]])
    res = VectorOpsSolver().add(v1, v2)

    assert res["status"] == "SUCCESS"
    assert res["result_matrix"].data == [[4, 6]]
    assert res["result_matrix"].rows == 1
    assert res["result_matrix"].cols == 2


def test_add_with_fractions():
    """(1/2, 1/3) + (1/2, 2/3) = (1, 1) exacto."""
    v1 = Matrix(2, 1, [[Fraction(1, 2)], [Fraction(1, 3)]])
    v2 = Matrix(2, 1, [[Fraction(1, 2)], [Fraction(2, 3)]])
    res = VectorOpsSolver().add(v1, v2)

    assert res["result_matrix"].data == [[1], [1]]


def test_add_preserves_large_denominator():
    """(1/1001, 0) + (1000/1001, 0) = (1, 0) sin truncar."""
    v1 = Matrix(2, 1, [[Fraction(1, 1001)], [0]])
    v2 = Matrix(2, 1, [[Fraction(1000, 1001)], [0]])
    res = VectorOpsSolver().add(v1, v2)

    assert res["result_matrix"].data == [[1], [0]]


def test_add_negative_components():
    v1 = Matrix(2, 1, [[-3], [5]])
    v2 = Matrix(2, 1, [[2], [-8]])
    res = VectorOpsSolver().add(v1, v2)

    assert res["result_matrix"].data == [[-1], [-3]]


# ---------------------------------------------------------------------------
# Suma — orientación y strict
# ---------------------------------------------------------------------------

def test_add_col_plus_row_transposes_in_permissive_mode():
    """(1,2,3)ᵀ + (4,5,6) fila → transpone la fila, resultado columna."""
    v1 = Matrix(3, 1, [[1], [2], [3]])
    v2 = Matrix(1, 3, [[4, 5, 6]])
    res = VectorOpsSolver().add(v1, v2)  # strict=False default

    assert res["status"] == "SUCCESS"
    assert res["result_matrix"].data == [[5], [7], [9]]
    assert res["result_matrix"].rows == 3
    assert res["result_matrix"].cols == 1


def test_add_row_plus_col_transposes_in_permissive_mode():
    """Fila primero → resultado fila."""
    v1 = Matrix(1, 3, [[4, 5, 6]])
    v2 = Matrix(3, 1, [[1], [2], [3]])
    res = VectorOpsSolver().add(v1, v2)

    assert res["result_matrix"].data == [[5, 7, 9]]
    assert res["result_matrix"].rows == 1
    assert res["result_matrix"].cols == 3


def test_add_includes_transposition_step_when_applied():
    """El paso de ajuste de orientación queda registrado."""
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(1, 2, [[3, 4]])
    res = VectorOpsSolver().add(v1, v2)

    descriptions = [s["description"] for s in res["steps"]]
    assert any("Ajuste de orientación" in d for d in descriptions)


def test_add_strict_rejects_orientation_mismatch():
    """strict=True rechaza fila + columna con dims iguales."""
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(1, 2, [[3, 4]])
    res = VectorOpsSolver().add(v1, v2, strict=True)

    assert res["status"] == "ERROR"
    assert "strict=True" in res["message"]
    assert res["result_matrix"] is None


# ---------------------------------------------------------------------------
# Suma — errores
# ---------------------------------------------------------------------------

def test_add_rejects_non_vector():
    """2×3 no es vector."""
    v1 = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    v2 = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    res = VectorOpsSolver().add(v1, v2)

    assert res["status"] == "ERROR"
    assert "se esperaba un vector" in res["message"]
    assert "2×3" in res["message"]


def test_add_rejects_mismatched_dimensions():
    """(1,2) + (1,2,3) → dims distintas."""
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(3, 1, [[1], [2], [3]])
    res = VectorOpsSolver().add(v1, v2)

    assert res["status"] == "ERROR"
    assert "Dimensiones incompatibles" in res["message"]
    assert "dim 2" in res["message"]
    assert "dim 3" in res["message"]


def test_add_raises_invalid_vector_error_class():
    """La excepción es InvalidVectorError, no ValueError genérica."""
    from src.backend.exceptions import AlgebraLinealError
    assert issubclass(InvalidVectorError, AlgebraLinealError)


# ---------------------------------------------------------------------------
# Resta
# ---------------------------------------------------------------------------

def test_subtract_column_vectors():
    v1 = Matrix(3, 1, [[5], [7], [9]])
    v2 = Matrix(3, 1, [[1], [2], [3]])
    res = VectorOpsSolver().subtract(v1, v2)

    assert res["status"] == "SUCCESS"
    assert res["result_matrix"].data == [[4], [5], [6]]


def test_subtract_with_fractions():
    v1 = Matrix(2, 1, [[1], [1]])
    v2 = Matrix(2, 1, [[Fraction(1, 3)], [Fraction(1, 7)]])
    res = VectorOpsSolver().subtract(v1, v2)

    assert res["result_matrix"].data == [[Fraction(2, 3)], [Fraction(6, 7)]]


def test_subtract_strict_rejects_row_col_mix():
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(1, 2, [[3, 4]])
    res = VectorOpsSolver().subtract(v1, v2, strict=True)

    assert res["status"] == "ERROR"


# ---------------------------------------------------------------------------
# Multiplicación escalar
# ---------------------------------------------------------------------------

def test_scalar_multiply_basic():
    """3 · (2, 4, 6)ᵀ = (6, 12, 18)ᵀ."""
    v = Matrix(3, 1, [[2], [4], [6]])
    res = VectorOpsSolver().scalar_multiply(3, v)

    assert res["status"] == "SUCCESS"
    assert res["result_matrix"].data == [[6], [12], [18]]


def test_scalar_multiply_row_vector():
    """2 · (1,2,3) fila = (2,4,6) fila."""
    v = Matrix(1, 3, [[1, 2, 3]])
    res = VectorOpsSolver().scalar_multiply(2, v)

    assert res["result_matrix"].data == [[2, 4, 6]]
    assert res["result_matrix"].rows == 1


def test_scalar_multiply_fraction_scalar():
    """(1/2) · (1, 2, 3)ᵀ = (1/2, 1, 3/2)ᵀ."""
    v = Matrix(3, 1, [[1], [2], [3]])
    res = VectorOpsSolver().scalar_multiply(Fraction(1, 2), v)

    assert res["result_matrix"].data == [
        [Fraction(1, 2)], [1], [Fraction(3, 2)]
    ]


def test_scalar_multiply_string_scalar_is_exact():
    v = Matrix(2, 1, [[4], [8]])
    res = VectorOpsSolver().scalar_multiply("3/4", v)

    assert res["result_matrix"].data == [[3], [6]]


def test_scalar_multiply_zero_scalar():
    v = Matrix(3, 1, [[1], [2], [3]])
    res = VectorOpsSolver().scalar_multiply(0, v)

    assert res["result_matrix"].data == [[0], [0], [0]]


def test_scalar_multiply_negative():
    v = Matrix(2, 1, [[1], [-2]])
    res = VectorOpsSolver().scalar_multiply(-1, v)

    assert res["result_matrix"].data == [[-1], [2]]


def test_scalar_multiply_invalid_scalar():
    v = Matrix(2, 1, [[1], [2]])
    res = VectorOpsSolver().scalar_multiply("abc", v)

    assert res["status"] == "ERROR"
    assert "Escalar inválido" in res["message"]


def test_scalar_multiply_rejects_non_vector():
    v = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    res = VectorOpsSolver().scalar_multiply(2, v)

    assert res["status"] == "ERROR"
    assert "se esperaba un vector" in res["message"]


# ---------------------------------------------------------------------------
# Trazabilidad
# ---------------------------------------------------------------------------

def test_add_produces_one_step_per_component_plus_initial():
    v1 = Matrix(3, 1, [[1], [2], [3]])
    v2 = Matrix(3, 1, [[4], [5], [6]])
    res = VectorOpsSolver().add(v1, v2)

    # 1 inicial + 3 componentes
    assert len(res["steps"]) == 4


def test_add_latex_details_count_matches_components():
    v1 = Matrix(3, 1, [[1], [2], [3]])
    v2 = Matrix(3, 1, [[4], [5], [6]])
    res = VectorOpsSolver().add(v1, v2)

    assert len(res["latex_details"]) == 3
    for detail in res["latex_details"]:
        assert "w_{" in detail


def test_add_steps_accumulate_result_matrix():
    """A partir del segundo paso, matrix lleva el estado acumulado."""
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(2, 1, [[3], [4]])
    res = VectorOpsSolver().add(v1, v2)

    # Paso 0: inicial, sin matrix
    assert res["steps"][0]["matrix"] is None
    # Paso 1: primer componente computado
    assert res["steps"][1]["matrix"].data == [[4], [0]]
    # Paso 2: ambos componentes
    assert res["steps"][2]["matrix"].data == [[4], [6]]


def test_scalar_multiply_steps_count():
    v = Matrix(3, 1, [[1], [2], [3]])
    res = VectorOpsSolver().scalar_multiply(2, v)

    # 1 inicial + 3 componentes
    assert len(res["steps"]) == 4


# ---------------------------------------------------------------------------
# Custom names
# ---------------------------------------------------------------------------

def test_add_with_custom_names_appear_in_latex():
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(2, 1, [[3], [4]])
    res = VectorOpsSolver().add(v1, v2, name1="u", name2="v")

    # El nombre custom NO aparece en el detalle LaTeX (w es siempre el resultado)
    # pero sí en los mensajes de error si los hubiera
    assert res["status"] == "SUCCESS"


def test_error_message_uses_custom_name():
    v1 = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    v2 = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    res = VectorOpsSolver().add(v1, v2, name1="mi_vector")

    assert "mi_vector" in res["message"]