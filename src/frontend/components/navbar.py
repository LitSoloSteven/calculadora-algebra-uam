from nicegui import ui
from src.frontend.components.icons import icon_svg

def create_navbar(active_ui=None, active_route='/'):
    # Header flotante estilo píldora neumórfica
    with ui.header().classes('px-2 sm:px-6 py-2 sm:py-4 flex justify-center w-full bg-transparent').style('view-transition-name: navbar;').props('reveal'):
        with ui.row().classes('panel-card rounded-full px-4 sm:px-8 py-2 flex items-center justify-between gap-4 sm:gap-8 overflow-x-auto no-wrap max-w-full'):
            
            # Secciones principales
            with ui.row().classes('items-center gap-4'):
                
                def btn_styles(route):
                    is_active = active_route == route
                    color = 'var(--accent)' if is_active else 'var(--text-main)'
                    shadow = 'var(--elev-inset)' if is_active else 'var(--elev-2)'
                    return f'color: {color} !important; box-shadow: {shadow} !important;'
                
                # 1. Sistemas Lineales
                with ui.button(on_click=lambda: ui.navigate.to('/sistemas-lineales'), color=None).classes('btn-neo-icon p-0').style(btn_styles('/sistemas-lineales')).props('flat ripple=false aria-label="Sistemas Lineales"').tooltip('Sistemas Lineales'):
                    ui.html(icon_svg('sistemas_lineales'))
                    
                # 2. Operaciones con Matrices
                with ui.button(on_click=lambda: ui.navigate.to('/operaciones-matrices'), color=None).classes('btn-neo-icon p-0').style(btn_styles('/operaciones-matrices')).props('flat ripple=false aria-label="Operaciones con Matrices"').tooltip('Operaciones con Matrices'):
                    ui.html(icon_svg('operaciones_matrices'))

                # 3. Conversor de Bases Numéricas
                with ui.button(on_click=lambda: ui.navigate.to('/conversor'), color=None).classes('btn-neo-icon p-0').style(btn_styles('/conversor')).props('flat ripple=false aria-label="Conversor"').tooltip('Conversor de Bases'):
                    ui.html(icon_svg('conversor_bases'))
                
                # 4. Tutor IA
                def toggle_ai_panel():
                    if active_ui and hasattr(active_ui, 'ai_panel'):
                        active_ui.ai_panel.toggle()
                        
                with ui.button(on_click=toggle_ai_panel, color=None).classes('btn-neo-icon p-0 text-main').props('flat ripple=false aria-label="Tutor IA"').tooltip('Tutor IA'):
                    ui.html(icon_svg('tutor_ia'))
                
            # Separador vertical sutil
            ui.html('<div class="h-6 w-px opacity-20" style="background-color: var(--text-sec);"></div>')
            
            # Acciones (Selector de temas)
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

                        # Inject logic to show checkmark on the active theme
                        ui.add_head_html('''
                        <style>
                            html[data-theme="papel"] { --show-papel: block; }
                            html[data-theme="marea"] { --show-marea: block; }
                            html[data-theme="medianoche"] { --show-medianoche: block; }
                        </style>
                        <script>
                            function setTheme(t) { applyTheme(t); }
                        </script>
                        ''')