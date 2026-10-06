"""Composition root de la interfaz web de Scalaris."""
import os
import logging
from nicegui import app, ui
from src.frontend.routes import register_routes
from src.frontend.theme import setup_theme  # Reexport para compatibilidad

logger = logging.getLogger(__name__)

def resolve_storage_secret(env) -> str:
    env_name = env.get("SCALARIS_ENV", "").strip().lower()
    secret = env.get("STORAGE_SECRET", "").strip()
    
    if env_name == "production":
        if not secret:
            raise SystemExit("ERROR CRÍTICO: SCALARIS_ENV es production pero falta STORAGE_SECRET.")
        return secret
        
    if not secret:
        logger.warning("STORAGE_SECRET ausente. Usando secreto de desarrollo (inseguro).")
        return "scalaris_dev_secret_key"
        
    return secret

_initialized = False


def init_app():
    """Inicializa archivos estáticos y registro de rutas."""
    global _initialized
    if _initialized:
        return
    env_name = os.environ.get("SCALARIS_ENV", "").strip().lower()
    max_cache_age = 3600 if env_name == "production" else 0
    app.add_static_files('/assets', 'src/frontend/assets', max_cache_age=max_cache_age)
    register_routes()
    _initialized = True


def run():
    """Punto de arranque del servidor web de Scalaris."""
    init_app()
    secret = resolve_storage_secret(os.environ)
    ui.run(
        title="Scalaris",
        favicon="src/frontend/assets/LogoOscuro.png",
        storage_secret=secret,
    )


if __name__ in {"__main__", "__mp_main__"}:
    from dotenv import load_dotenv
    load_dotenv(".env")
    load_dotenv("src/ai/.env")
    run()