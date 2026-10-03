"""Tests for geometry handoff (put/consume system and vectors)."""
import time
from unittest.mock import patch

from src.frontend.components.handoff import (
    HandoffResult,
    TTL_SECONDS,
    _STORE,
    put_matrix,
    consume_matrix,
    put_system,
    put_vectors,
    consume_system,
    consume_vectors,
    _now,
)


def _clear_store():
    _STORE.clear()


def test_put_consume_system_ok():
    _clear_store()
    token = put_system("sistemas", [["1", "2"], ["3", "4"]], ["5", "6"])
    result = consume_system(token, max_m=10, allowed_n={2, 3})
    assert result.status == "ok"
    assert result.data["matrix_A"] == [["1", "2"], ["3", "4"]]
    assert result.data["vector_b"] == ["5", "6"]


def test_put_consume_system_single_use():
    _clear_store()
    token = put_system("sistemas", [["1", "1"]], ["2"])
    result1 = consume_system(token, max_m=10, allowed_n={2, 3})
    assert result1.status == "ok"
    result2 = consume_system(token, max_m=10, allowed_n={2, 3})
    assert result2.status == "missing"


def test_consume_system_expired():
    _clear_store()
    token = put_system("test", [["1", "1"]], ["2"])
    # Simulate time passing
    with patch("src.frontend.components.handoff._now", return_value=_now() + TTL_SECONDS + 10):
        result = consume_system(token, max_m=10, allowed_n={2, 3})
    assert result.status == "expired"


def test_consume_system_empty_token():
    result = consume_system("", max_m=10, allowed_n={2, 3})
    assert result is None


def test_system_invalid_n():
    _clear_store()
    token = put_system("test", [["1", "0", "0", "0"]], ["1"])
    result = consume_system(token, max_m=10, allowed_n={2, 3})
    assert result.status == "invalid"


def test_system_invalid_cells():
    _clear_store()
    token = put_system("test", [["abc", "1"]], ["1"])
    result = consume_system(token, max_m=10, allowed_n={2, 3})
    assert result.status == "invalid"


def test_put_consume_vectors_ok():
    _clear_store()
    token = put_vectors("vectores", "vectores", [["1", "2"], ["3", "4"]])
    result = consume_vectors(token, allowed_n={2, 3})
    assert result.status == "ok"
    assert result.data["scene"] == "vectores"
    assert result.data["data"] == [["1", "2"], ["3", "4"]]


def test_put_consume_vectors_single_use():
    _clear_store()
    token = put_vectors("vectores", "combinacion", [["1", "2"]])
    result1 = consume_vectors(token, allowed_n={2, 3})
    assert result1.status == "ok"
    result2 = consume_vectors(token, allowed_n={2, 3})
    assert result2.status == "missing"


def test_consume_vectors_expired():
    _clear_store()
    token = put_vectors("test", "vectores", [["1", "0"]])
    with patch("src.frontend.components.handoff._now", return_value=_now() + TTL_SECONDS + 10):
        result = consume_vectors(token, allowed_n={2, 3})
    assert result.status == "expired"


def test_vectors_invalid_dimension():
    _clear_store()
    token = put_vectors("test", "vectores", [["1", "0", "0", "0"]])
    result = consume_vectors(token, allowed_n={2, 3})
    assert result.status == "invalid"


def test_vectors_invalid_cells():
    _clear_store()
    token = put_vectors("test", "vectores", [["abc", "1"]])
    result = consume_vectors(token, allowed_n={2, 3})
    assert result.status == "invalid"


def test_put_matrix_consume_matrix_still_work():
    """Existing put_matrix/consume_matrix are unchanged."""
    _clear_store()
    token = put_matrix("sistemas", [["1", "2"], ["3", "4"]])
    result = consume_matrix(token, max_n=10)
    assert result.status == "ok"
    assert result.data == [["1", "2"], ["3", "4"]]


def test_handoff_module_imports():
    """Module imports without error."""
    import src.frontend.components.handoff
    assert hasattr(src.frontend.components.handoff, 'put_system')
    assert hasattr(src.frontend.components.handoff, 'consume_system')
    assert hasattr(src.frontend.components.handoff, 'put_vectors')
    assert hasattr(src.frontend.components.handoff, 'consume_vectors')
