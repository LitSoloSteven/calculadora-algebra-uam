"""Pruebas para el adaptador del reproductor de pasos en operaciones de matrices (Fase F5)."""

import json
import re

import pytest

from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixOpsController
from src.frontend.views.matrix_ops._pasos_reproductor import construir_pasos_matrices


def _evaluar(expresion: str, matrices: dict) -> dict:
    """Evalúa la expresión matricial con el controlador y devuelve el dict deserializado."""
    return json.loads(MatrixOpsController.process_expression(expresion, json.dumps(matrices)))


def test_expresion_compleja_produce_pasos_con_etiquetas_y_grupo_por_suboperacion():
    """'2A - B(C - D^T)' produce pasos con tipo 'operacion', etiquetas correctas y un grupo por suboperación."""
    matrices = {
        "A": {"rows": 2, "cols": 2, "data": [["1", "2"], ["3", "4"]]},
        "B": {"rows": 2, "cols": 2, "data": [["2", "0"], ["1", "3"]]},
        "C": {"rows": 2, "cols": 2, "data": [["5", "1"], ["2", "4"]]},
        "D": {"rows": 2, "cols": 2, "data": [["1", "-1"], ["0", "2"]]},
    }
    res = _evaluar("2A - B(C - D^T)", matrices)
    assert res["status"] == "SUCCESS"
    assert len(res.get("segment_steps", [])) > 1

    pasos, grupos = construir_pasos_matrices(res)
    assert len(pasos) == len(res["segment_steps"])
    assert len(grupos) == len(pasos)

    etiquetas_validas = {
        "Suma",
        "Resta",
        "Multiplicación de Matrices",
        "Multiplicación Escalar",
        "Transposición",
        "Negación",
    }

    for i, paso in enumerate(pasos):
        assert paso.tipo == "operacion"
        assert paso.etiqueta_tipo in etiquetas_validas
        assert paso.indice == i
        assert paso.indice_grupo == i
        assert paso.meta_explicar is not None
        assert paso.meta_explicar["index"] == i + 1
        assert paso.meta_explicar["total"] == len(pasos)
        assert paso.meta_explicar["kind"] == "otro"
        assert paso.cuerpo == res["segment_steps"][i]

    for i, grupo in enumerate(grupos):
        assert grupo.tipo == "operacion"
        assert grupo.indices_pasos == (i,)
        assert grupo.titulo == pasos[i].descripcion
        assert grupo.resumen == "1 operación"


def test_expresion_de_una_sola_operacion_produce_un_paso_y_un_grupo():
    """Una expresión con una sola suboperación genera un único paso y un único grupo."""
    matrices = {
        "A": {"rows": 2, "cols": 2, "data": [["1", "0"], ["0", "1"]]},
        "B": {"rows": 2, "cols": 2, "data": [["2", "3"], ["4", "5"]]},
    }
    res = _evaluar("A + B", matrices)
    assert res["status"] == "SUCCESS"
    assert len(res.get("segment_steps", [])) == 1

    pasos, grupos = construir_pasos_matrices(res)
    assert len(pasos) == 1
    assert len(grupos) == 1

    paso = pasos[0]
    assert paso.tipo == "operacion"
    assert paso.etiqueta_tipo == "Suma"
    assert paso.indice == 0
    assert paso.indice_grupo == 0

    grupo = grupos[0]
    assert grupo.titulo == "Operaciones de la expresión"
    assert grupo.resumen == "1 operación"
    assert grupo.tipo == "operacion"
    assert grupo.indices_pasos == (0,)


def test_transposicion_sin_cell_by_cell_steps():
    """La transposición no incluye desglose celda a celda."""
    matrices = {
        "A": {"rows": 2, "cols": 3, "data": [["1", "2", "3"], ["4", "5", "6"]]},
    }
    res = _evaluar("A^T", matrices)
    assert res["status"] == "SUCCESS"

    pasos, grupos = construir_pasos_matrices(res)
    assert len(pasos) == 1
    paso = pasos[0]
    assert paso.etiqueta_tipo == "Transposición"
    cuerpo = paso.cuerpo
    assert not cuerpo.get("cell_by_cell_steps")
    assert "filas pasan a ser columnas" in paso.explicacion.lower()


def test_error_de_dimensiones_no_genera_pasos():
    """Si la expresión falla por incompatibilidad de dimensiones, no se generan pasos."""
    matrices = {
        "A": {"rows": 2, "cols": 2, "data": [["1", "2"], ["3", "4"]]},
        "B": {"rows": 3, "cols": 3, "data": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]]},
    }
    res = _evaluar("A + B", matrices)
    assert res["status"] == "ERROR"
    assert "dimens" in res["message"].lower() or "tamaño" in res["message"].lower()

    pasos, grupos = construir_pasos_matrices(res)
    assert pasos == ()
    assert grupos == ()


def test_sin_emdash_ni_voseo_en_textos_de_matrices():
    """Ninguna descripción o explicación contiene '—', 'Oops' ni formas de voseo."""
    matrices = {
        "A": {"rows": 2, "cols": 2, "data": [["1", "2"], ["3", "4"]]},
        "B": {"rows": 2, "cols": 2, "data": [["2", "0"], ["1", "3"]]},
        "C": {"rows": 2, "cols": 2, "data": [["5", "1"], ["2", "4"]]},
        "D": {"rows": 2, "cols": 2, "data": [["1", "-1"], ["0", "2"]]},
    }
    voseo_patterns = [
        r'\bvos\b', r'\bpodés\b', r'\btenés\b', r'\bquerés\b',
        r'\bhacé\b', r'\bmirá\b', r'\bfijate\b', r'\bacá\b',
    ]

    expresiones = ["2A - B(C - D^T)", "A + B", "-A", "3 * A", "A * B", "A^T"]
    for expr in expresiones:
        res = _evaluar(expr, matrices)
        pasos, grupos = construir_pasos_matrices(res)
        for paso in pasos:
            for texto in (paso.descripcion, paso.explicacion):
                assert "—" not in texto, f"Em-dash encontrado en {texto}"
                assert "Oops" not in texto, f"Oops encontrado en {texto}"
                for pat in voseo_patterns:
                    assert not re.search(pat, texto, re.IGNORECASE), f"Voseo '{pat}' en {texto}"
        for grupo in grupos:
            for texto in (grupo.titulo, grupo.resumen):
                assert "—" not in texto, f"Em-dash encontrado en grupo {texto}"
                assert "Oops" not in texto, f"Oops encontrado en grupo {texto}"
                for pat in voseo_patterns:
                    assert not re.search(pat, texto, re.IGNORECASE), f"Voseo '{pat}' en grupo {texto}"
