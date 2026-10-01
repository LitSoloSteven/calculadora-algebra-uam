"""Tests para InverseOpsController en tests/."""
import json
import pytest
from src.frontend.controllers.inverse_ops.controller_inverse_ops import InverseOpsController


def test_inverse_controller_2x2_success():
    payload = json.dumps({
        "n": 2,
        "data": [["1", "2"], ["3", "4"]],
    })
    res = InverseOpsController.process_inverse(payload)
    assert res["status"] == "SUCCESS"
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
    assert "otro" not in kinds

    for s in steps:
        g_idx = s["group_index"]
        assert 0 <= g_idx < len(groups)
        assert s["index"] in groups[g_idx]["step_indices"]

    assert stats["total"] == len(steps)
    assert stats["pivotes"] > 0
    assert stats["eliminaciones"] > 0
    assert stats["normalizaciones"] > 0


def test_inverse_controller_invalid_cell():
    payload = json.dumps({
        "n": 2,
        "data": [["1", "2"], ["abc", "4"]],
    })
    res = InverseOpsController.process_inverse(payload)
    assert res["status"] == "ERROR"
    assert res["error_cell"] == [1, 0]
    assert "Error en A[2,1]" in res["message"]


def test_inverse_controller_dimension_limits():
    payload_n51 = json.dumps({
        "n": 51,
        "data": [["0"] * 51] * 51,
    })
    res_n51 = InverseOpsController.process_inverse(payload_n51)
    assert res_n51["status"] == "ERROR"
    assert "entre 1 y 50" in res_n51["message"]


def test_inverse_controller_malformed_json():
    res_malformed = InverseOpsController.process_inverse("not json")
    assert res_malformed["status"] == "ERROR"

    res_not_dict = InverseOpsController.process_inverse("[1, 2, 3]")
    assert res_not_dict["status"] == "ERROR"


def test_inverse_controller_singular():
    payload = json.dumps({
        "n": 2,
        "data": [["1", "2"], ["2", "4"]],
    })
    res = InverseOpsController.process_inverse(payload)
    assert res["status"] == "SINGULAR"
    assert res["determinant"] == 0
    assert res["inverse"] is None
