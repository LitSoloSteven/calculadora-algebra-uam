from nicegui import ui
from src.frontend import flags
from src.frontend.navigation import breadcrumb
from src.frontend.components.navbar import create_navbar

def create_app_shell(active_ui=None, active_route='/'):
    create_navbar(active_ui, active_route=active_route)
    
    if flags.nav_v2():
        crumbs = breadcrumb(active_route)
        if crumbs:
            with ui.element('nav').classes('crumbs').props('aria-label="Migas de pan"'):
                pillar_name = crumbs[0][0]
                tool_name = crumbs[1][0]
                
                ui.label(pillar_name).classes('crumb')
                ui.label('/').classes('crumb-sep').props('aria-hidden=true')
                ui.label(tool_name).classes('crumb').props('aria-current="page"')
