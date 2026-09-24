import sys
import os

# 1. Inyección de ruta maestra: obliga al botón Play a ver la carpeta raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 2. Único bloque de importaciones correctas
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.utils.validators import MatrixValidator
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.vector_ops.operations import VectorOpsSolver

def test_gauss_module():
    print("==================================================")
    print(" PRUEBA DEL MÓDULO BACKEND: ELIMINACIÓN GAUSSIANA ")
    print("==================================================\n")

    raw_data = [
        [ 2.0,  1.0, -1.0,   8.0],
        [-3.0, -1.0,  2.0, -11.0],
        [-2.0,  1.0,  2.0,  -3.0]
    ]

    valid_dim, msg1 = MatrixValidator.validate_dimensions(3, 4)
    valid_data, msg2 = MatrixValidator.validate_matrix_data(raw_data, 3, 4)

    if not (valid_dim and valid_data):
        print(f"Error de validación: {msg1} | {msg2}")
        return

    A_aug = Matrix(3, 4, raw_data)
    print("--- MATRIZ ORIGINAL AUMENTADA ---")
    print(A_aug)

    solver = GaussSolver(A_aug)
    result = solver.solve()

    print("--- PASOS DEL ALGORITMO ---")
    for idx, step in enumerate(result["steps"]):
        print(f"\nPaso {idx + 1}: {step['description']}")
        print(step["matrix"])

    print("--------------------------------------------------")
    print(f"Estado del Sistema: {result['status']}")
    print(f"Mensaje: {result['message']}")
    
    if result["solution"]:
        print("\nSolución encontrada:")
        for i, val in enumerate(result["solution"]):
            print(f"  x{i+1} = {val}")

def run_fraction_test():
    raw_data_with_strings = [
        [ "2",     "1/3",  "-1",   "8"   ],
        [ "-3/2",  "-1",   "2",    "-11" ],
        [ "-2",    "1",    "2/5",  "-3"  ]
    ]

    print("\n--- PARSEANDO ENTRADAS CON FRACCIONES ---")
    valid, parsed_data, msg = MatrixValidator.validate_and_parse_raw_matrix(raw_data_with_strings, 3, 4)
    
    if not valid:
        print(f"Error de validación: {msg}")
        return

    print("Matriz parseada con éxito.")
    matrix = Matrix(3, 4, parsed_data)
    solver = GaussSolver(matrix)
    result = solver.solve()

    print("\n--- PASOS DEL ALGORITMO ---")
    for step in result["steps"]:
        print(f"\n-> {step['description']}")
        print(step["matrix"])


def test_linear_combination_canonical_flow():
    """Valida el ejemplo canónico de Lay (R³) y el nuevo flujo pedagógico."""
    print("\n==================================================")
    print(" PRUEBA COMBINACIÓN LINEAL: EJEMPLO CANÓNICO LAY  ")
    print("==================================================")

    # a_1 = [1, -2, -5]^T, a_2 = [2, 5, 6]^T, b = [7, 4, -3]^T
    a1 = Matrix(3, 1, [[1], [-2], [-5]])
    a2 = Matrix(3, 1, [[2], [5], [6]])
    b = Matrix(3, 1, [[7], [4], [-3]])

    solver = VectorOpsSolver()
    res = solver.is_linear_combination(
        b, [a1, a2],
        variable_names=["x_1", "x_2"],
        vector_names=["a_1", "a_2"],
    )

    print(f"Estado: {res['status']}")
    print(f"Mensaje: {res['message']}")
    print(f"Coeficientes: {res['coeficientes']}")

    # 1. Validación de Status y Coeficientes Exactos (x_1 = 3, x_2 = 2)
    assert res["status"] == "UNIQUE", f"Se esperaba UNIQUE, obtenido {res['status']}"
    assert res["es_combinacion_lineal"] is True
    assert res["coeficientes"] == [Fraction(3), Fraction(2)]
    assert res["coeficientes_str"] == ["3", "2"]

    # 2. Validación de setup_steps (5 pasos completos)
    setup = res["setup_steps"]
    assert len(setup) == 5, f"Se esperaban 5 setup_steps, obtenidos {len(setup)}"
    print("\n--- PASOS DE PLANTEAMIENTO PREVIO (setup_steps) ---")
    for s in setup:
        print(f"{s['description']}")
        print(f"  $$ {s['detail_latex']} $$\n")

    assert "1. Ecuación vectorial" in setup[0]["description"]
    assert "2. Multiplicación de los escalares" in setup[1]["description"]
    assert "3. Suma vectorial" in setup[2]["description"]
    assert "4. Sistema de ecuaciones lineales" in setup[3]["description"]
    assert "5. Matriz aumentada" in setup[4]["description"]

    # Verificación de contenidos LaTeX esperados en los setup_steps
    assert r"\begin{bmatrix} 1 \\ -2 \\ -5 \end{bmatrix}" in setup[0]["detail_latex"]
    assert r"\begin{bmatrix} 2 \\ 5 \\ 6 \end{bmatrix}" in setup[0]["detail_latex"]
    assert r"\begin{bmatrix} 7 \\ 4 \\ -3 \end{bmatrix}" in setup[0]["detail_latex"]
    assert r"\begin{cases}" in setup[3]["detail_latex"]
    assert r"array}{cc|c}" in setup[4]["detail_latex"]

    # 3. Validación de verification_step formal
    v_step = res["verification_step"]
    assert v_step is not None
    assert v_step["coincide"] is True
    print("--- VERIFICACIÓN FORMAL ---")
    print(f"Descripción: {v_step['description']}")
    print(f"Fórmula: {v_step['formula_latex']}")
    print(f"Sustitución: {v_step['substitution_latex']}")
    print(f"Evaluado: {v_step['evaluated_vector_latex']}")
    print(f"Comparación: {v_step['comparison_latex']}")
    print(f"Detalle unificado: {v_step['detail_latex']}")

    # Validación de detalle unificado requerido:
    assert r"\mathbf{y} = 3\mathbf{a}_1 + 2\mathbf{a}_2" in v_step["detail_latex"]
    assert r"\begin{bmatrix} 7 \\ 4 \\ -3 \end{bmatrix} = \mathbf{b}" in v_step["detail_latex"]
    assert r"\checkmark" in v_step["detail_latex"]

    # 4. Validación de Unificación de Pasos y Eliminación de Paso 0
    all_steps = res["steps"]
    gauss_steps = res["gauss_steps"]
    assert len(all_steps) == len(setup) + len(gauss_steps), (
        f"all_steps ({len(all_steps)}) debe ser la suma de setup ({len(setup)}) + gauss ({len(gauss_steps)})"
    )
    for idx, s in enumerate(all_steps, start=1):
        assert s["step_number"] == idx, f"Paso {idx} tiene step_number {s['step_number']}"
        assert "Paso 0" not in s["description"], f"Paso {idx} contiene 'Paso 0'!"
        assert not s["description"].startswith("0."), f"Paso {idx} comienza con '0.'!"

    # Asegurar que el primer paso redundante de Gauss ('Matriz inicial aumentada') no esté en gauss_steps
    for gs in gauss_steps:
        assert "Matriz inicial aumentada" not in gs["description"]

    # 5. Caso NO_SOLUTION preserva los 5 setup_steps
    b_incompatible = Matrix(3, 1, [[1], [1], [100]])
    res_no = solver.is_linear_combination(
        b_incompatible, [a1, a2],
        variable_names=["x_1", "x_2"],
        vector_names=["a_1", "a_2"],
    )
    assert res_no["status"] == "NO_SOLUTION"
    assert len(res_no["setup_steps"]) == 5
    assert res_no["verification_step"] is None

    # 6. Caso de ERROR temprano devuelve setup_steps = []
    res_err = solver.is_linear_combination(b, [])
    assert res_err["status"] == "ERROR"
    assert res_err["setup_steps"] == []

    print("\n>>> ¡TODAS LAS VALIDACIONES DE COMBINACIÓN LINEAL PASARON CON ÉXITO! <<<")


def test_linear_combination_fraction_coefficients():
    """Valida combinación lineal con coeficientes fraccionarios exactos (1/2, 1/3)."""
    print("\n==================================================")
    print(" PRUEBA COMBINACIÓN LINEAL: COEFICIENTES EXACTOS  ")
    print("==================================================")

    v1 = Matrix(2, 1, [[2], [0]])
    v2 = Matrix(2, 1, [[0], [3]])
    b = Matrix(2, 1, [[1], [1]])

    solver = VectorOpsSolver()
    res = solver.is_linear_combination(
        b, [v1, v2],
        variable_names=["c_1", "c_2"],
        vector_names=["v_1", "v_2"],
    )

    assert res["status"] == "UNIQUE"
    assert res["es_combinacion_lineal"] is True
    assert res["coeficientes"] == [Fraction(1, 2), Fraction(1, 3)]
    assert res["coeficientes_str"] == ["1/2", "1/3"]

    setup = res["setup_steps"]
    assert len(setup) == 5
    for s in setup:
        assert "0.333" not in s["detail_latex"]
        assert "0.500" not in s["detail_latex"]

    v_step = res["verification_step"]
    assert v_step is not None
    assert v_step["coincide"] is True
    assert "0.333" not in v_step["detail_latex"]
    assert "0.333" not in v_step["description"]
    assert r"\frac{1}{2}\mathbf{v}_1 + \frac{1}{3}\mathbf{v}_2" in v_step["detail_latex"]
    assert r"\left(\frac{1}{2}\right)" in v_step["substitution_latex"]
    assert r"\left(\frac{1}{3}\right)" in v_step["substitution_latex"]
    assert r"\checkmark" in v_step["detail_latex"]

    print(">>> ¡Validación con coeficientes fraccionarios exactos exitosa!")


def test_linear_combination_single_vector():
    """Valida combinación lineal con un único vector (k=1) y su descripción pedagógica."""
    print("\n==================================================")
    print(" PRUEBA COMBINACIÓN LINEAL: UN SOLO VECTOR (k=1)  ")
    print("==================================================")

    v1 = Matrix(3, 1, [[2], [4], [6]])
    b = Matrix(3, 1, [[6], [12], [18]])

    solver = VectorOpsSolver()
    res = solver.is_linear_combination(b, [v1], variable_names=["c_1"], vector_names=["v_1"])

    assert res["status"] == "UNIQUE"
    assert res["es_combinacion_lineal"] is True
    assert res["coeficientes"] == [Fraction(3)]

    setup = res["setup_steps"]
    assert len(setup) == 5
    assert "3. Igualdad vectorial componente a componente (un solo vector):" == setup[2]["description"]

    v_step = res["verification_step"]
    assert v_step is not None
    assert v_step["coincide"] is True
    assert r"\checkmark" in v_step["detail_latex"]

    print(">>> ¡Validación con un solo vector (k=1) exitosa!")


def test_vector_ops_add_subtract_scalar_full_vector():
    """Valida que Suma, Resta y Escalar muestren el vector resultante completo en latex_details[-1] y result_vector_latex."""
    print("\n==================================================")
    print(" PRUEBA VECTOR OPS: VECTOR COMPLETO EN RESULTADO  ")
    print("==================================================")

    solver = VectorOpsSolver()
    v1 = Matrix(3, 1, [[1], [-2], [5]])
    v2 = Matrix(3, 1, [[3], [4], [-1]])

    # 1. Suma
    res_add = solver.add(v1, v2, name1="v_1", name2="v_2")
    assert res_add["status"] == "SUCCESS"
    assert "result_vector_latex" in res_add
    assert "result_matrix_latex" in res_add
    # latex_details[-1] debe ser el vector resultante completo, no solo la última componente
    assert res_add["latex_details"][-1] == res_add["result_vector_latex"]
    assert r"\mathbf{w} =" in res_add["result_vector_latex"]
    assert r"\begin{bmatrix} 4 \\ 2 \\ 4 \end{bmatrix}" in res_add["result_vector_latex"]
    # Debe contener los cálculos fila por fila anteriores (3 filas + 1 vector completo = 4 entradas)
    assert len(res_add["latex_details"]) == 4
    assert res_add["latex_details"][0].startswith("w_{1}")
    assert res_add["latex_details"][1].startswith("w_{2}")
    assert res_add["latex_details"][2].startswith("w_{3}")

    # 2. Resta
    res_sub = solver.subtract(v1, v2, name1="v_1", name2="v_2")
    assert res_sub["status"] == "SUCCESS"
    assert "result_vector_latex" in res_sub
    assert res_sub["latex_details"][-1] == res_sub["result_vector_latex"]
    assert r"\mathbf{w} =" in res_sub["result_vector_latex"]
    assert r"\begin{bmatrix} -2 \\ -6 \\ 6 \end{bmatrix}" in res_sub["result_vector_latex"]

    # 3. Multiplicación Escalar
    res_esc = solver.scalar_multiply(-3, v1, name="v", result_name="w")
    assert res_esc["status"] == "SUCCESS"
    assert "result_vector_latex" in res_esc
    assert res_esc["latex_details"][-1] == res_esc["result_vector_latex"]
    assert r"\mathbf{w} =" in res_esc["result_vector_latex"]
    assert r"\begin{bmatrix} -3 \\ 6 \\ -15 \end{bmatrix}" in res_esc["result_vector_latex"]
    assert len(res_esc["latex_details"]) == 4

    print(">>> ¡Validación de vector completo en Suma, Resta y Escalar exitosa!")


if __name__ == "__main__":
    test_gauss_module()
    run_fraction_test()
    test_linear_combination_canonical_flow()
    test_linear_combination_fraction_coefficients()
    test_linear_combination_single_vector()
    test_vector_ops_add_subtract_scalar_full_vector()