from nicegui import ui

def create_navbar():

    with ui.header().classes('bg-primary text-white items-center px-6 py-4 flex justify-between'):
        

        with ui.row().classes('items-center'):

            with ui.button('Matriz', icon='grid_on', color='transparent').props('flat').classes('font-bold text-white'):
                with ui.menu():
                    ui.menu_item('Eliminación de Gauss', on_click=lambda: ui.navigate.to('/gauss'))
                    ui.menu_item('Gauss-Jordan', on_click=lambda: ui.navigate.to('/gauss-jordan'))
        
        ui.label('Calculadora de matrices').classes('text-xl font-bold tracking-wide')