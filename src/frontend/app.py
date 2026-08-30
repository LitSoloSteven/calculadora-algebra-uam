from nicegui import ui
from src.frontend.views.calculator_view import CalculatorUI

@ui.page('/')
def index():
    # Instanciamos el objeto de la interfaz
    app_ui = CalculatorUI()
    # Construimos la vista
    app_ui.build()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Calculadora Álgebra Lineal UAM")