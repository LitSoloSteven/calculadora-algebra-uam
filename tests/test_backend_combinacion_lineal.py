"""Pruebas de dominio para combinación lineal y operaciones vectoriales."""

from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.vector_ops.linear_combination import LinearCombinationSolver
from src.backend.solvers.vector_ops.operations import VectorOpsSolver


def test_combinacion_lineal_flujo_canonico():
    """Valida el ejemplo canónico de Lay en R³."""
    a1 = Matrix(3, 1, [[1], [-2], [-5]])
    a2 = Matrix(3, 1, [[2], [5], [6]])
    b = Matrix(3, 1, [[7], [4], [-3]])

    resolutor = LinearCombinationSolver()
    res = resolutor.solve(
        b,
        [a1, a2],
        variable_names=["x_1", "x_2"],
        vector_names=["a_1", "a_2"],
    )

    assert res["status"] == "UNIQUE"
    assert res["es_combinacion_lineal"] is True
    assert res["coeficientes"] == [Fraction(3), Fraction(2)]
    assert res["coeficientes_str"] == ["3", "2"]
    assert len(res["setup_steps"]) == 5

    assert "1. Ecuación vectorial" in res["setup_steps"][0]["description"]
    assert "2. Multiplicación de los escalares" in res["setup_steps"][1]["description"]
    assert "3. Suma vectorial" in res["setup_steps"][2]["description"]
    assert "4. Sistema de ecuaciones lineales" in res["setup_steps"][3]["description"]
    assert "5. Matriz aumentada" in res["setup_steps"][4]["description"]

    v_step = res["verification_step"]
    assert v_step is not None
    assert v_step["coincide"] is True
    assert r"\checkmark" in v_step["detail_latex"]


def test_combinacion_lineal_coeficientes_fraccionarios():
    """Valida combinación lineal con coeficientes fraccionarios exactos."""
    v1 = Matrix(2, 1, [[2], [0]])
    v2 = Matrix(2, 1, [[0], [3]])
    b = Matrix(2, 1, [[1], [1]])

    resolutor = LinearCombinationSolver()
    res = resolutor.solve(
        b,
        [v1, v2],
        variable_names=["c_1", "c_2"],
        vector_names=["v_1", "v_2"],
    )

    assert res["status"] == "UNIQUE"
    assert res["es_combinacion_lineal"] is True
    assert res["coeficientes"] == [Fraction(1, 2), Fraction(1, 3)]
    assert res["coeficientes_str"] == ["1/2", "1/3"]
    assert res["verification_step"]["coincide"] is True


def test_combinacion_lineal_un_solo_vector():
    """Valida combinación lineal con un único vector (k=1)."""
    v1 = Matrix(3, 1, [[2], [4], [6]])
    b = Matrix(3, 1, [[6], [12], [18]])

    resolutor = LinearCombinationSolver()
    res = resolutor.solve(b, [v1], variable_names=["c_1"], vector_names=["v_1"])

    assert res["status"] == "UNIQUE"
    assert res["es_combinacion_lineal"] is True
    assert res["coeficientes"] == [Fraction(3)]
    assert res["verification_step"]["coincide"] is True


def test_operaciones_vectores_vector_completo():
    """Valida que suma, resta y escalar retornen el vector resultante completo."""
    resolutor = VectorOpsSolver()
    v1 = Matrix(3, 1, [[1], [-2], [5]])
    v2 = Matrix(3, 1, [[3], [4], [-1]])

    res_add = resolutor.add(v1, v2, name1="v_1", name2="v_2")
    assert res_add["status"] == "SUCCESS"
    assert "result_vector_latex" in res_add
    assert res_add["latex_details"][-1] == res_add["result_vector_latex"]

    res_sub = resolutor.subtract(v1, v2, name1="v_1", name2="v_2")
    assert res_sub["status"] == "SUCCESS"
    assert res_sub["latex_details"][-1] == res_sub["result_vector_latex"]

    res_esc = resolutor.scalar_multiply(-3, v1, name="v", result_name="w")
    assert res_esc["status"] == "SUCCESS"
    assert res_esc["latex_details"][-1] == res_esc["result_vector_latex"]
