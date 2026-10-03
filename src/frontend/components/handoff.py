import secrets
import threading
import time
from dataclasses import dataclass

from nicegui import ui

from src.frontend.navigation import tool_by_id
from src.backend.utils.matrix_validator import MatrixValidator


TTL_SECONDS = 120
_MAX_ENTRIES = 64
_STORE: dict[str, tuple[float, dict]] = {}
_LOCK = threading.Lock()


def _now() -> float:
    return time.monotonic()


def put_matrix(source_id: str, data: list[list[str]]) -> str:
    token = secrets.token_urlsafe(16)
    payload = {"v": 1, "kind": "matrix_A", "source": source_id, "data": data}
    
    with _LOCK:
        now = _now()
        expired = [k for k, (ts, _) in _STORE.items() if now - ts > TTL_SECONDS]
        for k in expired:
            del _STORE[k]
        
        if len(_STORE) >= _MAX_ENTRIES:
            oldest = min(_STORE.keys(), key=lambda k: _STORE[k][0])
            del _STORE[oldest]
            
        _STORE[token] = (now, payload)
        
    return token


def handoff_url(route: str, token: str) -> str:
    return f"{route}?handoff={token}"


def validate_matrix_payload(payload, *, max_n: int) -> tuple[list[list[str]] | None, str | None]:
    if not isinstance(payload, dict):
        return None, "Los datos recibidos no son válidos, así que empezamos con la herramienta vacía."
    if payload.get("v") != 1 or payload.get("kind") != "matrix_A" or not isinstance(payload.get("source"), str):
        return None, "Los datos recibidos no son válidos, así que empezamos con la herramienta vacía."
    
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return None, "Los datos recibidos no son válidos, así que empezamos con la herramienta vacía."
    
    n = len(data)
    for row in data:
        if not isinstance(row, list) or len(row) != n:
            return None, "Los datos recibidos no son válidos, así que empezamos con la herramienta vacía."
            
    if n > max_n:
        return None, f"La matriz es de {n}×{n} y esta herramienta admite hasta {max_n}×{max_n}. Empezamos con la herramienta vacía."
        
    for row in data:
        for cell in row:
            if not isinstance(cell, str) or not (1 <= len(cell) <= 64):
                return None, "Los datos recibidos no son válidos, así que empezamos con la herramienta vacía."
            try:
                MatrixValidator.parse_number_exact(cell)
            except Exception:
                return None, "Los datos recibidos no son válidos, así que empezamos con la herramienta vacía."
                
    return data, None


@dataclass(frozen=True)
class HandoffResult:
    status: str
    data: list[list[str]] | None
    source_name: str
    message: str


def consume_matrix(token: str, *, max_n: int) -> HandoffResult | None:
    if not token:
        return None
        
    with _LOCK:
        entry = _STORE.pop(token, None)
        
    if entry is None:
        return HandoffResult(
            status='missing',
            data=None,
            source_name='',
            message="No encontramos los datos que ibas a traer. Ya los usaste o el enlace es antiguo. Puedes capturar la matriz aquí."
        )
        
    ts, payload = entry
    if _now() - ts > TTL_SECONDS:
        return HandoffResult(
            status='expired',
            data=None,
            source_name='',
            message="Los datos tardaron demasiado en llegar y expiraron. Vuelve a la herramienta de origen y repite la acción."
        )
        
    try:
        source_name = tool_by_id(payload["source"]).name
    except KeyError:
        source_name = "otra herramienta"
        
    data, error_msg = validate_matrix_payload(payload, max_n=max_n)
    if error_msg is not None:
        return HandoffResult(
            status='invalid',
            data=None,
            source_name=source_name,
            message=error_msg
        )
        
    return HandoffResult(
        status='ok',
        data=data,
        source_name=source_name,
        message=""
    )


def render_handoff_notice(result: HandoffResult, success_message: str) -> None:
    if result.status == 'ok':
        with ui.row().classes('handoff-note').props('role=status'):
            ui.icon('check_circle').classes('text-accent')
            ui.label(success_message)
    else:
        with ui.row().classes('items-center gap-2 px-4 py-2 badge-warning w-fit').props('role=status'):
            ui.icon('warning_amber')
            ui.label(result.message)


def clean_handoff_url() -> None:
    ui.timer(0.2, lambda: ui.run_javascript("(()=>{const u=new URL(location.href);u.searchParams.delete('handoff');history.replaceState(null,'',u.pathname+u.search+u.hash);})()"), once=True)
