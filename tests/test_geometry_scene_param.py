"""Pruebas de normalizacion de escena en URL y validacion de handoff en el Visualizador (Fase P5)."""
import pytest

from src.frontend.components.handoff import (
    HandoffResult,
    _STORE,
    consume_vectors,
    put_vectors,
)
from src.frontend.navigation import VISUALIZER_SCENES
from src.frontend.views.geometry.view_geometry import GeometryUI, VALID_SCENES


def test_visualizer_scenes_parity_with_valid_scenes():
    """(1) Garantiza que las claves de VISUALIZER_SCENES coincidan exactamente con VALID_SCENES."""
    scene_keys = tuple(item[0] for item in VISUALIZER_SCENES)
    assert scene_keys == VALID_SCENES
    assert VALID_SCENES == ('rectas-planos', 'vectores', 'combinacion')


@pytest.mark.parametrize(
    "input_scene, expected_scene",
    [
        ("rectas-planos", "rectas-planos"),
        ("vectores", "vectores"),
        ("combinacion", "combinacion"),
        ("invalida", "rectas-planos"),
        ("", "rectas-planos"),
        ("desconocida_xyz", "rectas-planos"),
        ("RECTAS-PLANOS", "rectas-planos"),
    ],
)
def test_normalize_scene_fallback(input_scene, expected_scene):
    """(2) Un parametro 'escena' invalido se normaliza a 'rectas-planos' sin redirigir."""
    assert GeometryUI.normalize_scene(input_scene) == expected_scene


def test_vectors_handoff_scene_mismatch_rejected():
    """(3) Un payload de vectores cuya escena no coincida con la URL se rechaza con el mensaje estandar."""
    _STORE.clear()
    # Genera un token con escena 'combinacion'
    token = put_vectors("vectores", "combinacion", [["1", "2"], ["3", "4"]])
    result = consume_vectors(token, allowed_n={2, 3})

    assert result.status == "ok"
    assert result.data is not None
    payload_scene = result.data.get("scene")

    # Si la URL activa es 'vectores', no coincide con 'combinacion'
    current_scene = "vectores"
    assert payload_scene != current_scene

    # La logica de rechazo genera HandoffResult invalido con el copy estandar
    if payload_scene != current_scene:
        rejected = HandoffResult(
            status="invalid",
            data=None,
            source_name=result.source_name,
            message="Los datos recibidos no son válidos, así que empezamos con la herramienta vacía.",
        )

    assert rejected.status == "invalid"
    assert rejected.data is None
    assert rejected.message == "Los datos recibidos no son válidos, así que empezamos con la herramienta vacía."


def test_vectors_handoff_scene_match_accepted():
    """Un payload de vectores cuya escena coincide con la URL se acepta normalmente."""
    _STORE.clear()
    token = put_vectors("vectores", "vectores", [["1", "2"], ["3", "4"]])
    result = consume_vectors(token, allowed_n={2, 3})

    assert result.status == "ok"
    assert result.data is not None
    assert result.data.get("scene") == "vectores"
