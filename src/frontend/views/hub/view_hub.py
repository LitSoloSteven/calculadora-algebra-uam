import html
from nicegui import ui
from src.frontend.components.app_shell import create_app_shell
from src.frontend.components.ai_panel import AIPanel
from src.frontend.components.icons import icon_svg
from src.frontend.navigation import HUB_ROUTE, nav_groups
from ._recent import normalize_recent

class HubUI:
    def __init__(self, glosa_open: bool = False):
        self.glosa_open = glosa_open
        self.ai_panel = None
        self.recent_container = None

    async def build(self, client):
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=HUB_ROUTE)
        
        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4 gap-8 hub-root view-root'):
            ui.label("Scalaris").classes('text-2xl font-bold text-main')
            ui.label("Álgebra lineal y utilidades numéricas, con cada paso a la vista.").classes('fs-small text-sec')
            
            ui.label("Continuar").classes('hub-section-title')
            self.recent_container = ui.row().classes('w-full')
            with self.recent_container:
                ui.skeleton().classes('w-full h-[56px]')
            
            with ui.element('div').classes('hub-cols'):
                groups = nav_groups()
                if groups:
                    # Primera columna: primer pilar
                    pilar1, tools1 = groups[0]
                    with ui.column().classes('hub-col'):
                        with ui.column().classes('panel-card hub-pillar'):
                            ui.label(pilar1.name).classes('hub-section-title')
                            for tool in tools1:
                                with ui.link(target=tool.route).classes('hub-row'):
                                    ui.html(icon_svg(tool.icon)).classes('hub-row-icon')
                                    ui.label(tool.name).classes('hub-row-name')
                                    ui.label(tool.descriptor).classes('hub-row-desc')
                                    if tool.example_latex:
                                        ui.html(f'<div class="math-scroll-container math-label hub-row-formula">$$ {html.escape(tool.example_latex)} $$</div>')
                    
                    # Segunda columna: el resto
                    if len(groups) > 1:
                        with ui.column().classes('hub-col'):
                            for pilar, tools in groups[1:]:
                                with ui.column().classes('panel-card hub-pillar'):
                                    ui.label(pilar.name).classes('hub-section-title')
                                    for tool in tools:
                                        with ui.link(target=tool.route).classes('hub-row'):
                                            ui.html(icon_svg(tool.icon)).classes('hub-row-icon')
                                            ui.label(tool.name).classes('hub-row-name')
                                            ui.label(tool.descriptor).classes('hub-row-desc')
                                            if tool.example_latex:
                                                ui.html(f'<div class="math-scroll-container math-label hub-row-formula">$$ {html.escape(tool.example_latex)} $$</div>')
                                                
        self.ai_panel.build()
        if self.glosa_open:
            self.ai_panel.open()
            
        await client.connected()
        try:
            res = await ui.run_javascript("return window.scalarisReadRecent ? window.scalarisReadRecent() : {ok:false, ids:[]};", timeout=3.0)
        except Exception:
            res = None
            
        self.recent_container.clear()
        with self.recent_container:
            if not isinstance(res, dict) or not res.get('ok'):
                with ui.element('div').classes('hub-empty'):
                    ui.icon('info').classes('text-2xl')
                    ui.label('No pudimos leer tu historial en este navegador. Puedes seguir usando todas las herramientas.')
            else:
                recent_tools = normalize_recent(res.get('ids'))
                if not recent_tools:
                    with ui.element('div').classes('hub-empty'):
                        ui.icon('explore').classes('text-2xl')
                        ui.label('Aún no has abierto ninguna herramienta').classes('font-bold text-main')
                        ui.label('Elige una de las de abajo y aparecerá aquí para que la retomes en un clic.')
                else:
                    with ui.element('div').classes('hub-recent-list'):
                        for tool in recent_tools:
                            with ui.link(target=tool.route).classes('hub-recent-item'):
                                ui.html(icon_svg(tool.icon))
                                ui.label(tool.name)
                                
        ui.run_javascript('typesetMathWhenReady();')
