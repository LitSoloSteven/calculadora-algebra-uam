from src.frontend.navigation import HUB_ROUTE
from src.frontend.components.navbar import create_navbar


def create_app_shell(active_ui=None, active_route='/', active_key=None):
    """Envoltura principal de la aplicacion que genera la barra superior contextual."""
    if active_route != HUB_ROUTE:
        create_navbar(active_ui, active_route=active_route, active_key=active_key)
