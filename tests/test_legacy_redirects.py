"""Pruebas unitarias para las redirecciones legacy (Fase 1)."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.frontend import navigation
from src.frontend.routes import register_legacy_redirects


@pytest.fixture
def client():
    """Crea una aplicación FastAPI mínima con las redirecciones legacy registradas."""
    app = FastAPI()
    register_legacy_redirects(app)
    return TestClient(app, follow_redirects=False)


def test_ten_legacy_routes_status_and_location(client):
    """Verifica que las 10 rutas legacy devuelvan código 302 y el Location exacto."""
    expected_redirects = {
        "/": "/algebra-lineal/sistemas",
        "/ia": "/algebra-lineal/sistemas",
        "/sistemas-lineales": "/algebra-lineal/sistemas",
        "/gauss": "/algebra-lineal/sistemas?method=gauss",
        "/gauss-jordan": "/algebra-lineal/sistemas?method=gauss-jordan",
        "/operaciones-matrices": "/algebra-lineal/matrices",
        "/matriz-inversa": "/algebra-lineal/inversa",
        "/vectores": "/algebra-lineal/vectores",
        "/conversor": "/utilidades/bases",
        "/romanos": "/utilidades/romanos",
    }

    for path, expected_location in expected_redirects.items():
        response = client.get(path)
        assert response.status_code == 302, f"Ruta {path} devolvió código {response.status_code}, se esperaba 302"
        assert response.headers["location"] == expected_location, (
            f"Ruta {path} redirigió a {response.headers['location']}, se esperaba {expected_location}"
        )


def test_query_preservation_and_precedence(client):
    """Verifica la preservación de parámetros query y la precedencia de queries fijas."""
    # 1. Conservar query normal
    r1 = client.get("/sistemas-lineales?method=gauss-jordan")
    assert r1.status_code == 302
    assert r1.headers["location"] == "/algebra-lineal/sistemas?method=gauss-jordan"

    # 2. Agregar query entrante a query fija (/gauss?x=1 -> ?method=gauss&x=1)
    r2 = client.get("/gauss?x=1")
    assert r2.status_code == 302
    assert r2.headers["location"] == "/algebra-lineal/sistemas?method=gauss&x=1"

    # 3. Precedencia: query fija prevalece sobre entrante (/gauss?method=gauss-jordan -> ?method=gauss)
    r3 = client.get("/gauss?method=gauss-jordan")
    assert r3.status_code == 302
    assert r3.headers["location"] == "/algebra-lineal/sistemas?method=gauss"


def test_no_legacy_chains(client):
    """Confirma que ningún Location de redirección apunte a otra ruta legacy."""
    legacy_paths = {rule.path for rule in navigation.legacy_redirects()}

    for path in legacy_paths:
        resp = client.get(path)
        target_path = resp.headers["location"].split("?")[0]
        assert target_path not in legacy_paths, (
            f"Ruta {path} produce una cadena redirigiendo a otra ruta legacy: {target_path}"
        )


def test_hub_enabled_redirects(monkeypatch):
    """Valida el comportamiento con HUB_ENABLED=True: '/' no se registra e '/ia' va a '/?glosa=1'."""
    monkeypatch.setattr(navigation, "HUB_ENABLED", True)

    app = FastAPI()
    register_legacy_redirects(app)
    hub_client = TestClient(app, follow_redirects=False)

    # '/' no debe estar registrada en legacy_redirects (debe dar 404 en esta app mínima)
    r_root = hub_client.get("/")
    assert r_root.status_code == 404, "Con HUB_ENABLED=True, '/' no debe ser manejado por legacy_redirects"

    # '/ia' debe redirigir a '/?glosa=1'
    r_ia = hub_client.get("/ia")
    assert r_ia.status_code == 302
    assert r_ia.headers["location"] == "/?glosa=1"
