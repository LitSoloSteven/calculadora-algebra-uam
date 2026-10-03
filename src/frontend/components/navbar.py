from nicegui import ui
from src.frontend.components.icons import icon_svg
from src.frontend.navigation import NAV_FLAT_ORDER, tool_by_id


def create_navbar(active_ui=None, active_route='/'):
    # Header flotante: Logo en la esquina izquierda y píldora neumórfica centrada
    with ui.header().classes('px-4 sm:px-8 py-2 sm:py-4 flex items-center justify-center w-full bg-transparent relative pointer-events-none').style('view-transition-name: navbar;').props('reveal'):
        
        # Logo de Scalaris en la esquina izquierda de la vista (apunta a '/', reactivo al tema)
        with ui.link(target='/').classes(
            'brand-logo-link brand-corner-link pointer-events-auto absolute left-6 sm:left-10 top-1/2 -translate-y-1/2 flex items-center justify-center select-none no-underline transition-transform duration-200 hover:scale-105 active:scale-95 z-10'
        ).props('aria-label="Scalaris - Inicio"').tooltip('Scalaris — Inicio'):
            ui.html('''
                <div class="brand-logo-container flex items-center justify-center" style="width: 72px; height: 72px;">
                    <img src="/assets/LogoOscuro.png" alt="Scalaris" class="brand-logo brand-logo-dark" style="height: 72px; width: 72px; object-fit: contain;" />
                    <img src="/assets/LogoClaro.png" alt="Scalaris" class="brand-logo brand-logo-light" style="height: 72px; width: 72px; object-fit: contain;" />
                </div>
            ''')

        # Píldora de navegación centrada (limpia, sin el logo interno)
        with ui.row().classes('panel-card rounded-full px-4 sm:px-8 py-2 flex items-center justify-between gap-4 sm:gap-8 overflow-x-auto no-wrap max-w-full pointer-events-auto'):
            
            # Secciones principales
            with ui.row().classes('items-center gap-4'):
                # Orden plano temporal idéntico al actual; se elimina en F2
                for tool_id in NAV_FLAT_ORDER:
                    tool = tool_by_id(tool_id)
                    is_active = (active_route == tool.route)
                    color = 'var(--accent)' if is_active else 'var(--text-main)'
                    shadow = 'var(--elev-inset)' if is_active else 'var(--elev-2)'
                    style_str = f'color: {color} !important; box-shadow: {shadow} !important;'
                    
                    aria_current = ' aria-current="page"' if is_active else ''
                    props_str = f'flat ripple=false href="{tool.route}" aria-label="{tool.name}"{aria_current}'
                    
                    with ui.button(color=None).classes('btn-neo-icon p-0').style(style_str).props(props_str).tooltip(tool.name):
                        ui.html(icon_svg(tool.icon))
                
                # Tutor IA (sin cambios)
                def toggle_ai_panel():
                    if active_ui and hasattr(active_ui, 'ai_panel'):
                        active_ui.ai_panel.toggle()
                        
                with ui.button(on_click=toggle_ai_panel, color=None).classes('btn-neo-icon p-0 text-main').props('flat ripple=false aria-label="Tutor IA"').tooltip('Tutor IA'):
                    ui.html(icon_svg('tutor_ia'))
                
            # Separador vertical sutil (sin cambios)
            ui.html('<div class="h-6 w-px opacity-20" style="background-color: var(--text-sec);"></div>')
            
            # Acciones (Selector de temas, sin cambios)
            with ui.row().classes('items-center'):
                with ui.button(color=None).classes('btn-neo-icon p-0 text-main').props('flat ripple=false').tooltip('Seleccionar Tema'):
                    ui.html(icon_svg('temas'))
                    with ui.menu().classes('p-2 min-w-[150px]'):
                        
                        def menu_item(label, theme_id, bg_color):
                            with ui.menu_item(on_click=lambda t=theme_id: ui.run_javascript(f"setTheme('{t}')")).classes('rounded-lg mb-1 flex items-center gap-3 w-full'):
                                ui.html(f'<div style="width: 14px; height: 14px; border-radius: 50%; background-color: {bg_color}; border: 1px solid var(--border-input);"></div>')
                                ui.label(label).classes('flex-1')
                                ui.html(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; display: var(--show-{theme_id}, none); color: var(--accent);"><polyline points="20 6 9 17 4 12"></polyline></svg>''')

                        menu_item('Papel', 'papel', '#F2F0EB')
                        menu_item('Marea', 'marea', '#EDF2F8')
                        menu_item('Medianoche', 'medianoche', '#082338')

                        # Inject logic to show checkmark on the active theme and brand logo styling
                        ui.add_head_html('''
                        <style>
                            html[data-theme="papel"] { --show-papel: block; }
                            html[data-theme="marea"] { --show-marea: block; }
                            html[data-theme="medianoche"] { --show-medianoche: block; }

                            /* Brand Logo switching */
                            .brand-logo-light { display: none !important; }
                            .brand-logo-dark { display: block !important; }
                            html[data-theme="medianoche"] .brand-logo-light { display: block !important; }
                            html[data-theme="medianoche"] .brand-logo-dark { display: none !important; }
                        </style>
                        ''')