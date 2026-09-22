"""Tests de la clave `solution_exact` en GaussSolver.solve().

`solution_exact` expone la solución como list[Fraction] cuando el sistema
tiene solución única, y None cuando es indeterminado o inconsistente.
Es fuente de verdad para consumidores que necesitan coeficientes exactos
sin re-parsear los strings paramétricos (por ejemplo, el futuro módulo de
combinación lineal de vectores).

La clave `solution` (strings) se preserva intacta para retrocompatibilidad.
"""
from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver
from src.backend.utils.formatters import format_fraction_str


# ---------------------------------------------------------------------------
# Caso UNIQUE: solution_exact es list[Fraction]
# ---------------------------------------------------------------------------

def test_solution_exact_unique_system():
    """Sistema 3x3 con solución entera: [2, 3, -1]."""
    A_aug = Matrix(3, 4, [
        [2, 1, -1, 8],
        [-3, -1, 2, -11],
        [-2, 1, 2, -3],
    ])
    result = GaussSolver(A_aug).solve()

    assert result["status"] == "UNIQUE_SOLUTION"
    assert result["solution_exact"] == [Fraction(2), Fraction(3), Fraction(-1)]


def test_solution_exact_with_fractions():
    """Solución con fracciones: exactitud garantizada."""
    A_aug = Matrix(2, 3, [
        [2, 1, 1],
        [1, 3, 2],
    ])
    result = GaussSolver(A_aug).solve()

    assert result["status"] == "UNIQUE_SOLUTION"
    # x1 = 1/5, x2 = 3/5
    assert result["solution_exact"] == [Fraction(1, 5), Fraction(3, 5)]


def test_solution_exact_preserves_large_denominator():
    """Denominadores > 1000 no se truncan en la solución exacta."""
    A_aug = Matrix(1, 2, [
        [1001, 1],
    ])
    result = GaussSolver(A_aug).solve()

    assert result["status"] == "UNIQUE_SOLUTION"
    assert result["solution_exact"] == [Fraction(1, 1001)]


def test_solution_exact_gauss_jordan_matches_gauss():
    """Gauss y Gauss-Jordan devuelven el mismo solution_exact."""
    A_aug = Matrix(3, 4, [
        [2, 1, -1, 8],
        [-3, -1, 2, -11],
        [-2, 1, 2, -3],
    ])
    r_gauss = GaussSolver(A_aug).solve()
    r_gj = GaussJordanSolver(A_aug).solve()

    assert r_gauss["solution_exact"] == r_gj["solution_exact"]


# ---------------------------------------------------------------------------
# Caso INFINITE: solution_exact es None
# ---------------------------------------------------------------------------

def test_solution_exact_none_when_infinite_solutions():
    """Sistema con variable libre → coeficientes no únicos → None."""
    A_aug = Matrix(1, 3, [
        [1, 1, 2],
    ])
    result = GaussSolver(A_aug).solve()

    assert result["status"] == "INFINITE_SOLUTIONS"
    assert result["solution_exact"] is None
    # La paramétrica sigue disponible vía solution (strings)
    assert result["solution"] is not None


def test_solution_exact_none_when_infinite_3x3():
    """Sistema 3x3 con rango deficiente."""
    A_aug = Matrix(3, 4, [
        [1, 2, 3, 6],
        [2, 4, 6, 12],
        [1, 1, 1, 3],
    ])
    result = GaussSolver(A_aug).solve()

    assert result["status"] == "INFINITE_SOLUTIONS"
    assert result["solution_exact"] is None


# ---------------------------------------------------------------------------
# Caso NO_SOLUTION: solution_exact es None
# ---------------------------------------------------------------------------

def test_solution_exact_none_when_no_solution():
    """Sistema inconsistente → None."""
    A_aug = Matrix(2, 3, [
        [1, 1, 1],
        [2, 2, 5],
    ])
    result = GaussSolver(A_aug).solve()

    assert result["status"] == "NO_SOLUTION"
    assert result["solution_exact"] is None


def test_solution_exact_key_always_present():
    """El contrato garantiza la clave en todos los estados posibles."""
    casos = [
        Matrix(1, 2, [[1, 1]]),                # UNIQUE
        Matrix(1, 3, [[1, 1, 2]]),             # INFINITE
        Matrix(2, 3, [[1, 1, 1], [2, 2, 5]]),  # NO_SOLUTION
    ]
    for A_aug in casos:
        result = GaussSolver(A_aug).solve()
        assert "solution_exact" in result, f"Falta en status={result['status']}"


# ---------------------------------------------------------------------------
# Retrocompatibilidad: `solution` intacta
# ---------------------------------------------------------------------------

def test_solution_strings_unchanged():
    """El string paramétrico sigue siendo exactamente el mismo."""
    A_aug = Matrix(2, 3, [
        [2, 1, 1],
        [1, 3, 2],
    ])
    result = GaussSolver(A_aug).solve()

    assert result["solution"] == ["1/5", "3/5"]


def test_solution_exact_consistent_with_solution_strings():
    """Cada Fraction de solution_exact coincide con su string en solution."""
    A_aug = Matrix(3, 4, [
        [2, 1, -1, 8],
        [-3, -1, 2, -11],
        [-2, 1, 2, -3],
    ])
    result = GaussSolver(A_aug).solve()

    for frac, s in zip(result["solution_exact"], result["solution"]):
        assert format_fraction_str(frac) == s
        
# ---------------------------------------------------------------------------
# free_cols — contrato del solver
# ---------------------------------------------------------------------------

def test_free_cols_empty_for_unique_solution():
    A_aug = Matrix(2, 3, [[1, 0, 5], [0, 1, 3]])
    result = GaussSolver(A_aug).solve()
    assert result["free_cols"] == []


def test_free_cols_single_free_variable():
    """Sistema 1×3: 2 variables (x1, x2) + b. Pivote en col 0 → col 1 libre."""
    A_aug = Matrix(1, 3, [[1, 2, 3]])
    result = GaussSolver(A_aug).solve()
    assert result["status"] == "INFINITE_SOLUTIONS"
    # num_vars = n - 1 = 2. Pivote en col 0 → free_cols = [1].
    # La col 2 es el término independiente, NO una variable.
    assert result["free_cols"] == [1]


def test_free_cols_multiple_free_variables():
    """Sistema 1×4: 3 variables + b. Pivote en col 0 → cols 1 y 2 libres."""
    A_aug = Matrix(1, 4, [[1, 2, 3, 4]])
    result = GaussSolver(A_aug).solve()
    assert result["status"] == "INFINITE_SOLUTIONS"
    assert result["free_cols"] == [1, 2]


def test_free_cols_empty_for_no_solution():
    A_aug = Matrix(2, 3, [[1, 1, 1], [2, 2, 5]])
    result = GaussSolver(A_aug).solve()
    assert result["status"] == "NO_SOLUTION"
    assert result["free_cols"] == []


def test_free_cols_key_always_present():
    casos = [
        Matrix(1, 2, [[1, 1]]),                # UNIQUE
        Matrix(1, 3, [[1, 1, 2]]),             # INFINITE
        Matrix(2, 3, [[1, 1, 1], [2, 2, 5]]),  # NO_SOLUTION
    ]
    for A_aug in casos:
        result = GaussSolver(A_aug).solve()
        assert "free_cols" in result