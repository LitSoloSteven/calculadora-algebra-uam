"""Composition root de la interfaz web de Scalaris."""
import os
from nicegui import app, ui
from src.frontend.routes import register_routes
from src.frontend.theme import setup_theme  # Reexport para compatibilidad

_initialized = False


def init_app():
    """Inicializa archivos estáticos y registro de rutas."""
    global _initialized
    if _initialized:
        return
    app.add_static_files('/assets', 'src/frontend/assets')
    register_routes()
    _initialized = True


def run():
    """Punto de arranque del servidor web de Scalaris."""
    init_app()
    ui.run(
        title="Scalaris",
        favicon="src/frontend/assets/LogoOscuro.png",
        storage_secret=os.getenv("STORAGE_SECRET"),
    )


if __name__ in {"__main__", "__mp_main__"}:
    from dotenv import load_dotenv
    load_dotenv(".env")
    load_dotenv("src/ai/.env")
    run()