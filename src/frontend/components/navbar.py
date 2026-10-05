import json
from nicegui import ui
from src.frontend.components.icons import icon_svg
from src.frontend import flags
from src.frontend.navigation import (
    NAV_FLAT_ORDER, tool_by_id, HUB_ENABLED, HUB_ROUTE, 
    nav_groups, pillar_for_route, tool_by_route
)

def create_navbar(active_ui=None, active_route='/'):
    with ui.header().classes('px-4 sm:px-8 py-2 sm:py-4 flex items-center justify-center w-full bg-transparent relative pointer-events-none').style('view-transition-name: navbar;').props('reveal'):
        
        with ui.link(target='/').classes(
            'brand-logo-link brand-corner-link pointer-events-auto absolute left-6 sm:left-10 top-1/2 -translate-y-1/2 flex items-center justify-center select-none no-underline z-10'
        ).props('aria-label="Scalaris - Inicio"').tooltip('Scalaris: Inicio'):
            ui.html('''
                <div class="brand-logo-container flex items-center justify-center" style="width: 72px; height: 72px;">
                    <img src="/assets/LogoOscuro.png" alt="Scalaris" class="brand-logo brand-logo-dark" style="height: 72px; width: 72px; object-fit: contain;" />
                    <img src="/assets/LogoClaro.png" alt="Scalaris" class="brand-logo brand-logo-light" style="height: 72px; width: 72px; object-fit: contain;" />
                </div>
            ''')

        with ui.row().classes('panel-card rounded-full px-4 sm:px-8 py-2 flex items-center justify-between gap-4 sm:gap-8 overflow-x-auto no-wrap max-w-full pointer-events-auto'):
            
            with ui.row().classes('items-center gap-4'):
                if not flags.nav_v2():
                    for tool_id in NAV_FLAT_ORDER:
                        tool = tool_by_id(tool_id)
                        is_active = (active_route == tool.route)
                        aria_current = ' aria-current="page"' if is_active else ''
                        props_str = f'flat ripple=false href="{tool.route}" aria-label="{tool.name}"{aria_current}'
                        
                        with ui.button(color=None).classes('btn-neo-icon p-0' + (' nav-active' if is_active else '')).props(props_str).tooltip(tool.name):
                            ui.html(icon_svg(tool.icon))
                else:
                    if HUB_ENABLED:
                        current = (active_route == HUB_ROUTE)
                        with ui.button(color=None).classes('nav-trigger' + (' nav-active' if current else '')).props(
                            f'flat ripple=false no-caps aria-label="Inicio" href="{HUB_ROUTE}"' + (' aria-current="page"' if current else '')
                        ).tooltip('Inicio'):
                            ui.html(icon_svg('inicio'))
                            
                        ui.element('div').classes('nav-sep')
                    
                    active_pillar = pillar_for_route(active_route)
                    for pillar, tools in nav_groups():
                        btn = ui.button(color=None).classes('nav-trigger' + (' nav-active' if active_pillar and active_pillar.id == pillar.id else '')).props(f'flat ripple=false no-caps aria-haspopup="menu" aria-expanded="false" aria-label="{pillar.name}"')
                        with btn:
                            ui.html(icon_svg(pillar.icon))
                            ui.label(pillar.short_name).classes('nav-label')
                            m = ui.menu().classes('nav-menu')
                            m.on('show', lambda _, b=btn: b.props('aria-expanded="true"'))
                            m.on('hide', lambda _, b=btn: b.props('aria-expanded="false"'))
                            with m:
                                for tool in tools:
                                    current_tool = (tool.route == active_route)
                                    with ui.menu_item().classes('nav-menu-item').props(f'href="{tool.route}"' + (' aria-current="page"' if current_tool else '')):
                                        ui.html(icon_svg(tool.icon)).classes('nav-menu-icon')
                                        with ui.element('div').classes('nav-menu-text'):
                                            ui.label(tool.name).classes('nav-menu-name')
                                            ui.label(tool.descriptor).classes('nav-menu-desc')
                                            
                        ui.element('div').classes('nav-sep')
                    
                if not flags.dock_enabled():
                    def toggle_ai_panel():
                        if active_ui and hasattr(active_ui, 'ai_panel'):
                            active_ui.ai_panel.toggle()
                            
                    with ui.button(on_click=toggle_ai_panel, color=None).classes('btn-neo-icon p-0 text-main').props('flat ripple=false aria-label="Glosa"').tooltip('Glosa'):
                        ui.html(icon_svg('tutor_ia'))
                
            ui.element('div').classes('nav-sep')
            
            with ui.row().classes('items-center'):
                theme_btn = ui.button(color=None).classes('btn-neo-icon p-0 text-main').props('flat ripple=false aria-label="Seleccionar Tema" aria-haspopup="menu" aria-expanded="false"').tooltip('Seleccionar Tema')
                with theme_btn:
                    ui.html(icon_svg('temas'))
                    theme_menu = ui.menu().classes('p-2 min-w-[150px]')
                    theme_menu.on('show', lambda _, b=theme_btn: b.props('aria-expanded="true"'))
                    theme_menu.on('hide', lambda _, b=theme_btn: b.props('aria-expanded="false"'))
                    with theme_menu:
                        def menu_item(label, theme_id, bg_color):
                            with ui.menu_item(on_click=lambda t=theme_id: ui.run_javascript(f"setTheme('{t}')")).classes('rounded-lg mb-1 flex items-center gap-3 w-full'):
                                ui.html(f'<div style="width: 14px; height: 14px; border-radius: 50%; background-color: {bg_color}; border: 1px solid var(--border-input);"></div>')
                                ui.label(label).classes('flex-1')
                                ui.html(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; display: var(--show-{theme_id}, none); color: var(--accent);"><polyline points="20 6 9 17 4 12"></polyline></svg>''')

                        menu_item('Papel', 'papel', '#F2F0EB')
                        menu_item('Marea', 'marea', '#EDF2F8')
                        menu_item('Medianoche', 'medianoche', '#082338')

    if flags.nav_v2():
        active_tool = tool_by_route(active_route)
        if active_tool is not None:
            ui.add_body_html('<script>window.scalarisRecordVisit && window.scalarisRecordVisit(' + json.dumps(active_tool.id) + ');</script>')