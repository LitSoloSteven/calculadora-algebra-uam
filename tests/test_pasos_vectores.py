"""Pruebas del reproductor de pasos y agrupación didáctica para Operaciones con Vectores."""

import ast
import json
import re
from pathlib import Path
from fractions import Fraction
import pytest

from src.backend.models.matrix import Matrix
from src.backend.solvers.vector_ops.operations import VectorOpsSolver
from src.frontend.controllers.vector_ops.controller_vector_ops import VectorOpsController
from src.frontend.views.vector_ops._pasos_reproductor import (
    construir_pasos_combinacion_lineal,
    construir_pasos_vector_basico,
)


def test_basic_ops_generate_expected_steps_sequence():
    """Suma, resta y multiplicación escalar generan secuencia [inicial, componentes..., resultado]."""
    v1 = Matrix(3, 1, [[1], [2], [3]])
    v2 = Matrix(3, 1, [[4], [5], [6]])

    # 1. Suma
    res_add = VectorOpsSolver().add(v1, v2)
    pasos_add, grupos_add = construir_pasos_vector_basico(res_add)
    tipos_add = [p.tipo for p in pasos_add]
    assert tipos_add == ["inicial", "componente", "componente", "componente", "resultado"]
    assert [p.etiqueta_tipo for p in pasos_add] == ["Inicial", "Componente", "Componente", "Componente", "Resultado"]
    assert len(grupos_add) == 1
    assert pasos_add[-1].meta_explicar["kind"] == "resultado"

    # 2. Resta
    res_sub = VectorOpsSolver().subtract(v1, v2)
    pasos_sub, grupos_sub = construir_pasos_vector_basico(res_sub)
    tipos_sub = [p.tipo for p in pasos_sub]
    assert tipos_sub == ["inicial", "componente", "componente", "componente", "resultado"]

    # 3. Escalar
    res_scal = VectorOpsSolver().scalar_multiply(2, v1)
    pasos_scal, grupos_scal = construir_pasos_vector_basico(res_scal)
    tipos_scal = [p.tipo for p in pasos_scal]
    assert tipos_scal == ["inicial", "componente", "componente", "componente", "resultado"]


def test_row_plus_column_sum_includes_ajuste_step():
    """La suma fila + columna incluye explícitamente el paso de ajuste de orientación."""
    v1_col = Matrix(2, 1, [[3], [1]])
    v2_row = Matrix(1, 2, [[2, 4]])

    res = VectorOpsSolver().add(v1_col, v2_row, strict=False)
    pasos, grupos = construir_pasos_vector_basico(res)
    tipos = [p.tipo for p in pasos]

    assert tipos == ["inicial", "ajuste", "componente", "componente", "resultado"]
    assert pasos[1].tipo == "ajuste"
    assert pasos[1].etiqueta_tipo == "Ajuste"
    assert "orientación" in pasos[1].descripcion.lower()


def test_linear_combination_groups_by_status():
    """Combinación lineal UNIQUE tiene 4 grupos, INFINITE no tiene comprobación, NO_SOLUTION sin sustitución ni comprobación."""
    # 1. UNIQUE
    payload_unique = json.dumps({
        "b": {"orientation": "column", "data": ["3", "2"]},
        "vectors": [
            {"orientation": "column", "data": ["1", "0"]},
            {"orientation": "column", "data": ["0", "1"]},
        ]
    })
    res_u = json.loads(VectorOpsController.process_linear_combination(payload_unique))
    assert res_u["status"] == "UNIQUE"
    pasos_u, grupos_u = construir_pasos_combinacion_lineal(res_u)
    assert len(grupos_u) == 4
    titulos_u = [g.titulo for g in grupos_u]
    assert titulos_u == [
        "Planteamiento algebraico",
        "Eliminación gaussiana",
        "Sustitución hacia atrás",
        "Comprobación",
    ]
    assert [g.tipo for g in grupos_u] == ["planteamiento", "eliminacion", "sustitucion", "verificacion"]

    # 2. INFINITE
    payload_infinite = json.dumps({
        "b": {"orientation": "column", "data": ["3", "6"]},
        "vectors": [
            {"orientation": "column", "data": ["1", "2"]},
            {"orientation": "column", "data": ["2", "4"]},
        ]
    })
    res_i = json.loads(VectorOpsController.process_linear_combination(payload_infinite))
    assert res_i["status"] == "INFINITE"
    pasos_i, grupos_i = construir_pasos_combinacion_lineal(res_i)
    assert len(grupos_i) == 3
    assert [g.titulo for g in grupos_i] == [
        "Planteamiento algebraico",
        "Eliminación gaussiana",
        "Sustitución hacia atrás",
    ]
    assert not any(g.tipo == "verificacion" for g in grupos_i)
    assert res_i.get("verification_step") is None

    # 3. NO_SOLUTION
    payload_no_sol = json.dumps({
        "b": {"orientation": "column", "data": ["0", "1"]},
        "vectors": [
            {"orientation": "column", "data": ["1", "0"]},
            {"orientation": "column", "data": ["2", "0"]},
        ]
    })
    res_n = json.loads(VectorOpsController.process_linear_combination(payload_no_sol))
    assert res_n["status"] == "NO_SOLUTION"
    pasos_n, grupos_n = construir_pasos_combinacion_lineal(res_n)
    assert len(grupos_n) == 2
    assert [g.titulo for g in grupos_n] == [
        "Planteamiento algebraico",
        "Eliminación gaussiana",
    ]
    assert not any(g.tipo in ("sustitucion", "verificacion") for g in grupos_n)


def test_steps_view_reconstructs_with_matrix():
    """Cada paso de steps_view serializa y reconstruye su matriz usando Matrix."""
    payload = json.dumps({
        "b": {"orientation": "column", "data": ["7", "4", "-3"]},
        "vectors": [
            {"orientation": "column", "data": ["1", "-2", "-5"]},
            {"orientation": "column", "data": ["2", "5", "6"]},
        ]
    })
    res = json.loads(VectorOpsController.process_linear_combination(payload))
    steps_view = res.get("steps_view", [])
    assert len(steps_view) > 0

    for s in steps_view:
        mat_dict = s["matrix"]
        assert isinstance(mat_dict, dict)
        assert "rows" in mat_dict and "cols" in mat_dict and "data" in mat_dict
        reconstructed = Matrix(mat_dict["rows"], mat_dict["cols"], mat_dict["data"])
        assert reconstructed.rows == mat_dict["rows"]
        assert reconstructed.cols == mat_dict["cols"]


def test_dimension_10_with_9_vectors_no_error():
    """Dimensión 10 con 9 vectores ejecuta sin error y genera pasos de reproductor."""
    vectors_data = [
        {"orientation": "column", "data": [("1" if r == c else "0") for r in range(10)]}
        for c in range(9)
    ]
    b_data = {"orientation": "column", "data": [str(r + 1) for r in range(10)]}
    payload = json.dumps({"b": b_data, "vectors": vectors_data})

    res_str = VectorOpsController.process_linear_combination(payload)
    res = json.loads(res_str)

    assert res["status"] in ("UNIQUE", "INFINITE", "NO_SOLUTION")
    assert res["n_vars"] == 9
    assert len(res["variables"]) == 9
    pasos, grupos = construir_pasos_combinacion_lineal(res)
    assert len(pasos) > 0
    assert len(grupos) >= 2


def test_legacy_keys_preserved_in_controller():
    """Verifica que las claves existentes en la salida del controller se preservan intactas."""
    payload = json.dumps({
        "b": {"orientation": "column", "data": ["1", "1"]},
        "vectors": [
            {"orientation": "column", "data": ["1", "0"]},
            {"orientation": "column", "data": ["0", "1"]},
        ]
    })
    res = json.loads(VectorOpsController.process_linear_combination(payload))

    required_keys = [
        "status", "es_combinacion_lineal", "coeficientes_str",
        "setup_steps", "gauss_steps", "steps", "steps_meta",
        "back_substitution_steps", "verification_step",
        "variables", "n_vars", "steps_view", "groups", "stats"
    ]
    for key in required_keys:
        assert key in res, f"Clave esperada faltante: {key}"

    assert len(res["setup_steps"]) == 5
    assert res["verification_step"] is not None
    assert "formula_latex" in res["verification_step"]


def test_no_forbidden_strings_nor_voseo():
    """Verifica que los módulos nuevos no contienen —, Oops ni voseo."""
    files_to_check = [
        Path("src/frontend/views/vector_ops/_pasos_reproductor.py"),
        Path("src/frontend/views/vector_ops/steps_mixin.py"),
        Path("src/frontend/views/vector_ops/results_mixin.py"),
        Path("src/frontend/controllers/vector_ops/controller_vector_ops.py"),
    ]

    voseo_pattern = re.compile(
        r"\b(ingresá|añadí|escribí|presioná|pegá|sumá|calculá|mostrá|revisá)\b",
        re.IGNORECASE,
    )

    for p in files_to_check:
        assert p.exists()
        text = p.read_text(encoding="utf-8")
        assert "—" not in text, f"Em-dash encontrado en {p}"
        assert "Oops" not in text, f"Oops encontrado en {p}"

        tree = ast.parse(text, filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value
                match = voseo_pattern.search(s)
                assert match is None, f"Voseo '{match.group(0)}' en {p}: {s}"
