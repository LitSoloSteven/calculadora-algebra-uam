"""Tests de VectorOpsSolver.is_linear_combination.

Cubre:
  - UNIQUE con coeficientes enteros, fraccionarios y denominadores grandes.
  - INFINITE cuando los vectores son linealmente dependientes.
  - NO_SOLUTION cuando b no está en el span.
  - ERROR en validaciones tempranas (shapes, dims, lista vacía).
  - El paso de verificación (comprobación componente a componente).
  - Reutilización de GaussSolver: los steps incluyen los pasos del solver.
"""
from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.vector_ops.operations import VectorOpsSolver


# ---------------------------------------------------------------------------
# UNIQUE — combinación con representación única
# ---------------------------------------------------------------------------

def test_uniqueness_with_basis():
    """b = 3·e_1 + 2·e_2 en R², representación única."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    b = Matrix(2, 1, [[3], [2]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert res["status"] == "UNIQUE"
    assert res["es_combinacion_lineal"] is True
    assert res["coeficientes"] == [Fraction(3), Fraction(2)]
    assert res["coeficientes_str"] == ["3", "2"]
    assert res["parametros_libres"] == []


def test_unique_with_fractions():
    """b = (1/2)·v₁ + (1/3)·v₂, coeficientes fraccionarios exactos."""
    v1 = Matrix(2, 1, [[2], [0]])
    v2 = Matrix(2, 1, [[0], [3]])
    b = Matrix(2, 1, [[1], [1]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert res["status"] == "UNIQUE"
    assert res["coeficientes"] == [Fraction(1, 2), Fraction(1, 3)]
    assert res["coeficientes_str"] == ["1/2", "1/3"]


def test_unique_preserves_large_denominator():
    """Denominador > 1000 no se trunca en los coeficientes."""
    # v1 = (1001, 0), b = (1, 0) → c_1 = 1/1001
    v1 = Matrix(2, 1, [[1001], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    b = Matrix(2, 1, [[1], [0]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert res["status"] == "UNIQUE"
    assert res["coeficientes"][0] == Fraction(1, 1001)


def test_unique_in_r3_with_three_vectors():
    """Ejemplo clásico de Lay en R³."""
    v1 = Matrix(3, 1, [[1], [-2], [-5]])
    v2 = Matrix(3, 1, [[2], [5], [6]])
    b = Matrix(3, 1, [[7], [4], [-3]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    # b = 3·v1 + 2·v2
    assert res["status"] == "UNIQUE"
    assert res["coeficientes"] == [Fraction(3), Fraction(2)]


def test_unique_returns_gauss_steps():
    """Los steps del Gauss subyacente se propagan."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    b = Matrix(2, 1, [[3], [2]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert len(res["steps"]) > 0
    assert res["steps"][0]["matrix"] is not None


def test_unique_includes_back_substitution_steps():
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    b = Matrix(2, 1, [[3], [2]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert len(res["back_substitution_steps"]) > 0


# ---------------------------------------------------------------------------
# UNIQUE — verification_step
# ---------------------------------------------------------------------------

def test_verification_step_present_on_unique():
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    b = Matrix(2, 1, [[3], [2]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert res["verification_step"] is not None
    assert res["verification_step"]["coincide"] is True
    assert "Comprobación" in res["verification_step"]["description"]
    assert "c_1" in res["verification_step"]["detail_latex"]


def test_verification_step_marks_ok():
    """El símbolo de checkmark aparece en el detalle LaTeX."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    b = Matrix(2, 1, [[3], [2]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert "\\checkmark" in res["verification_step"]["detail_latex"]
    assert res["verification_step"]["coincide"] is True


# ---------------------------------------------------------------------------
# INFINITE — vectores linealmente dependientes
# ---------------------------------------------------------------------------

def test_infinite_when_vectors_are_dependent():
    """v₂ = 2·v₁ → infinitas representaciones de b = 3·v₁."""
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(2, 1, [[2], [4]])
    b = Matrix(2, 1, [[3], [6]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert res["status"] == "INFINITE"
    assert res["es_combinacion_lineal"] is True
    assert res["coeficientes"] is None
    assert res["solucion_parametrica"] is not None
    assert len(res["parametros_libres"]) >= 1
    assert "infinitas" in res["message"].lower()


def test_infinite_has_no_verification_step():
    """No hay coeficientes únicos → no hay verificación."""
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(2, 1, [[2], [4]])
    b = Matrix(2, 1, [[3], [6]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert res["verification_step"] is None


# ---------------------------------------------------------------------------
# NO_SOLUTION — b fuera del span
# ---------------------------------------------------------------------------

def test_no_solution_when_b_outside_span():
    """v_1, v_2 viven en y=0, pero b tiene y=1."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[2], [0]])
    b = Matrix(2, 1, [[0], [1]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert res["status"] == "NO_SOLUTION"
    assert res["es_combinacion_lineal"] is False
    assert res["coeficientes"] is None
    assert res["verification_step"] is None


def test_no_solution_in_r3():
    """Tres vectores coplanares, b fuera del plano."""
    v1 = Matrix(3, 1, [[1], [0], [0]])
    v2 = Matrix(3, 1, [[0], [1], [0]])
    v3 = Matrix(3, 1, [[1], [1], [0]])  # coplanar con v1, v2
    b = Matrix(3, 1, [[0], [0], [1]])   # fuera del plano

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2, v3])

    assert res["status"] == "NO_SOLUTION"


# ---------------------------------------------------------------------------
# Casos degenerados: b = 0
# ---------------------------------------------------------------------------

def test_zero_b_always_is_combination_when_unique():
    """b = 0 con vectores LI → c_i = 0 todos."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    b = Matrix(2, 1, [[0], [0]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert res["status"] == "UNIQUE"
    assert res["coeficientes"] == [Fraction(0), Fraction(0)]


def test_zero_b_with_dependent_vectors_is_infinite():
    v1 = Matrix(2, 1, [[1], [1]])
    v2 = Matrix(2, 1, [[2], [2]])
    b = Matrix(2, 1, [[0], [0]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert res["status"] == "INFINITE"


# ---------------------------------------------------------------------------
# ERROR — validaciones tempranas
# ---------------------------------------------------------------------------

def test_error_on_empty_vectors_list():
    b = Matrix(2, 1, [[1], [2]])
    res = VectorOpsSolver().is_linear_combination(b, [])

    assert res["status"] == "ERROR"
    assert "al menos un vector" in res["message"]


def test_error_on_non_list_vectors():
    b = Matrix(2, 1, [[1], [2]])
    res = VectorOpsSolver().is_linear_combination(b, "no soy lista")

    assert res["status"] == "ERROR"


def test_error_on_row_vector_b():
    """b debe ser columna n×1. Fila se rechaza (no auto-transposición)."""
    v1 = Matrix(2, 1, [[1], [0]])
    b_row = Matrix(1, 2, [[3, 2]])

    res = VectorOpsSolver().is_linear_combination(b_row, [v1])

    assert res["status"] == "ERROR"
    assert "b" in res["message"]
    assert "se esperaba vector columna" in res["message"]


def test_error_on_row_vector_in_list():
    """Un vector fila en la lista se rechaza explícitamente."""
    v1_col = Matrix(2, 1, [[1], [0]])
    v2_row = Matrix(1, 2, [[0, 1]])
    b = Matrix(2, 1, [[3], [2]])

    res = VectorOpsSolver().is_linear_combination(b, [v1_col, v2_row])

    assert res["status"] == "ERROR"
    assert "v_2" in res["message"]


def test_error_on_non_vector_b():
    """Una matriz 2×3 no es vector."""
    v1 = Matrix(2, 1, [[1], [0]])
    b_matrix = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])

    res = VectorOpsSolver().is_linear_combination(b_matrix, [v1])

    assert res["status"] == "ERROR"
    assert "2×3" in res["message"]


def test_error_on_dimension_mismatch():
    """b dim 3, vectores dim 2 → error."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    b = Matrix(3, 1, [[1], [2], [3]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert res["status"] == "ERROR"
    assert "Dimensiones incompatibles" in res["message"]
    assert "b tiene dim 3" in res["message"]
    assert "v_1 tiene dim 2" in res["message"]


def test_error_on_inconsistent_vector_dimensions():
    """v_1 dim 2, v_2 dim 3 → error."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(3, 1, [[0], [1], [2]])
    b = Matrix(2, 1, [[1], [1]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    assert res["status"] == "ERROR"
    assert "v_2" in res["message"]


# ---------------------------------------------------------------------------
# Contrato de la respuesta
# ---------------------------------------------------------------------------

def test_all_contract_keys_present_on_success():
    """Todas las claves del contrato están presentes en éxito."""
    v1 = Matrix(2, 1, [[1], [0]])
    b = Matrix(2, 1, [[3], [0]])
    res = VectorOpsSolver().is_linear_combination(b, [v1])

    expected_keys = {
        "status", "es_combinacion_lineal", "coeficientes", "coeficientes_str",
        "solucion_parametrica", "parametros_libres", "message",
        "steps", "back_substitution_steps", "verification_step",
    }
    assert expected_keys.issubset(res.keys())


def test_all_contract_keys_present_on_error():
    """Todas las claves del contrato están presentes en error."""
    b = Matrix(2, 1, [[1], [2]])
    res = VectorOpsSolver().is_linear_combination(b, [])

    expected_keys = {
        "status", "es_combinacion_lineal", "coeficientes", "coeficientes_str",
        "solucion_parametrica", "parametros_libres", "message",
        "steps", "back_substitution_steps", "verification_step",
    }
    assert expected_keys.issubset(res.keys())


# ---------------------------------------------------------------------------
# Custom variable_names
# ---------------------------------------------------------------------------

def test_custom_variable_names_in_back_substitution():
    """Los nombres custom aparecen en los pasos de sustitución."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    b = Matrix(2, 1, [[3], [2]])

    res = VectorOpsSolver().is_linear_combination(
        b, [v1, v2], variable_names=["alpha", "beta"]
    )

    # Los pasos de back substitution usan los nombres custom
    all_text = " ".join(res["back_substitution_steps"])
    assert "alpha" in all_text or "beta" in all_text


# ---------------------------------------------------------------------------
# Uso de GaussSolver internamente
# ---------------------------------------------------------------------------

def test_uses_gauss_not_reimplemented():
    """El primer step del Gauss es la matriz aumentada [v_1|...|v_k|b]."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    b = Matrix(2, 1, [[3], [2]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])

    # El primer step del Gauss dice "Matriz inicial aumentada"
    first_desc = res["steps"][0]["description"]
    assert "inicial" in first_desc.lower()
    
def test_verification_step_uses_valid_pmatrix():
    """El LaTeX del verification_step usa \\\\ como separador de filas en pmatrix."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    b = Matrix(2, 1, [[3], [2]])

    res = VectorOpsSolver().is_linear_combination(b, [v1, v2])
    detail = res["verification_step"]["detail_latex"]

    # Las pmatrix del LHS computed y del b deben usar \\ como separador
    assert "\\\\" in detail
    # Y NO deben usar comas entre los elementos de la pmatrix
    import re
    matrices = re.findall(r"\\begin\{pmatrix\}(.*?)\\end\{pmatrix\}", detail)
    assert len(matrices) >= 2
    for contenido in matrices:
        # Sin comas dentro de una pmatrix (serían texto literal, no filas)
        assert "," not in contenido