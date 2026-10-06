"""Pruebas unitarias para InverseOpsController."""
import json
import os
import sys

# Inyección de ruta raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.frontend.controllers.inverse_ops.controller_inverse_ops import (
    InverseOpsController,
)


def test_inverse_ops_controller():
    print("==================================================")
    print(" PRUEBA DEL CONTROLLER: MATRIZ INVERSA            ")
    print("==================================================")

    # 1. Caso 2x2 invertible [[1, 2], [3, 4]]
    payload_valid = json.dumps({
        "n": 2,
        "data": [["1", "2"], ["3", "4"]],
    })
    res = InverseOpsController.process_inverse(payload_valid)
    assert res["status"] == "SUCCESS", f"Esperado SUCCESS, obtenido {res['status']}"
    assert res["determinant_str"] == "-2"
    assert res["matrix_a"] is not None
    assert res["matrix_a_latex"] is not None
    assert res["inverse"] is not None
    assert res["inverse_latex"] is not None
    assert len(res["verifications"]) == 3
    assert all(v["coincide"] is True for v in res["verifications"])

    steps = res["steps"]
    groups = res["groups"]
    stats = res["stats"]

    assert len(steps) > 0
    kinds = {s["kind"] for s in steps}
    assert "inicial" in kinds
    assert "pivote" in kinds
    assert "eliminacion" in kinds
    assert "normalizacion" in kinds
    assert "otro" not in kinds, f"No debería haber pasos tipo 'otro', encontrados: {kinds}"

    for s in steps:
        g_idx = s["group_index"]
        assert 0 <= g_idx < len(groups), f"group_index inválido {g_idx}"
        assert s["index"] in groups[g_idx]["step_indices"]

    assert stats["total"] == len(steps)
    assert stats["pivotes"] > 0
    assert stats["eliminaciones"] > 0
    assert stats["normalizaciones"] > 0

    # 2. Celda inválida "abc" en (1, 0) (fila 2, columna 1)
    payload_invalid_cell = json.dumps({
        "n": 2,
        "data": [["1", "2"], ["abc", "4"]],
    })
    res_err_cell = InverseOpsController.process_inverse(payload_invalid_cell)
    assert res_err_cell["status"] == "ERROR"
    assert res_err_cell["error_cell"] == [1, 0]
    assert "Error en A[2,1]" in res_err_cell["message"]

    # 3. n=51 (excede INVERSE_MAX_DIMENSION)
    payload_n51 = json.dumps({
        "n": 51,
        "data": [["0"] * 51] * 51,
    })
    res_n51 = InverseOpsController.process_inverse(payload_n51)
    assert res_n51["status"] == "ERROR"
    assert "entre 1 y 50" in res_n51["message"]

    # 4. Payload malformado (sin lanzar excepción)
    res_malformed = InverseOpsController.process_inverse("esto no es json")
    assert res_malformed["status"] == "ERROR"

    res_not_dict = InverseOpsController.process_inverse("[1, 2, 3]")
    assert res_not_dict["status"] == "ERROR"

    # 5. Matriz singular [[1, 2], [2, 4]]
    payload_singular = json.dumps({
        "n": 2,
        "data": [["1", "2"], ["2", "4"]],
    })
    res_sing = InverseOpsController.process_inverse(payload_singular)
    assert res_sing["status"] == "SINGULAR"
    assert res_sing["determinant"] == 0
    assert res_sing["inverse"] is None

    print(">>> ¡Todas las pruebas del controller pasaron con éxito!")


if __name__ == "__main__":
    test_inverse_ops_controller()
