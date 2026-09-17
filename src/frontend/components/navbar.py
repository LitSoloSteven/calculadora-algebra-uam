from nicegui import ui

def create_navbar():
    # Header flotante estilo píldora neumórfica
    with ui.header().classes('px-6 py-4 flex justify-center w-full bg-transparent').props('reveal'):
        with ui.row().classes('panel-card rounded-full px-8 py-2 flex items-center justify-between gap-8'):
            
            # Secciones principales
            with ui.row().classes('items-center gap-4'):
                # 1. Sistemas Lineales
                ui.button(icon='calculate', on_click=lambda: ui.navigate.to('/sistemas-lineales')) \
                    .classes('btn-neo-icon text-main').props('ripple=false flat aria-label="Sistemas Lineales"').tooltip('Sistemas Lineales')
                    
                # 2. Operaciones con Matrices
                ui.button(icon='grid_view', on_click=lambda: ui.navigate.to('/operaciones-matrices')) \
                    .classes('btn-neo-icon text-main').props('ripple=false flat aria-label="Operaciones con Matrices"').tooltip('Operaciones con Matrices')

                # 3. Conversor de Bases Numéricas
                ui.button(icon='sync_alt', on_click=lambda: ui.navigate.to('/conversor')) \
                    .classes('btn-neo-icon text-main').props('ripple=false flat aria-label="Conversor"').tooltip('Conversor de Bases')
                
                # 4. Tutor IA
                ui.button(icon='smart_toy', on_click=lambda: ui.navigate.to('/ia')) \
                    .classes('btn-neo-icon text-main').props('ripple=false flat aria-label="Tutor IA"').tooltip('Tutor IA')
                
            # Separador vertical sutil
            ui.html('<div class="h-6 w-px opacity-20" style="background-color: var(--text-sec);"></div>')
            
            # Acciones (Selector de temas)
            with ui.row().classes('items-center'):
                with ui.button(icon='palette').classes('btn-neo-icon text-main').props('ripple=false flat').tooltip('Seleccionar Tema'):
                    with ui.menu().classes('p-2'):
                        ui.menu_item('Tema Claro', on_click=lambda: ui.run_javascript("setTheme('claro')")).classes('rounded-lg mb-1')
                        ui.menu_item('Tema Aqua', on_click=lambda: ui.run_javascript("setTheme('aqua')")).classes('rounded-lg mb-1')
                        ui.menu_item('Tema Oscuro', on_click=lambda: ui.run_javascript("setTheme('oscuro')")).classes('rounded-lg')