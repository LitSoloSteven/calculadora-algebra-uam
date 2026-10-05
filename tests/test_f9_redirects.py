from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.frontend import navigation
from src.frontend.routes import register_legacy_redirects


@pytest.fixture
def hub_client(monkeypatch):
    monkeypatch.setattr(navigation, "HUB_ENABLED", True)
    app = FastAPI()
    register_legacy_redirects(app)
    return TestClient(app, follow_redirects=False)


def test_f9_all_legacy_routes_301_with_hub_active(hub_client):
    """Verifica que con Hub activo, todas las rutas legacy devuelvan 301 con Location correcto."""
    expected_redirects = {
        "/ia": "/?glosa=1",
        "/sistemas-lineales": "/algebra-lineal/sistemas",
        "/gauss": "/algebra-lineal/sistemas?method=gauss",
        "/gauss-jordan": "/algebra-lineal/sistemas?method=gauss-jordan",
        "/operaciones-matrices": "/algebra-lineal/matrices",
        "/matriz-inversa": "/algebra-lineal/inversa",
        "/vectores": "/algebra-lineal/vectores",
        "/conversor": "/utilidades/bases",
        "/romanos": "/utilidades/romanos",
    }

    for path, expected_loc in expected_redirects.items():
        resp = hub_client.get(path)
        assert resp.status_code == 301, f"Ruta {path} devolvió {resp.status_code}, se esperaba 301"
        assert resp.headers["location"] == expected_loc


def test_f9_query_preservation_and_precedence(hub_client):
    """Verifica que la query se preserve con 301 y que la fija tenga precedencia."""
    # Preservar query
    r1 = hub_client.get("/matriz-inversa?foo=bar&baz=1")
    assert r1.status_code == 301
    assert r1.headers["location"] == "/algebra-lineal/inversa?foo=bar&baz=1"

    # Merge con fija
    r2 = hub_client.get("/gauss?extra=test")
    assert r2.status_code == 301
    assert r2.headers["location"] == "/algebra-lineal/sistemas?method=gauss&extra=test"

    # Precedencia
    r3 = hub_client.get("/gauss?method=override")
    assert r3.status_code == 301
    assert r3.headers["location"] == "/algebra-lineal/sistemas?method=gauss"


def test_f9_no_redirect_chains(hub_client):
    """Verifica que no haya cadenas de redirecciones hacia otras rutas legacy."""
    legacy_paths = {rule.path for rule in navigation.legacy_redirects()}
    for path in legacy_paths:
        resp = hub_client.get(path)
        target = resp.headers["location"].split("?")[0]
        assert target not in legacy_paths, f"Cadena detectada: {path} -> {target}"


def test_f9_hub_disabled_returns_302(monkeypatch):
    """Verifica que con Hub desactivado, las rutas que dependen del flag devuelvan 302."""
    monkeypatch.setattr(navigation, "HUB_ENABLED", False)
    app = FastAPI()
    register_legacy_redirects(app)
    client = TestClient(app, follow_redirects=False)

    for path in ("/", "/ia"):
        resp = client.get(path)
        assert resp.status_code == 302, f"Ruta {path} devolvió {resp.status_code}, se esperaba 302"
        assert resp.headers["location"] == "/algebra-lineal/sistemas"
