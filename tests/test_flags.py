"""Pruebas unitarias para las feature flags del frontend (Fase 1)."""
import pytest

from src.frontend.flags import dock_enabled, nav_v2, proactive_enabled


def test_flags_defaults(monkeypatch):
    """Verifica los valores por defecto cuando las variables de entorno no existen."""
    monkeypatch.delenv("SCALARIS_NAV", raising=False)
    monkeypatch.delenv("SCALARIS_DOCK", raising=False)
    monkeypatch.delenv("SCALARIS_PROACTIVE", raising=False)

    assert nav_v2() is True
    assert dock_enabled() is True
    assert proactive_enabled() is True


@pytest.mark.parametrize("truthy", ["1", "true", "True", "TRUE", "on", "ON", "yes", "YES"])
def test_flags_truthy_values(monkeypatch, truthy):
    """Verifica la activación de flags con múltiples variantes verdaderas."""
    monkeypatch.setenv("SCALARIS_NAV", truthy)
    monkeypatch.setenv("SCALARIS_DOCK", truthy)
    monkeypatch.setenv("SCALARIS_PROACTIVE", truthy)

    assert nav_v2() is True
    assert dock_enabled() is True
    assert proactive_enabled() is True


@pytest.mark.parametrize("falsy", ["0", "false", "False", "FALSE", "off", "OFF", "no", "NO"])
def test_flags_falsy_values(monkeypatch, falsy):
    """Verifica la desactivación de flags con múltiples variantes falsas."""
    monkeypatch.setenv("SCALARIS_NAV", falsy)
    monkeypatch.setenv("SCALARIS_DOCK", falsy)
    monkeypatch.setenv("SCALARIS_PROACTIVE", falsy)

    assert nav_v2() is False
    assert dock_enabled() is False
    assert proactive_enabled() is False


@pytest.mark.parametrize("invalid", ["invalid", "2", "none", "", "   ", "maybe"])
def test_flags_invalid_values_fallback_to_defaults(monkeypatch, invalid):
    """Verifica que valores inválidos caigan de forma segura a su respectivo default."""
    monkeypatch.setenv("SCALARIS_NAV", invalid)
    monkeypatch.setenv("SCALARIS_DOCK", invalid)
    monkeypatch.setenv("SCALARIS_PROACTIVE", invalid)

    assert nav_v2() is True  # default True
    assert dock_enabled() is True  # default True
    assert proactive_enabled() is True  # default True
