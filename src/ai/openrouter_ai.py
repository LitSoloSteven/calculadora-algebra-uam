"""Cliente para la API de OpenRouter con reintentos, caché y tolerancia a fallos."""

from dataclasses import dataclass
from enum import Enum
import hashlib
import logging
import os
import threading
import time

from dotenv import load_dotenv
import requests

from src.ai.clasificador_respuestas import (
    ContextoIntento,
    clasificar_error_http,
    procesar_respuesta_exitosa,
)
from src.ai.constantes import (
    CAPACIDAD_MAXIMA_CACHE, LIMITE_TIEMPO_TOTAL_SEGUNDOS, MODELO_PRIMARIO_DEFECTO,
    TIEMPO_ESPERA_REINTENTO_SEGUNDOS, TIEMPO_MINIMO_RESTANTE_SEGUNDOS,
    TIEMPO_VIDA_CACHE_SEGUNDOS, TIMEOUT_CONEXION_MAXIMO_SEGUNDOS,
    TIMEOUT_LECTURA_MAXIMO_SEGUNDOS, URL_OPENROUTER,
)
from src.ai.prompts import build_messages

logger = logging.getLogger(__name__)

load_dotenv(".env")
load_dotenv("src/ai/.env")


class AIErrorKind(str, Enum):
    """Categorías granulares de error al consultar el servicio de IA."""

    NO_KEY = "NO_KEY"
    AUTH = "AUTH"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    EMPTY = "EMPTY"
    NETWORK = "NETWORK"
    SERVICE = "SERVICE"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class AIResult:
    """Resultado inmutable de una consulta a Glosa."""

    ok: bool
    text: str
    kind: AIErrorKind | None = None
    model: str | None = None
    cached: bool = False


_bloqueo_cache = threading.Lock()
_cache_respuestas: dict[str, tuple[AIResult, float]] = {}


def _calcular_hash_cache(
    pregunta: str,
    bloque_contexto: str | None,
    mas_simple: bool,
    modelos: list[str],
) -> str:
    """Genera hash SHA-256 único para la combinación de parámetros de consulta."""
    datos = f"{pregunta}|{bloque_contexto}|{mas_simple}|{','.join(modelos)}"
    return hashlib.sha256(datos.encode("utf-8")).hexdigest()


def _leer_cache(clave_cache: str, ahora: float) -> AIResult | None:
    """Limpia entradas vencidas y devuelve resultado en caché si existe."""
    with _bloqueo_cache:
        expiradas = [
            k
            for k, v in _cache_respuestas.items()
            if ahora - v[1] > TIEMPO_VIDA_CACHE_SEGUNDOS
        ]
        for k in expiradas:
            del _cache_respuestas[k]

        if clave_cache in _cache_respuestas:
            res, _ = _cache_respuestas[clave_cache]
            return AIResult(True, res.text, model=res.model, cached=True)
    return None


def _guardar_en_cache(clave_cache: str, resultado: AIResult, ahora: float) -> None:
    """Almacena un resultado exitoso aplicando desalojo LRU al superar la capacidad."""
    with _bloqueo_cache:
        if len(_cache_respuestas) >= CAPACIDAD_MAXIMA_CACHE:
            mas_antiguo = min(_cache_respuestas.keys(), key=lambda k: _cache_respuestas[k][1])
            del _cache_respuestas[mas_antiguo]
        _cache_respuestas[clave_cache] = (resultado, ahora)


def _manejar_excepcion_red(
    exc: Exception, modelo: str, idx_modelo: int, total_modelos: int
) -> tuple[AIResult | None, bool]:
    """Clasifica errores de red y timeout devolviendo resultado o señal de fin."""
    if isinstance(exc, requests.exceptions.Timeout):
        logger.warning("Tiempo de espera agotado al contactar %s", modelo)
        if idx_modelo == 0 and total_modelos > 1:
            return None, False
        msg = "Glosa tardó demasiado en responder. Vuelve a intentarlo en unos segundos."
        return AIResult(False, msg, AIErrorKind.TIMEOUT), True
    if isinstance(exc, requests.exceptions.ConnectionError):
        logger.error("Error de conexión al contactar %s", modelo)
        msg = "No hay conexión con el servicio de IA. Revisa tu red y vuelve a intentarlo."
        return AIResult(False, msg, AIErrorKind.NETWORK), True
    logger.error("Excepción de red en %s: %s", modelo, exc)
    return None, False


class OpenRouterIA:
    """Cliente de comunicación con modelos de lenguaje vía OpenRouter."""

    MODELO_PRIMARIO = os.getenv("OPENROUTER_PRIMARY_MODEL", MODELO_PRIMARIO_DEFECTO)
    MODELOS_RESERVA = [
        m.strip()
        for m in os.getenv("OPENROUTER_FALLBACK_MODELS", "").split(",")
        if m.strip()
    ]

    _tiempo_monotonico = time.monotonic
    _tiempo_dormir = time.sleep
    _peticiones_post = staticmethod(requests.post)

    def __init__(self) -> None:
        """Inicializa credenciales y URL base del servicio."""
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.url = URL_OPENROUTER

    def _validar_precondiciones(
        self, cancel: threading.Event | None
    ) -> AIResult | None:
        """Valida estado de cancelación y disponibilidad de la clave API."""
        if cancel and cancel.is_set():
            return AIResult(False, "Operación cancelada", AIErrorKind.CANCELLED)
        if not self.api_key:
            msg = "Glosa no está configurada en este servidor. Avisa a quien administra Scalaris."
            return AIResult(False, msg, AIErrorKind.NO_KEY)
        return None

    def _ejecutar_llamada_red(
        self, modelo: str, mensajes: list, tiempo_restante: float
    ) -> requests.Response:
        """Emite petición HTTP POST a OpenRouter con timeouts dinámicos."""
        t_conn = min(TIMEOUT_CONEXION_MAXIMO_SEGUNDOS, tiempo_restante)
        t_read = min(TIMEOUT_LECTURA_MAXIMO_SEGUNDOS, tiempo_restante)
        cabeceras = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://calculadora-algebra-uam.local",
            "X-Title": "Calculadora Algebra Lineal UAM",
        }
        return self._peticiones_post(
            self.url,
            headers=cabeceras,
            json={"model": modelo, "messages": mensajes},
            timeout=(t_conn, t_read),
        )

    def _procesar_respuesta_intento(
        self,
        resp: requests.Response,
        modelo: str,
        ctx_intento: ContextoIntento,
    ) -> tuple[AIResult | None, str]:
        """Procesa código HTTP 200 u otros códigos de la respuesta recibida."""
        if resp.status_code == 200:
            return procesar_respuesta_exitosa(resp, modelo, AIResult, AIErrorKind), "exito"
        res, accion = clasificar_error_http(
            resp.status_code,
            resp.text,
            modelo,
            ctx_intento,
            ai_result_cls=AIResult,
            error_kind_cls=AIErrorKind,
        )
        return res, accion

    def _ejecutar_un_intento(
        self,
        modelo: str,
        mensajes: list,
        tiempo_restante: float,
        cancel: threading.Event | None,
        ctx: ContextoIntento,
    ) -> tuple[AIResult | None, str]:
        """Ejecuta una petición individual y clasifica su resultado o excepción."""
        try:
            resp = self._ejecutar_llamada_red(modelo, mensajes, tiempo_restante)
            if cancel and cancel.is_set():
                return AIResult(False, "Operación cancelada", AIErrorKind.CANCELLED), "terminar"
            return self._procesar_respuesta_intento(resp, modelo, ctx)
        except requests.exceptions.RequestException as e:
            res, terminar = _manejar_excepcion_red(e, modelo, ctx.idx_modelo, ctx.total_modelos)
            accion = "terminar" if (terminar or res) else "interrumpir"
            return res, accion

    def _intentar_modelo(
        self,
        modelo: str,
        mensajes: list,
        fecha_limite: float,
        cancel: threading.Event | None,
        config_intento: tuple[int, int, int],
    ) -> tuple[AIResult | None, bool]:
        """Ejecuta los intentos configurados para un modelo específico."""
        max_intentos, idx_modelo, total_modelos = config_intento
        for intento in range(max_intentos):
            if cancel and cancel.is_set():
                return AIResult(False, "Operación cancelada", AIErrorKind.CANCELLED), True

            tiempo_restante = fecha_limite - self._tiempo_monotonico()
            if tiempo_restante < TIEMPO_MINIMO_RESTANTE_SEGUNDOS:
                return None, True

            ctx = ContextoIntento(intento, idx_modelo, tiempo_restante, total_modelos)
            res, accion = self._ejecutar_un_intento(modelo, mensajes, tiempo_restante, cancel, ctx)
            if accion in ("exito", "terminar"):
                return res, True
            if accion == "reintentar":
                self._tiempo_dormir(TIEMPO_ESPERA_REINTENTO_SEGUNDOS)
                continue
            break

        return None, False

    def _paso_cache(
        self, question: str, context: str | None, simpler: bool, modelos: list[str]
    ) -> tuple[str, AIResult | None]:
        """Paso de caché: calcula hash y busca resultado existente si aplica."""
        clave = _calcular_hash_cache(question, context, simpler, modelos)
        return clave, _leer_cache(clave, self._tiempo_monotonico())

    def _paso_cascada_modelos(
        self,
        modelos: list[str],
        mensajes: list,
        cancel: threading.Event | None,
        clave_cache: str,
    ) -> AIResult:
        """Paso de intento por modelo: recorre los modelos hasta obtener respuesta."""
        fecha_limite = self._tiempo_monotonico() + LIMITE_TIEMPO_TOTAL_SEGUNDOS
        for idx, modelo in enumerate(modelos):
            max_intentos = 2 if idx == 0 else 1
            res, terminar = self._intentar_modelo(
                modelo, mensajes, fecha_limite, cancel, (max_intentos, idx, len(modelos))
            )
            if terminar and res:
                if res.ok and clave_cache:
                    _guardar_en_cache(clave_cache, res, self._tiempo_monotonico())
                return res
        return AIResult(
            False,
            "Glosa no pudo responder ahora. Vuelve a intentarlo en un momento.",
            AIErrorKind.SERVICE,
        )

    def ask(
        self,
        question: str,
        history: list | None = None,
        *,
        context_block: str | None = None,
        cancel: threading.Event | None = None,
        cacheable: bool = False,
        simpler: bool = False,
    ) -> AIResult:
        """Realiza una consulta a Glosa orquestando validación, caché y llamadas de red."""
        res_val = self._validar_precondiciones(cancel)
        if res_val:
            return res_val

        modelos = [self.MODELO_PRIMARIO]
        if self.MODELOS_RESERVA:
            modelos.append(self.MODELOS_RESERVA[0])

        clave_cache = ""
        if cacheable:
            clave_cache, res_cache = self._paso_cache(question, context_block, simpler, modelos)
            if res_cache:
                return res_cache

        mensajes = build_messages(history or [], question, context_block, simpler=simpler)
        return self._paso_cascada_modelos(modelos, mensajes, cancel, clave_cache)