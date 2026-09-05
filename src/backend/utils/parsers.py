from nicegui import ui
from src.frontend.views.linear_systems.view_gauss import GaussUI
from src.frontend.views.linear_systems.view_gauss_jordan import GaussJordanUI

def setup_theme():
    ui.add_head_html('''
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
        
        <style>
            :root {
                --bg-color: #F1E9D2;
                --text-color: #4C516D;
                --shadow-light: #ffffff;
                --shadow-dark: #d2cbb7;
                
                --btn-bg: #4C516D;
                --btn-text: #F1E9D2;
                --btn-inset-dark: #3d4157;
                --btn-inset-light: #5b6183;

                --text-engrave: -1px -1px 1px rgba(0, 0, 0, 0.15), 1px 1px 1px rgba(255, 255, 255, 0.7);
                --btn-text-engrave: -1px -1px 1px rgba(0, 0, 0, 0.5), 1px 1px 1px rgba(255, 255, 255, 0.15);
            }
            body.dark-theme {
                --bg-color: #4C516D;
                --text-color: #F1E9D2;
                --shadow-light: #5b6183; 
                --shadow-dark: #3d4157;
                
                --btn-bg: #F1E9D2;
                --btn-text: #4C516D;
                --btn-inset-dark: #d2cbb7;
                --btn-inset-light: #ffffff;

                --text-engrave: -1px -1px 1px rgba(0, 0, 0, 0.5), 1px 1px 1px rgba(255, 255, 255, 0.1);
                --btn-text-engrave: -1px -1px 1px rgba(0, 0, 0, 0.15), 1px 1px 1px rgba(255, 255, 255, 0.8);
            }
            
            body {
                background-color: var(--bg-color);
                color: var(--text-color);
                font-family: 'Space Grotesk', sans-serif;
                transition: background-color 0.5s ease, color 0.5s ease;
            }

            .q-btn, .q-toolbar, .q-item, .q-tooltip {
                font-family: 'Space Grotesk', sans-serif !important;
            }

            .neu-flat {
                background: var(--bg-color) !important;
                box-shadow: 8px 8px 16px var(--shadow-dark), -8px -8px 16px var(--shadow-light);
                border-radius: 20px;
                border: none !important;
                color: var(--text-color) !important;
                transition: all 0.5s ease;
            }
            
            /* === BOTONES === */
            .neu-btn {
                background: var(--btn-bg) !important;
                color: var(--btn-text) !important;
                box-shadow: 6px 6px 12px var(--shadow-dark), -6px -6px 12px var(--shadow-light);
                border-radius: 15px;
                font-weight: 700;
                transition: all 0.5s ease;
                cursor: pointer;
                border: none;
            }
            .neu-btn:active {
                box-shadow: inset 4px 4px 8px var(--btn-inset-dark), inset -4px -4px 8px var(--btn-inset-light);
                transform: scale(0.96);
            }
            .neu-btn .q-icon, .neu-btn .q-btn__content, .neu-btn span {
                color: var(--btn-text) !important;
                text-shadow: var(--btn-text-engrave);
                transition: color 0.5s ease;
            }

            /* === INPUTS Y TEXT FIELDS (INVERTIDOS) === */
            .neu-pressed {
                /* Fuerza el fondo de contraste */
                background-color: var(--btn-bg) !important;
                box-shadow: inset 4px 4px 8px var(--btn-inset-dark), inset -4px -4px 8px var(--btn-inset-light) !important;
                border-radius: 12px !important;
                border: none !important;
                transition: all 0.5s ease;
            }
            
            /* Destruye cualquier fondo nativo de las sub-capas de Quasar */
            .neu-pressed .q-field__control,
            .neu-pressed .q-field__control-container,
            .neu-pressed .q-field__append,
            .neu-pressed .q-field__prepend {
                background: transparent !important;
            }
            
            /* Elimina la linea gris inferior por defecto */
            .neu-pressed .q-field__control:before, 
            .neu-pressed .q-field__control:after {
                display: none !important;
            }

            /* Números ingresados por el usuario */
            .neu-pressed .q-field__native, 
            .neu-pressed .q-field__input {
                font-family: 'Cambria Math', 'Latin Modern Math', 'Computer Modern', serif !important;
                font-size: 1.15rem !important;
                color: var(--btn-text) !important;
                -webkit-text-fill-color: var(--btn-text) !important;
                text-shadow: var(--btn-text-engrave) !important;
                transition: color 0.5s ease;
            }
            
            /* Etiquetas dentro del input (ej: "Ecuaciones") */
            .neu-pressed .q-field__label {
                font-family: 'Space Grotesk', sans-serif !important;
                color: var(--btn-text) !important;
                text-shadow: var(--btn-text-engrave) !important;
                transition: color 0.5s ease;
            }
            
            /* Íconos (como flechas de aumento/disminución) */
            .neu-pressed .q-icon {
                color: var(--btn-text) !important;
                transition: color 0.5s ease;
            }
            
            /* Signos matemáticos externos ($x_1$, +, =) */
            .text-lg, .text-2xl {
                text-shadow: var(--text-engrave);
                transition: color 0.5s ease;
            }
        </style>
        
        <script>
            document.addEventListener("DOMContentLoaded", () => {
                if (localStorage.getItem('theme') === 'dark') {
                    document.body.classList.add('dark-theme');
                }
            });
            function toggleTheme() {
                document.body.classList.toggle('dark-theme');
                const isDark = document.body.classList.contains('dark-theme');
                localStorage.setItem('theme', isDark ? 'dark' : 'light');
            }
        </script>
    ''')

@ui.page('/')
def index():
    ui.navigate.to('/gauss')

@ui.page('/gauss')
def gauss_page():
    setup_theme()
    app_ui = GaussUI()
    app_ui.build()

@ui.page('/gauss-jordan')
def gauss_jordan_page():
    setup_theme()
    app_ui = GaussJordanUI()
    app_ui.build()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Calculadora Álgebra Lineal UAM")