import json
import threading
import pytest
import requests

from src.ai.openrouter_ai import OpenRouterIA, AIResult, AIErrorKind


class MockResponse:
    def __init__(self, status_code: int, json_data: dict = None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text or json.dumps(self._json_data)

    def json(self):
        return self._json_data


@pytest.fixture(autouse=True)
def reset_openrouter_state(monkeypatch):
    import src.ai.openrouter_ai as oai

    with oai._bloqueo_cache:
        oai._cache_respuestas.clear()
    monkeypatch.setattr(OpenRouterIA, "MODELOS_RESERVA", [])
    yield
    with oai._bloqueo_cache:
        oai._cache_respuestas.clear()


def test_sin_clave_no_key_y_sin_llamada_red(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    call_count = 0

    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return MockResponse(200)

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    res = client.ask("¿Qué es una matriz?")
    assert res.ok is False
    assert res.kind == AIErrorKind.NO_KEY
    assert call_count == 0


def test_200_con_contenido_ok(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    calls = []

    def mock_post(url, headers=None, json=None, timeout=None):
        calls.append((url, json))
        return MockResponse(200, {"choices": [{"message": {"content": "Una matriz es un arreglo bidimensional."}}]})

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is True
    assert res.text == "Una matriz es un arreglo bidimensional."
    assert len(calls) == 1


def test_200_sin_choices_empty(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def mock_post(url, headers=None, json=None, timeout=None):
        return MockResponse(200, {"choices": []})

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is False
    assert res.kind == AIErrorKind.EMPTY


def test_401_auth_sin_reintento(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    calls = []

    def mock_post(url, headers=None, json=None, timeout=None):
        calls.append(url)
        return MockResponse(401, text="Unauthorized: invalid api key")

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is False
    assert res.kind == AIErrorKind.AUTH
    assert len(calls) == 1


def test_429_primario_sleep_y_reintento(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    calls = []
    sleeps = []

    def mock_post(url, headers=None, json=None, timeout=None):
        calls.append(len(calls))
        if len(calls) == 1:
            return MockResponse(429, text="Rate limited")
        return MockResponse(200, {"choices": [{"message": {"content": "Respuesta tras reintento"}}]})

    def mock_sleep(secs):
        sleeps.append(secs)

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    monkeypatch.setattr(OpenRouterIA, "_tiempo_dormir", staticmethod(mock_sleep))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is True
    assert res.text == "Respuesta tras reintento"
    assert len(calls) == 2
    assert len(sleeps) == 1
    assert sleeps[0] == 1.0


def test_429_persistente_con_fallback_segundo_modelo(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    fallback_name = "backup/model-secondary:free"
    monkeypatch.setattr(OpenRouterIA, "MODELOS_RESERVA", [fallback_name])
    calls = []
    sleeps = []

    def mock_post(url, headers=None, json=None, timeout=None):
        model_called = json.get("model")
        calls.append(model_called)
        if model_called != fallback_name:
            return MockResponse(429, text="Rate limit en modelo primario")
        return MockResponse(200, {"choices": [{"message": {"content": "Respuesta desde fallback"}}]})

    def mock_sleep(secs):
        sleeps.append(secs)

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    monkeypatch.setattr(OpenRouterIA, "_tiempo_dormir", staticmethod(mock_sleep))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is True
    assert res.text == "Respuesta desde fallback"
    assert res.model == fallback_name
    assert calls.count(OpenRouterIA.MODELO_PRIMARIO) == 2
    assert calls.count(fallback_name) == 1


def test_429_sin_fallback_rate_limit(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(OpenRouterIA, "MODELOS_RESERVA", [])

    def mock_post(url, headers=None, json=None, timeout=None):
        return MockResponse(429, text="Rate limit")

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    monkeypatch.setattr(OpenRouterIA, "_tiempo_dormir", staticmethod(lambda s: None))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is False
    assert res.kind == AIErrorKind.RATE_LIMIT


def test_timeout_con_y_sin_fallback(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    # 1. Con fallback
    fallback_name = "backup/model-timeout"
    monkeypatch.setattr(OpenRouterIA, "MODELOS_RESERVA", [fallback_name])

    def mock_post_with_fallback(url, headers=None, json=None, timeout=None):
        if json.get("model") == OpenRouterIA.MODELO_PRIMARIO:
            raise requests.exceptions.Timeout("Timeout en primario")
        return MockResponse(200, {"choices": [{"message": {"content": "Respuesta exitosa en fallback"}}]})

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post_with_fallback))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is True
    assert res.model == fallback_name

    # 2. Sin fallback
    monkeypatch.setattr(OpenRouterIA, "MODELOS_RESERVA", [])

    def mock_post_timeout(url, headers=None, json=None, timeout=None):
        raise requests.exceptions.Timeout("Timeout total")

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post_timeout))
    client2 = OpenRouterIA()
    res2 = client2.ask("pregunta")
    assert res2.ok is False
    assert res2.kind == AIErrorKind.TIMEOUT


def test_connection_error_network(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def mock_post(url, headers=None, json=None, timeout=None):
        raise requests.exceptions.ConnectionError("Error de socket")

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is False
    assert res.kind == AIErrorKind.NETWORK


def test_cancel_antes_de_llamar_cancelled_sin_llamada(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    call_count = 0

    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return MockResponse(200)

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    cancel = threading.Event()
    cancel.set()
    res = client.ask("pregunta", cancel=cancel)
    assert res.ok is False
    assert res.kind == AIErrorKind.CANCELLED
    assert call_count == 0


def test_deadline_agotado_con_reloj_simulado_service(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    simulated_time = 100.0

    def mock_time():
        return simulated_time

    def mock_post(url, headers=None, json=None, timeout=None):
        nonlocal simulated_time
        # Simulamos que la llamada consumió casi todo el tiempo y dejó menos de 2s
        simulated_time = 139.5
        return MockResponse(500, text="Transient error")

    monkeypatch.setattr(OpenRouterIA, "_tiempo_monotonico", staticmethod(mock_time))
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    monkeypatch.setattr(OpenRouterIA, "_tiempo_dormir", staticmethod(lambda s: None))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is False
    assert res.kind == AIErrorKind.SERVICE


def test_cacheable_comportamiento_completo(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    current_time = 1000.0

    def mock_time():
        return current_time

    network_calls = 0

    def mock_post(url, headers=None, json=None, timeout=None):
        nonlocal network_calls
        network_calls += 1
        return MockResponse(200, {"choices": [{"message": {"content": f"Respuesta #{network_calls}"}}]})

    monkeypatch.setattr(OpenRouterIA, "_tiempo_monotonico", staticmethod(mock_time))
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()

    # 1. Primera llamada con cacheable=True -> llamada de red
    res1 = client.ask("¿Qué es un vector?", cacheable=True)
    assert res1.ok is True
    assert res1.cached is False
    assert network_calls == 1

    # 2. Segunda llamada con idénticos parámetros -> devuelve de caché
    res2 = client.ask("¿Qué es un vector?", cacheable=True)
    assert res2.ok is True
    assert res2.cached is True
    assert res2.text == res1.text
    assert network_calls == 1

    # 3. Diferente simpler genera otra clave -> llamada de red
    res3 = client.ask("¿Qué es un vector?", cacheable=True, simpler=True)
    assert res3.ok is True
    assert res3.cached is False
    assert network_calls == 2

    # 4. Diferente context_block genera otra clave -> llamada de red
    res4 = client.ask("¿Qué es un vector?", cacheable=True, context_block="[CONTEXTO]\n{\"v\":1}\n[/CONTEXTO]")
    assert res4.ok is True
    assert res4.cached is False
    assert network_calls == 3

    # 5. cacheable=False no cachea ni lee caché
    res5 = client.ask("¿Qué es un vector?", cacheable=False)
    assert res5.ok is True
    assert res5.cached is False
    assert network_calls == 4

    # 6. Pasado 3600 segundos la entrada en caché expira
    current_time += 3601.0
    res6 = client.ask("¿Qué es un vector?", cacheable=True)
    assert res6.ok is True
    assert res6.cached is False
    assert network_calls == 5


def test_ningun_airesult_text_contiene_palabras_prohibidas(monkeypatch):
    prohibidas = ["Traceback", "Python", ".env", "OPENROUTER"]
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    # Evaluamos los textos producidos en cada tipo de error
    client = OpenRouterIA()

    # NO_KEY
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    r_no_key = OpenRouterIA().ask("hola")

    # CANCELLED
    cancel = threading.Event()
    cancel.set()
    r_cancelled = client.ask("hola", cancel=cancel)

    # AUTH (401)
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(lambda *a, **k: MockResponse(401, text="Auth err")))
    r_auth = client.ask("hola")

    # EMPTY (200 sin choices)
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(lambda *a, **k: MockResponse(200, {"choices": []})))
    r_empty = client.ask("hola")

    # RATE_LIMIT (429)
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(lambda *a, **k: MockResponse(429, text="Rate limit")))
    monkeypatch.setattr(OpenRouterIA, "_tiempo_dormir", staticmethod(lambda s: None))
    r_rate = client.ask("hola")

    # TIMEOUT
    def raise_timeout(*a, **k):
        raise requests.exceptions.Timeout("timeout")
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(raise_timeout))
    r_timeout = client.ask("hola")

    # NETWORK
    def raise_conn(*a, **k):
        raise requests.exceptions.ConnectionError("conn")
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(raise_conn))
    r_network = client.ask("hola")

    # SERVICE (deadline/500)
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(lambda *a, **k: MockResponse(500, text="error")))
    r_service = client.ask("hola")

    todos_los_resultados = [
        r_no_key,
        r_cancelled,
        r_auth,
        r_empty,
        r_rate,
        r_timeout,
        r_network,
        r_service,
    ]

    for res in todos_los_resultados:
        for p in prohibidas:
            assert p not in res.text, f"Palabra prohibida '{p}' encontrada en: {res.text}"
