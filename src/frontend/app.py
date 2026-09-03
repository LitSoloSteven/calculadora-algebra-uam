from nicegui import ui
from src.frontend.views.linear_systems.view_gauss import GaussUI
from src.frontend.views.linear_systems.view_gauss_jordan import GaussJordanUI

@ui.page('/')
def index():
    ui.navigate.to('/gauss')

@ui.page('/gauss')
def gauss_page():
    app_ui = GaussUI()
    app_ui.build()

@ui.page('/gauss-jordan')
def gauss_jordan_page():
    app_ui = GaussJordanUI()
    app_ui.build()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Calculadora Álgebra Lineal UAM")