"""Lógica de selección y emisión de sugerencias contextuales proactivas para Glosa."""
from dataclasses import dataclass, field
import os
from typing import Any, Protocol

from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend import flags
from src.frontend.catalogo_sugerencias import CATALOGO_SUGERENCIAS, FOLLOW_UPS, FollowUp


@dataclass(frozen=True)
class InvalidCell:
    """Representa una celda con valor no numérico o inválido en la matriz."""

    label: str
    focus: tuple[int, int] | None = None


@dataclass(frozen=True)
class Signals:
    """Señales de estado de la herramienta activa emitidas hacia Glosa."""

    tool: str
    state: str
    flags: frozenset[str] = field(default_factory=frozenset)
    invalid: InvalidCell | None = None


@dataclass(frozen=True)
class Suggestion:
    """Sugerencia generada lista para renderizarse en chips interactivos."""

    id: str
    text: str
    role: str
    focus: tuple[int, int] | None = None


_CATALOG = CATALOGO_SUGERENCIAS


def glosa_configured() -> bool:
    """Verifica si la clave de API para OpenRouter está configurada en el entorno."""
    return bool(os.getenv("OPENROUTER_API_KEY", "").strip())


def first_invalid_cell(items: Any) -> InvalidCell | None:
    """Localiza la primera celda con entrada numérica inválida o no parseable."""
    for item in items:
        label = item[0]
        valor = item[1]
        focus = item[2] if len(item) > 2 else None

        val_str = str(valor).strip() if valor is not None else ""
        if not val_str or val_str in ("0", "0.0"):
            continue
        ok, _, _ = ValidadorMatriz.parsear_numero_exacto(val_str)
        if not ok:
            return InvalidCell(label=label, focus=focus)
    return None


def chips_active() -> bool:
    """Indica si el modo proactivo y el dock de Glosa están activos."""
    return flags.dock_enabled() and flags.proactive_enabled()


def _es_flag_valido(herramienta: str, nombre_flag: str, estado: str) -> bool:
    """Comprueba restricciones adicionales entre herramienta, flag y estado."""
    if herramienta == "matrices" and nombre_flag == "has_product":
        return estado == "ok"
    if herramienta == "bases":
        return estado == "result"
    if herramienta == "romanos":
        return estado in ("ok", "error")
    return True


def _coincide_disparador(disparador: str, senales: Signals) -> bool:
    """Evalúa si el disparador coincide con el estado o flags activos."""
    if disparador == senales.state:
        return True
    if disparador.startswith("flag_"):
        nombre_flag = disparador[5:]
        if nombre_flag in senales.flags:
            return _es_flag_valido(senales.tool, nombre_flag, senales.state)
    return False


def candidates(signals: Signals | None) -> list[Suggestion]:
    """Genera la lista de todas las sugerencias candidatas para las señales dadas."""
    if not signals:
        return []

    cands: list[Suggestion] = []

    if signals.state == "none" and signals.invalid:
        label = signals.invalid.label
        if len(label) > 24:
            label = label[:23] + "…"
        cands.append(
            Suggestion(
                id=f"{signals.tool}.invalid",
                text=f"¿Por qué {label} no es válido?",
                role="specific",
                focus=signals.invalid.focus,
            )
        )

    for tool, trigger, id_, text, role in _CATALOG:
        if tool != signals.tool:
            continue
        if _coincide_disparador(trigger, signals):
            cands.append(Suggestion(id=id_, text=text, role=role))

    return cands


def select_chips(cands: list[Suggestion], limit: int) -> list[Suggestion]:
    """Ordena y prioriza chips por rol (específico > estado > flag) hasta el límite."""
    specifics = [c for c in cands if c.role == "specific"]
    states = [c for c in cands if c.role == "state"]
    flags_list = [c for c in cands if c.role == "flag"]

    selected: list[Suggestion] = []
    selected.extend(specifics)

    for s in states[:2]:
        if s not in selected:
            selected.append(s)

    if flags_list and flags_list[0] not in selected:
        selected.append(flags_list[0])

    for s in states[2:]:
        if s not in selected:
            selected.append(s)

    for f in flags_list[1:]:
        if f not in selected:
            selected.append(f)

    return selected[:limit]


def suggest(
    signals: Signals | None,
    *,
    limit: int = 3,
    include_specific: bool = True,
) -> list[Suggestion]:
    """Genera las mejores sugerencias a mostrar según las señales actuales de la vista."""
    cands = candidates(signals)
    if not include_specific:
        cands = [c for c in cands if c.role != "specific"]
    return select_chips(cands, limit)


class SuggestionProvider(Protocol):
    """Protocolo para vistas capaces de proveer señales dinámicas para Glosa."""

    def get_ai_signals(self) -> Signals | None:
        """Devuelve las señales contextuales de la vista actual."""
        ...
