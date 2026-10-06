"""F9 Break-UI y rendimiento (Catálogo de la Sección 6).

Pruebas sin navegador que verifican robustez ante casos límite, entradas
maliciosas o extremas, y tiempos de respuesta dentro del presupuesto con
holgura mínima de 10x.
"""
import json
import time
from fractions import Fraction

from src.backend.utils.validators import MatrixValidator
from src.frontend.controllers.geometry.controller_geometry import GeometryController
from src.frontend.controllers.inverse_ops.controller_inverse_ops import InverseOpsController
from src.frontend.controllers.linear_systems.controller_gauss import MatrixController
from src.frontend.controllers.linear_systems.controller_gauss_jordan import GaussJordanController
from src.frontend.controllers.vector_ops.controller_vector_ops import VectorOpsController
from src.backend.solvers.numeric_systems.roman_calculator import RomanCalculator, RomanNumeralError
from src.backend.solvers.numeric_systems.conversor_bases import ConversorBases
from src.frontend.components.glosa_render import render_glosa_text


# ============================================================================
# Celdas extremas / inválidas
# ============================================================================

def test_cell_extreme_and_invalid_inputs():
    """Valida celdas extremas y anómalas sin lanzar excepciones no controladas."""
    cases = [
        ("1001/1000", True),
        ("-123456789012/987654321", True),
        ("0.0000001", True),
        ("1/0", False),
        ("abc", False),
        ("", False),
    ]

    for val_str, should_be_valid in cases:
        t0 = time.perf_counter()
        ok, parsed, err_msg = MatrixValidator.parse_number_exact(val_str)
        dur = time.perf_counter() - t0

        # Presupuesto: parseo < 50ms (holgura 10x sobre < 1ms)
        assert dur < 0.05
        assert ok is should_be_valid
        assert isinstance(parsed, Fraction)
        assert "Traceback" not in err_msg
        if not ok:
            assert len(err_msg) > 0


# ============================================================================
# GeometryController (los 3 procesos)
# ============================================================================

def test_geometry_controller_all_three_processes():
    """Verifica los 3 procesos de GeometryController sin lanzar excepción y con status coherente."""
    # 1. process_lines_planes
    p_lines = json.dumps({
        "matrix_A": [["1", "2"], ["3", "4"]],
        "vector_b": ["5", "6"]
    })
    t0 = time.perf_counter()
    r_lines = GeometryController.process_lines_planes(p_lines)
    dur_lines = time.perf_counter() - t0
    assert dur_lines < 1.0  # holgura 10x sobre ~10ms
    assert r_lines.get("status") == "OK"
    assert "Traceback" not in r_lines.get("message", "")
    json.dumps(r_lines)  # JSON serializable

    # 2. process_vectors
    p_vecs = json.dumps({
        "vectors": [
            {"data": ["1", "2"], "orientation": "column"},
            {"data": ["3", "4"], "orientation": "column"}
        ]
    })
    t0 = time.perf_counter()
    r_vecs = GeometryController.process_vectors(p_vecs)
    dur_vecs = time.perf_counter() - t0
    assert dur_vecs < 1.0
    assert r_vecs.get("status") == "OK"
    assert "Traceback" not in r_vecs.get("message", "")
    json.dumps(r_vecs)

    # 3. process_combination
    p_comb = json.dumps({
        "b": {"data": ["5", "6"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"}
        ]
    })
    t0 = time.perf_counter()
    r_comb = GeometryController.process_combination(p_comb)
    dur_comb = time.perf_counter() - t0
    assert dur_comb < 1.0
    assert r_comb.get("status") == "OK"
    assert "Traceback" not in r_comb.get("message", "")
    json.dumps(r_comb)


# ============================================================================
# InverseOpsController 50x50
# ============================================================================

def test_inverse_ops_controller_50x50_identity():
    """50x50 identidad con fracciones no lanza excepción y retorna status coherente."""
    n = 50
    mat_ident = [[("1/2" if i == j else "0") for j in range(n)] for i in range(n)]
    payload = json.dumps({"n": n, "data": mat_ident})

    t0 = time.perf_counter()
    res = InverseOpsController.process_inverse(payload)
    dur = time.perf_counter() - t0

    # Medido ~2.7s; holgura 10x => < 30s
    assert dur < 30.0
    assert res.get("status") == "SUCCESS"
    assert "Traceback" not in res.get("message", "")
    assert res.get("n") == 50


def test_inverse_ops_controller_50x50_singular():
    """50x50 singular con fila duplicada se detecta rápidamente sin excepción."""
    n = 50
    mat_sing = [[("1" if i == j else "0") for j in range(n)] for i in range(n)]
    mat_sing[1] = list(mat_sing[0])
    payload = json.dumps({"n": n, "data": mat_sing})

    t0 = time.perf_counter()
    res = InverseOpsController.process_inverse(payload)
    dur = time.perf_counter() - t0

    # Medido ~0.005s; holgura 10x => < 0.5s
    assert dur < 0.5
    assert res.get("status") == "SINGULAR"
    assert "Traceback" not in res.get("message", "")
    assert res.get("n") == 50


# ============================================================================
# Sistemas 10x10 inconsistente, 1x1 y 10x1 (MatrixController y GaussJordanController)
# ============================================================================

def test_linear_systems_10x10_inconsistent():
    """10x10 inconsistente para Gauss y Gauss-Jordan."""
    mat_10 = [["1" if i == j else "0" for j in range(10)] for i in range(10)]
    mat_10[9] = ["0"] * 10
    b_10 = ["1"] * 9 + ["5"]
    payload = json.dumps({"matrix_A": mat_10, "vector_b": b_10})

    t0 = time.perf_counter()
    res_gauss = json.loads(MatrixController.process_system(payload))
    dur_gauss = time.perf_counter() - t0
    assert dur_gauss < 1.0
    assert res_gauss.get("status") == "NO_SOLUTION"
    assert "Traceback" not in res_gauss.get("message", "")

    t0 = time.perf_counter()
    res_gj = json.loads(GaussJordanController.process_system(payload))
    dur_gj = time.perf_counter() - t0
    assert dur_gj < 1.0
    assert res_gj.get("status") == "NO_SOLUTION"
    assert "Traceback" not in res_gj.get("message", "")


def test_linear_systems_1x1():
    """Sistema 1x1 con solución única."""
    payload = json.dumps({"matrix_A": [["2"]], "vector_b": ["6"]})

    t0 = time.perf_counter()
    res_gauss = json.loads(MatrixController.process_system(payload))
    dur_gauss = time.perf_counter() - t0
    assert dur_gauss < 0.5
    assert res_gauss.get("status") == "UNIQUE_SOLUTION"
    assert res_gauss.get("solution") == ["3"]

    t0 = time.perf_counter()
    res_gj = json.loads(GaussJordanController.process_system(payload))
    dur_gj = time.perf_counter() - t0
    assert dur_gj < 0.5
    assert res_gj.get("status") == "UNIQUE_SOLUTION"
    assert res_gj.get("solution") == ["3"]


def test_linear_systems_10x1():
    """Sistema 10 ecuaciones con 1 variable compatible."""
    mat = [[str(i + 1)] for i in range(10)]
    b = [str((i + 1) * 2) for i in range(10)]
    payload = json.dumps({"matrix_A": mat, "vector_b": b})

    t0 = time.perf_counter()
    res_gauss = json.loads(MatrixController.process_system(payload))
    dur_gauss = time.perf_counter() - t0
    assert dur_gauss < 0.5
    assert res_gauss.get("status") == "UNIQUE_SOLUTION"
    assert res_gauss.get("solution") == ["2"]

    t0 = time.perf_counter()
    res_gj = json.loads(GaussJordanController.process_system(payload))
    dur_gj = time.perf_counter() - t0
    assert dur_gj < 0.5
    assert res_gj.get("status") == "UNIQUE_SOLUTION"
    assert res_gj.get("solution") == ["2"]


# ============================================================================
# VectorOpsController: combinacion lineal dim 10 con 9 vectores
# ============================================================================

def test_vector_ops_combination_dim10_9vecs():
    """Combinación lineal con b de dimensión 10 y 9 vectores columna."""
    b_v = {"data": [str(i + 1) for i in range(10)], "orientation": "column"}
    vectors_9 = [
        {"data": [("1" if i == j else "0") for i in range(10)], "orientation": "column"}
        for j in range(9)
    ]
    payload = json.dumps({"b": b_v, "vectors": vectors_9})

    t0 = time.perf_counter()
    res = json.loads(VectorOpsController.process_linear_combination(payload))
    dur = time.perf_counter() - t0

    assert dur < 2.0  # holgura 10x sobre ~30ms
    assert res.get("status") in ("INCONSISTENT", "NO_SOLUTION", "UNIQUE", "INFINITE")
    assert "Traceback" not in res.get("message", "")


# ============================================================================
# RomanCalculator: "MMMCMXCIX + I" y "V − V"
# ============================================================================

def test_roman_calculator_overflow_and_zero():
    """Verifica manejo controlado de suma > 3999 y resta = 0 en números romanos."""
    t0 = time.perf_counter()
    try:
        RomanCalculator.sumar("MMMCMXCIX", "I")
        sum_error = None
    except RomanNumeralError as e:
        sum_error = str(e)
    dur_sum = time.perf_counter() - t0
    assert dur_sum < 0.1
    assert sum_error is not None
    assert "Traceback" not in sum_error
    assert "3999" in sum_error or "rango" in sum_error.lower() or "máximo" in sum_error.lower()

    t0 = time.perf_counter()
    try:
        RomanCalculator.restar("V", "V")
        sub_error = None
    except RomanNumeralError as e:
        sub_error = str(e)
    dur_sub = time.perf_counter() - t0
    assert dur_sub < 0.1
    assert sub_error is not None
    assert "Traceback" not in sub_error
    assert "cero" in sub_error.lower() or "cero" in sub_error


# ============================================================================
# ConversorBases: 200 bits, negativos y prefijo 0x
# ============================================================================

def test_conversor_bases_large_and_prefixes():
    """Conversor maneja enteros de 200 bits, negativos y prefijo 0x."""
    conv = ConversorBases()

    # Entero de 200 bits
    big_val = str(2 ** 200 - 1)
    t0 = time.perf_counter()
    r_big = conv.decimal_a_todo(big_val)
    dur_big = time.perf_counter() - t0
    assert dur_big < 0.5
    assert "error" not in r_big
    assert len(r_big["binario"]) == 200
    assert "Traceback" not in str(r_big)

    # Negativo
    t0 = time.perf_counter()
    r_neg = conv.decimal_a_todo("-12345678901234567890")
    dur_neg = time.perf_counter() - t0
    assert dur_neg < 0.5
    assert "error" not in r_neg
    assert r_neg["decimal"].startswith("-")

    # Prefijo 0x
    t0 = time.perf_counter()
    r_hex = conv.hexadecimal_a_todo("0x1A2B3C")
    dur_hex = time.perf_counter() - t0
    assert dur_hex < 0.5
    assert "error" not in r_hex
    assert r_hex["hexadecimal"] == "1A2B3C"


# ============================================================================
# Chat: render_glosa_text
# ============================================================================

def test_render_glosa_text_edge_cases():
    """Chat render_glosa_text con 3000 chars, 200 chars sin espacios, XSS y matriz 12x12."""
    long_text = "a" * 3000
    no_space_text = "x" * 200
    xss_payload = '<script>alert("xss")</script><img src="x" onerror="evil()">'
    matrix_code = "```\n" + "\n".join(" ".join(f"{i*12+j:3d}" for j in range(12)) for i in range(12)) + "\n```"

    combined = f"{long_text}\n\n{no_space_text}\n\n{xss_payload}\n\n{matrix_code}"

    t0 = time.perf_counter()
    html_out = render_glosa_text(combined)
    dur = time.perf_counter() - t0

    assert dur < 0.1  # holgura 10x sobre ~1ms
    # XSS mitigado
    assert "<script" not in html_out
    assert "<img" not in html_out
    assert "&lt;script" in html_out
    assert "&lt;img" in html_out
    # Bloque de código preservado
    assert '<pre class="glosa-pre"><code>' in html_out
    assert 'overflow-wrap: anywhere;' in html_out
