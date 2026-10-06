"""Componente de seleccion de tema reutilizable para Scalaris."""
from nicegui import ui
from src.frontend.components.icons import icon_svg


def render_theme_button():
    """Renderiza el boton de tema con su menu desplegable accesible."""
    theme_btn = ui.button(color=None).classes('btn-neo-icon p-0 text-main').props(
        'flat ripple=false aria-label="Seleccionar Tema" aria-haspopup="menu" aria-expanded="false"'
    ).tooltip('Seleccionar Tema')

    with theme_btn:
        ui.html(icon_svg('temas'))
        theme_menu = ui.menu().classes('p-2 min-w-[150px]')
        theme_menu.on('show', lambda _, b=theme_btn: b.props('aria-expanded="true"'))
        theme_menu.on('hide', lambda _, b=theme_btn: b.props('aria-expanded="false"'))

        with theme_menu:
            def menu_item(label: str, theme_id: str, swatch_token: str):
                with ui.menu_item(
                    on_click=lambda t=theme_id: ui.run_javascript(f"setTheme('{t}')")
                ).classes('rounded-lg mb-1 flex items-center gap-3 w-full'):
                    ui.html(
                        f'<div style="width: 14px; height: 14px; border-radius: 50%; '
                        f'background-color: var({swatch_token}); border: 1px solid var(--border-input);"></div>'
                    )
                    ui.label(label).classes('flex-1')
                    ui.html(
                        f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '''
                        f'''stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '''
                        f'''style="width: 14px; height: 14px; display: var(--show-{theme_id}, none); color: var(--accent);"><polyline points="20 6 9 17 4 12"></polyline></svg>'''
                    )

            menu_item('Papel', 'papel', '--swatch-papel')
            menu_item('Marea', 'marea', '--swatch-marea')
            menu_item('Medianoche', 'medianoche', '--swatch-medianoche')

    return theme_btn
