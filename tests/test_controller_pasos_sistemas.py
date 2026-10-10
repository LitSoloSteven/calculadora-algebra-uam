"""Pruebas para los pasos, serialización y reproductor en Sistemas de Ecuaciones (Fase F4)."""

import json
from fractions import Fraction

import pytest

from src.backend.models.matrix import Matrix
from src.frontend.controllers.linear_systems.controller_gauss import MatrixController
from src.frontend.controllers.linear_systems.controller_gauss_jordan import GaussJordanController
from src.frontend.views.linear_systems._pasos_reproductor import construir_pasos_reproductor


def _resolver_gauss(payload: dict) -> dict:
    return json.loads(MatrixController.process_system(json.dumps(payload)))


def _resolver_gauss_jordan(payload: dict) -> dict:
    return json.loads(GaussJordanController.process_system(json.dumps(payload)))


def test_claves_nuevas_presentes_en_gauss_y_gauss_jordan():
    """Verifica que tanto Gauss como Gauss-Jordan incluyan las claves nuevas requeridas."""
    payload = {
        "matrix_A": [["2", "1", "-1"], ["-3", "-1", "2"], ["-2", "1", "2"]],
        "vector_b": ["8", "-11", "-3"],
        "variables": ["x1", "x2", "x3"],
    }
    for res in (_resolver_gauss(payload), _resolver_gauss_jordan(payload)):
        assert "variables" in res
        assert res["variables"] == ["x1", "x2", "x3"]
        assert "n_vars" in res
        assert res["n_vars"] == 3
        assert "steps_view" in res
        assert isinstance(res["steps_view"], list) and len(res["steps_view"]) > 0
        assert "groups" in res
        assert isinstance(res["groups"], list) and len(res["groups"]) > 0
        assert "stats" in res
        assert isinstance(res["stats"], dict)
        for stat_key in ("total", "pivotes", "intercambios", "eliminaciones", "normalizaciones"):
            assert stat_key in res["stats"]


def test_variables_por_defecto_si_vienen_none():
    """Si variables es None, debe generar x1..xn automáticamente."""
    payload = {
        "matrix_A": [["1", "2"], ["3", "4"]],
        "vector_b": ["5", "6"],
        "variables": None,
    }
    res_g = _resolver_gauss(payload)
    res_gj = _resolver_gauss_jordan(payload)
    assert res_g["variables"] == ["x1", "x2"]
    assert res_gj["variables"] == ["x1", "x2"]


def test_cada_steps_view_reconstruye_con_matrix():
    """Cada elemento de steps_view['matrix'] debe reconstruirse como Matrix exacta."""
    payload = {
        "matrix_A": [["2", "1", "-1"], ["-3", "-1", "2"], ["-2", "1", "2"]],
        "vector_b": ["8", "-11", "-3"],
        "variables": ["x1", "x2", "x3"],
    }
    for res in (_resolver_gauss(payload), _resolver_gauss_jordan(payload)):
        for step in res["steps_view"]:
            mat_dict = step["matrix"]
            assert "rows" in mat_dict
            assert "cols" in mat_dict
            assert "data" in mat_dict
            reconstruida = Matrix(mat_dict["rows"], mat_dict["cols"], mat_dict["data"])
            assert reconstruida.rows == mat_dict["rows"]
            assert reconstruida.cols == mat_dict["cols"]
            assert len(reconstruida.data) == mat_dict["rows"]


def test_kinds_nunca_otro():
    """El tipo de cada paso en steps_view no debe ser nunca 'otro'."""
    payloads = [
        # Sistema estándar 3x3
        {
            "matrix_A": [["2", "1", "-1"], ["-3", "-1", "2"], ["-2", "1", "2"]],
            "vector_b": ["8", "-11", "-3"],
            "variables": ["x1", "x2", "x3"],
        },
        # Sistema 3x3 con pivoteo e intercambio
        {
            "matrix_A": [["0", "2", "1"], ["3", "1", "-1"], ["1", "-1", "2"]],
            "vector_b": ["5", "4", "3"],
            "variables": ["x1", "x2", "x3"],
        },
        # Inconsistente (NO_SOLUTION)
        {
            "matrix_A": [["1", "1"], ["1", "1"]],
            "vector_b": ["1", "2"],
            "variables": ["x1", "x2"],
        },
        # Indeterminado (INFINITE_SOLUTIONS)
        {
            "matrix_A": [["1", "2", "3"], ["2", "4", "6"], ["-1", "-2", "-3"]],
            "vector_b": ["1", "2", "-1"],
            "variables": ["x1", "x2", "x3"],
        },
    ]

    tipos_validos = {"inicial", "intercambio", "pivote", "eliminacion", "normalizacion"}

    for payload in payloads:
        for solver_fn in (_resolver_gauss, _resolver_gauss_jordan):
            res = solver_fn(payload)
            for step in res["steps_view"]:
                kind = step["kind"]
                assert kind != "otro", f"Paso clasificado como 'otro': {step}"
                assert kind in tipos_validos, f"Tipo inesperado: {kind}"


def test_sistema_3x3_con_intercambio():
    """Un sistema 3x3 que fuerza intercambio de filas debe reflejarlo en stats y swap_rows."""
    payload = {
        "matrix_A": [["0", "2", "1"], ["3", "1", "-1"], ["1", "-1", "2"]],
        "vector_b": ["5", "4", "3"],
        "variables": ["x1", "x2", "x3"],
    }
    for res in (_resolver_gauss(payload), _resolver_gauss_jordan(payload)):
        assert res["status"] == "UNIQUE_SOLUTION"
        assert res["stats"]["intercambios"] >= 1
        pasos_intercambio = [s for s in res["steps_view"] if s["kind"] == "intercambio"]
        assert len(pasos_intercambio) >= 1
        primer_swap = pasos_intercambio[0]
        assert primer_swap["swap_rows"] is not None
        assert len(primer_swap["swap_rows"]) == 2
        assert len(primer_swap["rows_changed"]) == 2
        # El título de al menos un grupo de columna debe mencionar intercambio
        grupos_swap = [g for g in res["groups"] if "intercambio" in g["title"]]
        assert len(grupos_swap) >= 1


def test_sistema_10x10_fracciones_denominador_cuatro_digitos():
    """Sistema 10x10 con denominadores de 4 dígitos debe resolverse y reconstruirse sin error."""
    m = 10
    A = [["0"] * m for _ in range(m)]
    b = [f"{i + 1}/1001" for i in range(m)]

    for i in range(m):
        A[i][i] = f"{i + 2}/1001"
        if i + 1 < m:
            A[i][i + 1] = "1/1001"
        if i > 0:
            A[i][i - 1] = "1/1001"

    payload = {
        "matrix_A": A,
        "vector_b": b,
        "variables": [f"x{i+1}" for i in range(m)],
    }

    for solver_fn in (_resolver_gauss, _resolver_gauss_jordan):
        res = solver_fn(payload)
        assert res["status"] == "UNIQUE_SOLUTION"
        assert len(res["steps_view"]) > 0
        for step in res["steps_view"]:
            mat_dict = step["matrix"]
            reconstruida = Matrix(mat_dict["rows"], mat_dict["cols"], mat_dict["data"])
            assert reconstruida.rows == m
            assert reconstruida.cols == m + 1


def test_no_solution_e_infinite_solutions():
    """Sistemas inconsistentes e indeterminados deben incluir steps_view, groups y stats."""
    payload_no_sol = {
        "matrix_A": [["1", "2"], ["2", "4"]],
        "vector_b": ["3", "7"],
        "variables": ["x1", "x2"],
    }
    for solver_fn in (_resolver_gauss, _resolver_gauss_jordan):
        res = solver_fn(payload_no_sol)
        assert res["status"] == "NO_SOLUTION"
        assert len(res["steps_view"]) > 0
        assert len(res["groups"]) > 0
        assert res["stats"]["total"] == len(res["steps_view"])

    payload_inf = {
        "matrix_A": [["1", "2", "3"], ["2", "4", "6"]],
        "vector_b": ["4", "8"],
        "variables": ["x1", "x2", "x3"],
    }
    for solver_fn in (_resolver_gauss, _resolver_gauss_jordan):
        res = solver_fn(payload_inf)
        assert res["status"] == "INFINITE_SOLUTIONS"
        assert len(res["steps_view"]) > 0
        assert len(res["groups"]) > 0
        assert res["stats"]["total"] == len(res["steps_view"])


def test_claves_antiguas_siguen_identicas():
    """Verifica que las claves existentes del contrato conserven valores y estructura."""
    payload = {
        "matrix_A": [["2", "1", "-1"], ["-3", "-1", "2"], ["-2", "1", "2"]],
        "vector_b": ["8", "-11", "-3"],
        "variables": ["x1", "x2", "x3"],
    }

    res_g = _resolver_gauss(payload)
    assert res_g["status"] == "UNIQUE_SOLUTION"
    assert res_g["solution"] == ["2", "3", "-1"]
    assert "intermediate_steps_latex" in res_g
    assert len(res_g["intermediate_steps_latex"]) > 0
    assert "steps_meta" in res_g
    assert len(res_g["steps_meta"]) == len(res_g["intermediate_steps_latex"])
    assert "back_substitution_steps" in res_g
    assert len(res_g["back_substitution_steps"]) > 0
    assert "verification_steps_latex" in res_g
    assert len(res_g["verification_steps_latex"]) > 0

    res_gj = _resolver_gauss_jordan(payload)
    assert res_gj["status"] == "UNIQUE_SOLUTION"
    assert res_gj["solution"] == ["2", "3", "-1"]
    assert "intermediate_steps_latex" in res_gj
    assert len(res_gj["intermediate_steps_latex"]) > 0
    assert "steps_meta" in res_gj
    assert len(res_gj["steps_meta"]) == len(res_gj["intermediate_steps_latex"])
    assert "verification_steps_latex" in res_gj
    assert len(res_gj["verification_steps_latex"]) > 0


def test_pasos_reproductor_genera_grupos_esperados_para_unique_infinite_y_no_solution():
    """_pasos_reproductor debe construir las fases esperadas según el tipo de solución."""
    # 1. UNIQUE SOLUTION
    payload_unique = {
        "matrix_A": [["2", "1", "-1"], ["-3", "-1", "2"], ["-2", "1", "2"]],
        "vector_b": ["8", "-11", "-3"],
        "variables": ["x1", "x2", "x3"],
    }
    res_u_g = _resolver_gauss(payload_unique)
    pasos_g, grupos_g = construir_pasos_reproductor(res_u_g, metodo="gauss")
    assert len(pasos_g) > 0
    assert len(grupos_g) >= 3
    # Gauss debe tener fase de sustitución hacia atrás y comprobación
    titulos_g = [g.titulo for g in grupos_g]
    assert "Sustitución hacia atrás" in titulos_g
    assert "Comprobación Ax = b" in titulos_g
    tipos_pasos_g = {p.tipo for p in pasos_g}
    assert "sustitucion" in tipos_pasos_g
    assert "verificacion" in tipos_pasos_g

    # Gauss-Jordan debe conservar el rótulo "Solución final"
    res_u_gj = _resolver_gauss_jordan(payload_unique)
    pasos_gj, grupos_gj = construir_pasos_reproductor(res_u_gj, metodo="gauss-jordan")
    titulos_gj = [g.titulo for g in grupos_gj]
    assert "Solución final" in titulos_gj
    assert "Comprobación Ax = b" in titulos_gj

    # 2. INFINITE SOLUTIONS (debe tener sustitución/solución final, pero no verificación)
    payload_inf = {
        "matrix_A": [["1", "2", "3"], ["2", "4", "6"]],
        "vector_b": ["4", "8"],
        "variables": ["x1", "x2", "x3"],
    }
    res_inf = _resolver_gauss(payload_inf)
    pasos_inf, grupos_inf = construir_pasos_reproductor(res_inf, metodo="gauss")
    titulos_inf = [g.titulo for g in grupos_inf]
    assert "Sustitución hacia atrás" in titulos_inf
    assert "Comprobación Ax = b" not in titulos_inf

    # 3. NO SOLUTION (solo fases de eliminación; no sustitución ni comprobación)
    payload_no_sol = {
        "matrix_A": [["1", "2"], ["2", "4"]],
        "vector_b": ["3", "7"],
        "variables": ["x1", "x2"],
    }
    res_no = _resolver_gauss(payload_no_sol)
    pasos_no, grupos_no = construir_pasos_reproductor(res_no, metodo="gauss")
    titulos_no = [g.titulo for g in grupos_no]
    assert "Sustitución hacia atrás" not in titulos_no
    assert "Solución final" not in titulos_no
    assert "Comprobación Ax = b" not in titulos_no
    # Todos los pasos de NO_SOLUTION son de eliminación
    assert all(p.tipo in ("inicial", "intercambio", "pivote", "eliminacion", "normalizacion") for p in pasos_no)
