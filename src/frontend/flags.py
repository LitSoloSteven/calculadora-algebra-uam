"""Feature flags del frontend de Scalaris.

Evalúa variables de entorno en tiempo de llamada para controlar
la activación progresiva de capacidades en fases posteriores.
"""
from __future__ import annotations

import os

_TRUE_VALUES: frozenset[str] = frozenset({"1", "true", "on", "yes"})
_FALSE_VALUES: frozenset[str] = frozenset({"0", "false", "off", "no"})


def _parse_bool_env(var_name: str, default: bool) -> bool:
    """Parsea una variable de entorno como booleano.

    Acepta: 1/0, true/false, on/off, yes/no (insensible a mayúsculas/minúsculas).
    Si la variable no está definida o contiene un valor inválido, retorna `default`.
    """
    raw = os.getenv(var_name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return default


def nav_v2() -> bool:
    """Indica si la barra de navegación y taxonomía v2 están activas (por defecto: True)."""
    return _parse_bool_env("SCALARIS_NAV", default=True)


def dock_enabled() -> bool:
    """Indica si el dock de Glosa está habilitado (por defecto: False)."""
    return _parse_bool_env("SCALARIS_DOCK", default=False)


def proactive_enabled() -> bool:
    """Indica si el modo proactivo de sugerencias está habilitado (por defecto: False)."""
    return _parse_bool_env("SCALARIS_PROACTIVE", default=False)
