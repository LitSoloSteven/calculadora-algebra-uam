from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator


def _eval(expr, matrices):
    return MatrixExpressionEvaluator().evaluate(expr, matrices)


def test_AB_means_A_times_B():
    A = Matrix(1, 1, [[2]])
    B = Matrix(1, 1, [[3]])
    r = _eval("AB", {"A": A, "B": B})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(6)


def test_ABC_means_A_times_B_times_C():
    A = Matrix(1, 1, [[2]])
    B = Matrix(1, 1, [[3]])
    C = Matrix(1, 1, [[4]])
    r = _eval("ABC", {"A": A, "B": B, "C": C})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(24)


def test_A_with_digit_is_name_not_multiplication():
    """A2 se interpreta como nombre 'A2', no como A * 2.
    Preserva retrocompatibilidad con tests y consumidores que usan
    nombres con dígitos."""
    A2 = Matrix(1, 1, [[5]])
    r = _eval("A2", {"A2": A2})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(5)


def test_2A_still_works():
    A = Matrix(1, 1, [[5]])
    r = _eval("2A", {"A": A})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(10)


def test_underscore_name_still_works():
    A_foo = Matrix(1, 1, [[7]])
    r = _eval("A_foo", {"A_foo": A_foo})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(7)


def test_AB_with_explicit_star_still_works():
    A = Matrix(1, 1, [[2]])
    B = Matrix(1, 1, [[3]])
    r = _eval("A*B", {"A": A, "B": B})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(6)


def test_A_plus_B_still_works():
    A = Matrix(1, 1, [[2]])
    B = Matrix(1, 1, [[3]])
    r = _eval("A + B", {"A": A, "B": B})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(5)
    
def test_A3_plus_B3_still_works():
    """El test preexistente que rompió con el fix anterior ahora pasa."""
    A3 = Matrix(2, 2, [[1, 0], [0, 1]])
    B3 = Matrix(2, 2, [[1, 2], [3, 4]])
    r = _eval("A3 + B3", {"A3": A3, "B3": B3})
    assert r["status"] == "SUCCESS"
    assert r["result_matrix"].data[0][0] == Fraction(2)


# --- Expresiones anidadas complejas y combinaciones ---

def test_complex_nested_expression_with_transpose():
    """2A - B(C - Dᵀ) y 2A - B*(C - D^T) con cálculo exacto."""
    A = Matrix(2, 2, [[1, 2], [3, 4]])
    B = Matrix(2, 2, [[5, 6], [7, 8]])
    C = Matrix(2, 2, [[1, 0], [0, 1]])
    D = Matrix(2, 2, [[2, 1], [0, 3]])
    mats = {"A": A, "B": B, "C": C, "D": D}

    for expr in ("2A - B(C - Dᵀ)", "2A - B*(C - D^T)", "2A - B*(C - D^t)"):
        r = _eval(expr, mats)
        assert r["status"] == "SUCCESS"
        # 2A = [[2, 4], [6, 8]]
        # Dᵀ = [[2, 0], [1, 3]]
        # C - Dᵀ = [[-1, 0], [-1, -2]]
        # B * (C - Dᵀ) = [[-11, -12], [-15, -16]]
        # 2A - B(C - Dᵀ) = [[13, 16], [21, 24]]
        assert r["result_matrix"].data == [
            [Fraction(13), Fraction(16)],
            [Fraction(21), Fraction(24)],
        ]


def test_scalar_multiplication_both_orders():
    """k * A y A * k dan el mismo resultado."""
    A = Matrix(2, 2, [[1, 2], [3, 4]])
    mats = {"A": A}

    r1 = _eval("2 * A", mats)
    r2 = _eval("A * 2", mats)
    r3 = _eval("2A", mats)
    r4 = _eval("(A)2", mats)

    expected = [[Fraction(2), Fraction(4)], [Fraction(6), Fraction(8)]]
    for r in (r1, r2, r3, r4):
        assert r["status"] == "SUCCESS"
        assert r["result_matrix"].data == expected


def test_transposition_expressions():
    """Aᵀ, (A + B)ᵀ y (A*B)ᵀ."""
    A = Matrix(2, 2, [[1, 2], [3, 4]])
    B = Matrix(2, 2, [[5, 6], [7, 8]])
    mats = {"A": A, "B": B}

    r_t = _eval("Aᵀ", mats)
    assert r_t["status"] == "SUCCESS"
    assert r_t["result_matrix"].data == [[Fraction(1), Fraction(3)], [Fraction(2), Fraction(4)]]

    r_sum_t = _eval("(A + B)ᵀ", mats)
    assert r_sum_t["status"] == "SUCCESS"
    assert r_sum_t["result_matrix"].data == [[Fraction(6), Fraction(10)], [Fraction(8), Fraction(12)]]


def test_negation_expressions():
    """-A, --A, -(A + B), A * -B y A * (-2)."""
    A = Matrix(2, 2, [[1, 2], [3, 4]])
    B = Matrix(2, 2, [[5, 6], [7, 8]])
    mats = {"A": A, "B": B}

    r_neg = _eval("-A", mats)
    assert r_neg["status"] == "SUCCESS"
    assert r_neg["result_matrix"].data == [[Fraction(-1), Fraction(-2)], [Fraction(-3), Fraction(-4)]]

    r_double_neg = _eval("--A", mats)
    assert r_double_neg["status"] == "SUCCESS"
    assert r_double_neg["result_matrix"].data == [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]

    r_mul_neg = _eval("A * -B", mats)
    assert r_mul_neg["status"] == "SUCCESS"
    assert r_mul_neg["result_matrix"].data == [[Fraction(-19), Fraction(-22)], [Fraction(-43), Fraction(-50)]]