from nicegui import ui

def create_navbar():
    with ui.footer().classes('bg-transparent p-6 flex justify-center items-center z-50').style('border: none;'):
        with ui.row().classes('neu-flat px-8 py-3 items-center gap-8'):
            
            ui.button(icon='calculate', on_click=lambda: ui.navigate.to('/gauss'), color=None) \
                .classes('neu-btn w-14 h-14 rounded-full').tooltip('Gauss')
                
            ui.button(icon='functions', on_click=lambda: ui.navigate.to('/gauss-jordan'), color=None) \
                .classes('neu-btn w-14 h-14 rounded-full').tooltip('Gauss-Jordan')
                
            ui.button(icon='palette', on_click=lambda: ui.run_javascript("toggleTheme()"), color=None) \
                .classes('neu-btn w-14 h-14 rounded-full').tooltip('Cambiar Tema')
                
            ui.label('Álgebra UAM').classes('text-lg font-bold tracking-wide ml-4')