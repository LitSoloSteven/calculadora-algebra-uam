"""Punto de composición y arranque del servidor web de Scalaris."""
import logging
import os
from typing import Mapping
from nicegui import app, ui

from src.frontend.routes import registrar_rutas
from src.frontend.textos import (
    MSJ_ERROR_PRODUCCION_SIN_SECRETO,
    MSJ_SECRETO_DEV_INSEGURO,
)
from src.frontend.theme import setup_theme  # Reexport para compatibilidad

logger = logging.getLogger(__name__)

_INICIALIZADO: bool = False


def resolver_secreto_almacenamiento(variables_entorno: Mapping[str, str]) -> str:
    """Resuelve la clave de cifrado para almacenamiento de sesión de NiceGUI.

    Raises:
        SystemExit: si el entorno es producción y falta STORAGE_SECRET.
    """
    entorno = variables_entorno.get("SCALARIS_ENV", "").strip().lower()
    secreto = variables_entorno.get("STORAGE_SECRET", "").strip()

    if entorno == "production":
        if not secreto:
            raise SystemExit(MSJ_ERROR_PRODUCCION_SIN_SECRETO)
        return secreto

    if not secreto:
        logger.warning(MSJ_SECRETO_DEV_INSEGURO)
        return "scalaris_dev_secret_key"

    return secreto


def inicializar_aplicacion() -> None:
    """Configura los archivos estáticos y registra las rutas de la aplicación."""
    global _INICIALIZADO
    if _INICIALIZADO:
        return

    entorno = os.environ.get("SCALARIS_ENV", "").strip().lower()
    max_edad_cache = 3600 if entorno == "production" else 0
    app.add_static_files("/assets", "src/frontend/assets", max_cache_age=max_edad_cache)
    registrar_rutas()
    _INICIALIZADO = True


def ejecutar() -> None:
    """Inicia el bucle principal de servicio de la interfaz web."""
    inicializar_aplicacion()
    secreto = resolver_secreto_almacenamiento(os.environ)
    ui.run(
        title="Scalaris",
        favicon="src/frontend/assets/LogoOscuro.png",
        storage_secret=secreto,
    )


if __name__ in {"__main__", "__mp_main__"}:
    from dotenv import load_dotenv

    load_dotenv(".env")
    load_dotenv("src/ai/.env")
    ejecutar()