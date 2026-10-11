"""Clasificador de respuestas y errores HTTP del servicio OpenRouter.

Determina si una respuesta HTTP 200 contiene datos válidos y traduce códigos de
error HTTP (401, 403, 429, 5xx) en decisiones de reintento, conmutación o finalización.
"""

from dataclasses import dataclass
import logging
from typing import Any
import requests

from src.ai.constantes import (
    CODIGOS_ESTADO_TRANSITORIOS,
    TIEMPO_RESTANTE_MINIMO_PARA_REINTENTO,
)

logger = logging.getLogger(__name__)


def procesar_respuesta_exitosa(
    respuesta: requests.Response, modelo: str, ai_result_cls: type, error_kind_cls: type
) -> Any:
    """Parsea el JSON de una respuesta HTTP 200 y extrae el texto generado."""
    try:
        datos = respuesta.json()
        opciones = datos.get("choices") or []
        contenido = (
            (opciones[0].get("message") or {}).get("content")
            if opciones
            else None
        )
        if contenido:
            return ai_result_cls(True, contenido, model=modelo)
        logger.error("Respuesta de IA vacía con estado 200. Modelo: %s", modelo)
        return ai_result_cls(
            False,
            "Glosa no devolvió una respuesta. Reformula la pregunta o inténtalo de nuevo.",
            error_kind_cls.EMPTY,
        )
    except Exception as e:
        logger.error("Error parseando JSON de respuesta de IA: %s", e)
        return ai_result_cls(
            False,
            "Glosa no pudo responder ahora. Vuelve a intentarlo en un momento.",
            error_kind_cls.SERVICE,
        )


@dataclass
class ContextoIntento:
    """Metadatos de la iteración actual en la cascada de llamadas a modelos."""

    intento: int
    idx_modelo: int
    tiempo_restante: float
    total_modelos: int


def _manejar_limite_tasa(
    ctx: ContextoIntento, ai_result_cls: type, error_kind_cls: type
) -> tuple[Any, str]:
    """Determina si un error 429 debe reintentarse, pasar a fallback o terminar."""
    if (
        ctx.intento == 0
        and ctx.idx_modelo == 0
        and ctx.tiempo_restante > TIEMPO_RESTANTE_MINIMO_PARA_REINTENTO
    ):
        return None, "reintentar"
    if ctx.idx_modelo == 0 and ctx.total_modelos > 1:
        return None, "fallback"
    res = ai_result_cls(
        False,
        "Glosa está recibiendo muchas consultas ahora. Espera unos segundos y vuelve a intentarlo.",
        error_kind_cls.RATE_LIMIT,
    )
    return res, "terminar"


def clasificar_error_http(
    codigo: int,
    cuerpo_texto: str,
    modelo: str,
    ctx: ContextoIntento,
    *,
    ai_result_cls: type,
    error_kind_cls: type,
) -> tuple[Any, str]:
    """Clasifica errores HTTP en acción ('reintentar', 'fallback', 'terminar') o resultado."""
    if codigo in (401, 403):
        logger.error("Error de autenticación con OpenRouter: %s - %s", codigo, cuerpo_texto[:200])
        res = ai_result_cls(
            False,
            "Glosa no pudo autenticarse con el servicio de IA. Avisa a quien administra Scalaris.",
            error_kind_cls.AUTH,
        )
        return res, "terminar"

    if codigo == 429:
        logger.warning("Límite de tasa en %s", modelo)
        return _manejar_limite_tasa(ctx, ai_result_cls, error_kind_cls)

    if codigo in CODIGOS_ESTADO_TRANSITORIOS:
        logger.warning("Error transitorio %s en %s: %s", codigo, modelo, cuerpo_texto[:200])
        if (
            ctx.intento == 0
            and ctx.idx_modelo == 0
            and ctx.tiempo_restante > TIEMPO_RESTANTE_MINIMO_PARA_REINTENTO
        ):
            return None, "reintentar"
        return None, "fallback"

    logger.error("Error no manejado %s en %s: %s", codigo, modelo, cuerpo_texto[:200])
    return None, "fallback"
