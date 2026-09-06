from nicegui import ui
from src.frontend.views.linear_systems.view_gauss import GaussUI
from src.frontend.views.linear_systems.view_gauss_jordan import GaussJordanUI

def setup_theme():
    ui.add_head_html('''
        <!-- Configuración e importación de MathJax -->
        <script>
            window.MathJax = {
                tex: {
                    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
                },
                svg: {
                    fontCache: 'global'
                }
            };
        </script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
        
        <style>
            :root {
                /* Paleta base */
                --navy-900:  #262B42;
                --navy-700:  #4A5578;
                --navy-300:  #9AA3C2;
                --cream-50:  #FBF8EF;
                --cream-100: #F5F0DC;
                --cream-500: #D9CDA4;
                --accent-700: #256F69;
                --accent-200: #BFE6E1;

                /* Variables Estructurales */
                --radius-card: 16px;
                --radius-input: 12px;
                --radius-btn: 12px;

                /* === TEMA CLARO === */
                --bg-page: var(--cream-50);
                --bg-panel: var(--cream-100);
                --text-main: var(--navy-900);
                --text-sec: var(--navy-700);
                --shadow-panel: 0 4px 20px rgba(38, 43, 66, 0.08);
                
                /* Botones */
                --btn-primary-bg: var(--accent-700);
                --btn-primary-text: var(--cream-50);
                
                /* Celdas de Matriz Invertidas */
                --input-bg: var(--navy-700);
                --input-text: var(--cream-50);
                
                /* Badges de Estado */
                --badge-err-bg: #FADBD8;
                --badge-err-text: #C0392B;
                --badge-suc-bg: #D5F5E3;
                --badge-suc-text: #229954;
                --badge-warn-bg: #FDEBD0;
                --badge-warn-text: #B9770E;
            }
            body.dark-theme {
                /* === TEMA OSCURO === */
                --bg-page: var(--navy-900);
                --bg-panel: var(--navy-700);
                --text-main: var(--cream-50);
                --text-sec: var(--cream-100);
                --shadow-panel: 0 4px 20px rgba(0, 0, 0, 0.3);
                
                /* Botones */
                --btn-primary-bg: var(--accent-200);
                --btn-primary-text: var(--navy-900);
                
                /* Celdas de Matriz Invertidas */
                --input-bg: var(--cream-50);
                --input-text: var(--navy-900);
                
                /* Badges de Estado */
                --badge-err-bg: #5B2C2C;
                --badge-err-text: #E8897D;
                --badge-suc-bg: #274D36;
                --badge-suc-text: #8FCBA6;
                --badge-warn-bg: #5C4325;
                --badge-warn-text: #E3B27E;
            }
            
            body {
                background-color: var(--bg-page);
                color: var(--text-main);
                font-family: 'Space Grotesk', sans-serif;
                transition: background-color 0.3s ease, color 0.3s ease;
            }

            .q-btn, .q-toolbar, .q-item, .q-tooltip { font-family: 'Space Grotesk', sans-serif !important; }

            /* Contenedores Panel */
            .panel-card {
                background-color: var(--bg-panel) !important;
                border-radius: var(--radius-card);
                box-shadow: var(--shadow-panel) !important;
                transition: all 0.3s ease;
            }

            /* === INPUTS DE MATRIZ INVERTIDOS === */
            .matrix-input .q-field__control {
                background: var(--input-bg) !important;
                border: none !important;
                border-radius: var(--radius-input);
                transition: all 0.3s ease;
            }
            .matrix-input .q-field__control:before, 
            .matrix-input .q-field__control:after { display: none !important; }
            
            /* Foco explícito */
            .matrix-input .q-field--focused .q-field__control {
                outline: 2px solid var(--btn-primary-bg) !important;
                outline-offset: 2px;
            }

            /* Valores tecleados (Color invertido) */
            .matrix-input .q-field__native, .matrix-input .q-field__input {
                font-family: 'Cambria Math', 'Latin Modern Math', 'Computer Modern', serif !important;
                font-size: 1.15rem !important;
                color: var(--input-text) !important;
                -webkit-text-fill-color: var(--input-text) !important;
                text-align: center;
                transition: all 0.3s ease;
            }
            
            /* Placeholder ("0") opacidad atenuada */
            .matrix-input input::placeholder {
                color: var(--input-text) !important;
                -webkit-text-fill-color: var(--input-text) !important;
                opacity: 0.3 !important;
            }

            /* Signos y subíndices (x1 + x2 =) */
            .math-label {
                font-family: 'Space Grotesk', sans-serif !important;
                color: var(--text-main) !important;
                font-weight: 500;
            }
            .math-label i { font-style: italic; font-family: 'Cambria Math', serif; }
            .math-label sub {
                vertical-align: baseline;
                position: relative;
                top: 0.2em;
                font-size: 0.8em;
                font-weight: 700;
            }

            /* === BOTONES PRIMARIOS Y SECUNDARIOS === */
            .btn-primary {
                background: var(--btn-primary-bg) !important;
                color: var(--btn-primary-text) !important;
                border-radius: var(--radius-btn) !important;
                font-weight: 700;
                transition: all 0.2s ease;
            }
            .btn-primary:active { transform: scale(0.97); }

            .btn-ghost {
                background: transparent !important;
                color: var(--text-main) !important;
                border: 1px solid var(--text-main) !important;
                border-radius: var(--radius-btn) !important;
                font-weight: 600;
                transition: all 0.2s ease;
            }
            .btn-ghost:active { transform: scale(0.97); }
            
            /* === BADGES DE ESTADO === */
            .badge-error { background: var(--badge-err-bg) !important; color: var(--badge-err-text) !important; transition: all 0.3s ease; }
            .badge-error .q-icon { color: var(--badge-err-text) !important; }
            
            .badge-success { background: var(--badge-suc-bg) !important; color: var(--badge-suc-text) !important; transition: all 0.3s ease; }
            .badge-success .q-icon { color: var(--badge-suc-text) !important; }
            
            .badge-warning { background: var(--badge-warn-bg) !important; color: var(--badge-warn-text) !important; transition: all 0.3s ease; }
            .badge-warning .q-icon { color: var(--badge-warn-text) !important; }
            /* === TOGGLE NEUMÓRFICO === */
            .neo-toggle {
                background: var(--bg-panel) !important;
                border-radius: var(--radius-btn) !important;
                padding: 4px !important;
                /* Sombra interna para crear la profundidad del carril */
                box-shadow: inset 4px 4px 8px rgba(0,0,0,0.1), inset -4px -4px 8px rgba(255,255,255,0.05) !important;
                border: none !important;
            }
            body.dark-theme .neo-toggle {
                box-shadow: inset 4px 4px 8px rgba(0,0,0,0.3), inset -4px -4px 8px rgba(255,255,255,0.02) !important;
            }
           /* === TABS NEUMÓRFICOS (PÍLDORA DESLIZANTE) === */
            .neo-tabs {
                background: var(--bg-panel) !important;
                border-radius: 999px !important;
                padding: 4px !important;
                box-shadow: inset 4px 4px 8px rgba(0,0,0,0.1), inset -4px -4px 8px rgba(255,255,255,0.05) !important;
            }
            body.dark-theme .neo-tabs {
                box-shadow: inset 4px 4px 8px rgba(0,0,0,0.3), inset -4px -4px 8px rgba(255,255,255,0.02) !important;
            }
            .neo-tabs .q-tab {
                border-radius: 999px !important;
                min-height: 40px !important;
                padding: 0 24px !important;
                color: var(--text-sec) !important;
                font-weight: 600 !important;
                transition: color 0.3s ease !important;
                z-index: 1 !important;
            }
            /* === TABS NEUMÓRFICOS (PÍLDORA DESLIZANTE CON REBOTE) === */
            .neo-tabs {
                background: var(--bg-panel) !important;
                border-radius: 999px !important;
                padding: 4px !important;
                box-shadow: inset 4px 4px 8px rgba(0,0,0,0.1), inset -4px -4px 8px rgba(255,255,255,0.05) !important;
                width: 320px !important; /* Fuerza a que sea un interruptor de tamaño fijo */
            }
            body.dark-theme .neo-tabs {
                box-shadow: inset 4px 4px 8px rgba(0,0,0,0.3), inset -4px -4px 8px rgba(255,255,255,0.02) !important;
            }
            .neo-tabs .q-tabs__content {
                width: 100% !important; /* Expande el contenido al borde del interruptor */
            }
      /* === TABS NEUMÓRFICOS (PÍLDORA CON CORTE RECTO AL CENTRO) === */
            .neo-tabs {
                background: var(--bg-panel) !important;
                border-radius: 999px !important; /* Vuelve a ser una píldora (ovalado) */
                padding: 0 !important;
                box-shadow: inset 4px 4px 8px rgba(0,0,0,0.1), inset -4px -4px 8px rgba(255,255,255,0.05) !important;
                width: 320px !important;
                overflow: hidden !important; /* El secreto: el contenedor ovalado recorta todo lo que sobresalga */
            }
            body.dark-theme .neo-tabs {
                box-shadow: inset 4px 4px 8px rgba(0,0,0,0.3), inset -4px -4px 8px rgba(255,255,255,0.02) !important;
            }
            .neo-tabs .q-tabs__content { width: 100% !important; }
            
            /* Las pestañas individuales */
            .neo-tabs .q-tab {
                min-height: 44px !important;
                flex: 1 !important;
                padding: 0 !important;
                color: var(--text-sec) !important;
                font-weight: 600 !important;
                transition: color 0.3s ease !important;
                z-index: 1 !important;
                border-radius: 0 !important; /* Recto al centro. El contenedor lo redondeará por fuera */
            }
            .neo-tabs .q-tab--active { color: var(--btn-primary-text) !important; }
            
            /* Sombra al pasar el ratón (Hover) y efecto onda */
            .neo-tabs .q-focus-helper {
                border-radius: 0 !important; /* La sombra ahora es recta al centro y ovalada por fuera */
            }
            
            /* El indicador (fondo animado) */
            .neo-tabs .q-tab__indicator {
                height: 100% !important;
                top: 0 !important;
                background: var(--btn-primary-bg) !important;
                z-index: -1 !important;
                border-radius: 0 !important; /* Plano al centro, recortado ovalado por el contenedor */
                box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
                transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) !important; /* Efecto Spring Bounce */
            }
            .q-tab-panels { background: transparent !important; }

            /* === ANIMACIÓN DE REBOTE PARA LOS PANELES DE ABAJO === */
            .q-transition--slide-left-enter-active,
            .q-transition--slide-left-leave-active,
            .q-transition--slide-right-enter-active,
            .q-transition--slide-right-leave-active {
                transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
            }
        </style>
        </style>
        
        <script>
            document.addEventListener("DOMContentLoaded", () => {
                if (localStorage.getItem('theme') === 'dark') document.body.classList.add('dark-theme');
            });
            function toggleTheme() {
                document.body.classList.toggle('dark-theme');
                localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
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