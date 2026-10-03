import os
import time
import requests
import threading
import json
import hashlib
from enum import Enum
from dataclasses import dataclass
from dotenv import load_dotenv
import logging

from src.ai.prompts import build_messages, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

load_dotenv(".env")
load_dotenv("src/ai/.env")

class AIErrorKind(str, Enum):
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
    ok: bool
    text: str
    kind: AIErrorKind | None = None
    model: str | None = None
    cached: bool = False

# Caché LRU a nivel de clase
_cache_lock = threading.Lock()
_response_cache = {}  # sha256 -> (resultado, timestamp)

class OpenRouterIA:
    PRIMARY_MODEL = os.getenv("OPENROUTER_PRIMARY_MODEL", "nex-agi/nex-n2.5-pro:free")
    FALLBACK_MODELS = [m.strip() for m in os.getenv("OPENROUTER_FALLBACK_MODELS", "").split(",") if m.strip()]
    
    TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526}

    # Inyección de dependencias para testing
    _time_monotonic = time.monotonic
    _time_sleep = time.sleep
    _requests_post = staticmethod(requests.post)

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def _get_cache_key(self, question: str, context_block: str, simpler: bool, models: list[str]) -> str:
        data = f"{question}|{context_block}|{simpler}|{','.join(models)}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def _call_model(self, model: str, messages: list, timeout: tuple) -> requests.Response:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://calculadora-algebra-uam.local",
            "X-Title": "Calculadora Algebra Lineal UAM",
        }
        data = {
            "model": model,
            "messages": messages,
        }
        return self._requests_post(self.url, headers=headers, json=data, timeout=timeout)

    def ask(self, question: str, history: list = None, *, context_block: str = None, 
            cancel: threading.Event = None, cacheable: bool = False, simpler: bool = False) -> AIResult:
        
        if not self.api_key:
            return AIResult(False, "Glosa no está configurada en este servidor. Avisa a quien administra Scalaris.", AIErrorKind.NO_KEY)

        if history is None:
            history = []
            
        modelos_a_intentar = [self.PRIMARY_MODEL]
        if self.FALLBACK_MODELS:
            modelos_a_intentar.append(self.FALLBACK_MODELS[0])

        if cacheable:
            cache_key = self._get_cache_key(question, context_block, simpler, modelos_a_intentar)
            with _cache_lock:
                # Cleanup and check cache
                now = self._time_monotonic()
                keys_to_delete = [k for k, v in _response_cache.items() if now - v[1] > 3600]
                for k in keys_to_delete:
                    del _response_cache[k]
                    
                if cache_key in _response_cache:
                    cached_res, _ = _response_cache[cache_key]
                    return AIResult(True, cached_res.text, model=cached_res.model, cached=True)

        messages = build_messages(history, question, context_block, simpler=simpler)
        
        deadline = self._time_monotonic() + 40.0
        
        for idx, modelo in enumerate(modelos_a_intentar):
            max_intentos = 2 if idx == 0 else 1 # El primario permite 2 intentos (backoff), fallback 1
            
            for intento in range(max_intentos):
                if cancel and cancel.is_set():
                    return AIResult(False, "Operación cancelada", AIErrorKind.CANCELLED)
                    
                time_left = deadline - self._time_monotonic()
                if time_left < 2.0:
                    break
                    
                connect_timeout = min(5.0, time_left)
                read_timeout = min(25.0, time_left)
                
                try:
                    response = self._call_model(modelo, messages, timeout=(connect_timeout, read_timeout))
                    
                    if cancel and cancel.is_set():
                        return AIResult(False, "Operación cancelada", AIErrorKind.CANCELLED)
                        
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            choices = data.get("choices") or []
                            content = (choices[0].get("message") or {}).get("content") if choices else None
                            if content:
                                res = AIResult(True, content, model=modelo)
                                if cacheable:
                                    with _cache_lock:
                                        if len(_response_cache) >= 128:
                                            oldest = min(_response_cache.keys(), key=lambda k: _response_cache[k][1])
                                            del _response_cache[oldest]
                                        _response_cache[cache_key] = (res, self._time_monotonic())
                                return res
                            else:
                                logger.error(f"AI response EMPTY. Status 200 sin choices. Modelo: {modelo}")
                                return AIResult(False, "Glosa no devolvió una respuesta. Reformula la pregunta o inténtalo de nuevo.", AIErrorKind.EMPTY)
                        except Exception as e:
                            logger.error(f"Error parseando json de AI: {e}")
                            
                    elif response.status_code in {401, 403}:
                        logger.error(f"Auth error OpenRouter: {response.status_code} - {response.text[:200]}")
                        return AIResult(False, "Glosa no pudo autenticarse con el servicio de IA. Avisa a quien administra Scalaris.", AIErrorKind.AUTH)
                        
                    elif response.status_code == 429:
                        logger.warning(f"Rate limit de OpenRouter: {response.status_code} en {modelo}")
                        if intento == 0 and idx == 0 and (deadline - self._time_monotonic()) > 8.0:
                            self._time_sleep(1.0)
                            continue
                        elif idx == 0 and len(modelos_a_intentar) > 1:
                            break # Pasar al fallback
                        else:
                            return AIResult(False, "Glosa está recibiendo muchas consultas ahora. Espera unos segundos y vuelve a intentarlo.", AIErrorKind.RATE_LIMIT)
                            
                    elif response.status_code in self.TRANSIENT_STATUS_CODES:
                        logger.warning(f"Error {response.status_code} en {modelo}: {response.text[:200]}")
                        if intento == 0 and idx == 0 and (deadline - self._time_monotonic()) > 8.0:
                            self._time_sleep(1.0)
                            continue
                        else:
                            break # Fallback o termina
                            
                    else:
                        logger.error(f"Error {response.status_code} en {modelo}: {response.text[:200]}")
                        break
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout al contactar {modelo}")
                    if idx == 0 and len(modelos_a_intentar) > 1:
                        break # Pasa a fallback
                    return AIResult(False, "Glosa tardó demasiado en responder. Vuelve a intentarlo en unos segundos.", AIErrorKind.TIMEOUT)
                except requests.exceptions.ConnectionError:
                    logger.error(f"Error de red al contactar {modelo}")
                    return AIResult(False, "No hay conexión con el servicio de IA. Revisa tu red y vuelve a intentarlo.", AIErrorKind.NETWORK)
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error de requests al contactar {modelo}: {e}")
                    break

        return AIResult(False, "Glosa no pudo responder ahora. Vuelve a intentarlo en un momento.", AIErrorKind.SERVICE)

    def analizar_sistema(self, prompt_text: str, history: list = None) -> tuple[bool, str]:
        # Envoltorio de compatibilidad
        result = self.ask(prompt_text, history=history)
        return result.ok, result.text