from nicegui import ui

def create_navbar():
    # Trasladado a un header superior (desktop layout optimizado)
    with ui.header().classes('panel-card px-6 py-3 flex justify-between items-center z-50 mt-4 mx-6').props('flat bordered'):
        with ui.row().classes('items-center gap-4'):
            ui.label('Álgebra UAM').classes('text-xl font-medium tracking-wide').style('color: var(--text-main); font-weight: 500;')
            
        with ui.row().classes('items-center gap-4'):
            ui.button(icon='calculate', on_click=lambda: ui.navigate.to('/gauss')) \
                .classes('btn-ghost w-10 h-10 rounded-full p-0').props('ripple=false flat aria-label="Eliminación de Gauss"').tooltip('Eliminación de Gauss')
                
            ui.button(icon='functions', on_click=lambda: ui.navigate.to('/gauss-jordan')) \
                .classes('btn-ghost w-10 h-10 rounded-full p-0').props('ripple=false flat aria-label="Gauss-Jordan"').tooltip('Gauss-Jordan')
                
            ui.button(icon='palette', on_click=lambda: ui.run_javascript("toggleTheme()")) \
                .classes('btn-ghost w-10 h-10 rounded-full p-0').props('ripple=false flat aria-label="Cambiar Tema"').tooltip('Cambiar Tema')