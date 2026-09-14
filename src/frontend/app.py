from nicegui import ui
from src.frontend.views.linear_systems.view_linear_systems import LinearSystemsUI

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
                /* Paleta base compartida */
                --cream-50:  #FBF8EF;
                --cream-100: #F5F0DC;
                --cream-500: #D9CDA4;

                /* Variables Estructurales de Bordes */
                --radius-card: 20px;
                --radius-input: 12px;
                --radius-btn: 12px;
                --radius-badge: 8px;
                --radius-pill: 999px;
            }

            /* === TEMA CLARO (Default) === */
            body[data-theme="claro"], body {
                --bg-page: var(--cream-50);
                --bg-panel: var(--cream-100);
                --text-main: #262B42;
                --text-sec: #4A5578;
                --shadow-light: rgba(255, 255, 255, 0.5);
                --shadow-dark: rgba(0, 0, 0, 0.05);
                
                --btn-primary-bg: #256F69;
                --btn-primary-text: var(--cream-50);
                
                --bg-calc-btn: #FDFBEE;
                
                --input-bg: #EBE4C8;
                --input-text: #262B42;
                
                /* Badges de Estado */
                --badge-err-bg: #FADBD8;
                --badge-err-text: #C0392B;
                --badge-suc-bg: #D5F5E3;
                --badge-suc-text: #229954;
                --badge-warn-bg: #FDEBD0;
                --badge-warn-text: #B9770E;
            }

            /* === TEMA AQUA === */
            body[data-theme="aqua"] {
                --bg-page: #EAF6FF;
                --bg-panel: #D9EFFF;
                --text-main: #082338;
                --text-sec: #153C5C;
                --shadow-light: rgba(255, 255, 255, 0.6);
                --shadow-dark: rgba(8, 35, 56, 0.08);
                
                --btn-primary-bg: #082338;
                --btn-primary-text: #EAF6FF;
                
                --bg-calc-btn: #E4F3FF;
                
                --input-bg: #CBE4F9;
                --input-text: #082338;
                
                /* Badges de Estado */
                --badge-err-bg: #FADBD8;
                --badge-err-text: #C0392B;
                --badge-suc-bg: #D5F5E3;
                --badge-suc-text: #229954;
                --badge-warn-bg: #FDEBD0;
                --badge-warn-text: #B9770E;
            }

            /* === TEMA OSCURO === */
            body[data-theme="oscuro"] {
                --bg-page: #082338;
                --bg-panel: #0A2B45;
                --text-main: #EAF6FF;
                --text-sec: #B1D4F0;
                --shadow-light: rgba(255, 255, 255, 0.03);
                --shadow-dark: rgba(0, 0, 0, 0.25);
                
                --btn-primary-bg: #BFE6E1;
                --btn-primary-text: #082338;
                
                --bg-calc-btn: #0D3554;
                
                --input-bg: #061D2E;
                --input-text: #EAF6FF;
                
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
                transition: background-color 0.4s ease, color 0.4s ease;
            }

            .q-btn, .q-toolbar, .q-item, .q-tooltip { font-family: 'Space Grotesk', sans-serif !important; }

            /* === PANELES Y CONTENEDORES (Outset Neumorphism) === */
            .panel-card {
                background-color: var(--bg-panel) !important;
                border-radius: var(--radius-card) !important;
                box-shadow: 10px 10px 20px var(--shadow-dark), -10px -10px 20px var(--shadow-light) !important;
                transition: all 0.3s ease;
            }

            /* === INPUTS DE MATRIZ (Inset Neumorphism) === */
            .matrix-input .q-field__control {
                background: var(--input-bg) !important;
                border: none !important;
                border-radius: var(--radius-input) !important;
                box-shadow: inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light) !important;
                transition: all 0.3s ease;
            }
            .matrix-input .q-field__control:before, 
            .matrix-input .q-field__control:after { display: none !important; }
            
            .matrix-input .q-field--focused .q-field__control {
                outline: 2px solid var(--btn-primary-bg) !important;
                outline-offset: 2px;
            }

            /* FIX AUTOFILL BACKGROUND */
            .matrix-input input:-webkit-autofill,
            .matrix-input input:-webkit-autofill:hover,
            .matrix-input input:-webkit-autofill:focus,
            .matrix-input input:-webkit-autofill:active {
                -webkit-text-fill-color: var(--input-text) !important;
                box-shadow: 0 0 0px 1000px var(--input-bg) inset !important;
                -webkit-box-shadow: 0 0 0px 1000px var(--input-bg) inset !important;
                transition: background-color 5000s ease-in-out 0s;
            }

            .matrix-input .q-field__native, .matrix-input .q-field__input {
                font-family: 'Cambria Math', 'Latin Modern Math', 'Computer Modern', serif !important;
                font-size: 1.15rem !important;
                color: var(--input-text) !important;
                -webkit-text-fill-color: var(--input-text) !important;
                text-align: center;
                transition: all 0.3s ease;
            }
            
            .matrix-input input::placeholder {
                color: var(--input-text) !important;
                -webkit-text-fill-color: var(--input-text) !important;
                opacity: 0.3 !important;
            }

            /* Etiquetas matemáticas */
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
                box-shadow: 6px 6px 12px var(--shadow-dark), -6px -6px 12px var(--shadow-light) !important;
                transition: all 0.2s ease;
            }
            .btn-primary:active {
                box-shadow: inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light) !important;
                transform: scale(0.97);
            }

            .btn-ghost {
                background: transparent !important;
                color: var(--text-main) !important;
                border: none !important;
                border-radius: var(--radius-btn) !important;
                font-weight: 600;
                box-shadow: 4px 4px 8px var(--shadow-dark), -4px -4px 8px var(--shadow-light) !important;
                transition: all 0.2s ease;
            }
            .btn-ghost:active {
                box-shadow: inset 3px 3px 6px var(--shadow-dark), inset -3px -3px 6px var(--shadow-light) !important;
                transform: scale(0.97);
            }
            
            /* === BADGES DE ESTADO (Embossed style) === */
            .badge-error, .badge-success, .badge-warning {
                border-radius: var(--radius-badge) !important;
                box-shadow: 4px 4px 8px var(--shadow-dark), -4px -4px 8px var(--shadow-light) !important;
                transition: all 0.3s ease;
            }
            .badge-error { background: var(--badge-err-bg) !important; color: var(--badge-err-text) !important; }
            .badge-error .q-icon { color: var(--badge-err-text) !important; }
            
            .badge-success { background: var(--badge-suc-bg) !important; color: var(--badge-suc-text) !important; }
            .badge-success .q-icon { color: var(--badge-suc-text) !important; }
            
            .badge-warning { background: var(--badge-warn-bg) !important; color: var(--badge-warn-text) !important; }
            .badge-warning .q-icon { color: var(--badge-warn-text) !important; }

            /* === TABS NEUMÓRFICOS === */
            .neo-tabs {
                background: var(--bg-panel) !important;
                border-radius: var(--radius-pill) !important;
                padding: 4px !important;
                box-shadow: inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light) !important;
            }
            .neo-tabs .q-tab {
                border-radius: var(--radius-pill) !important;
                min-height: 40px !important;
                padding: 0 24px !important;
                color: var(--text-sec) !important;
                font-weight: 600 !important;
                transition: color 0.3s ease !important;
                z-index: 1 !important;
            }
            .neo-tabs .q-tabs__content { width: 100% !important; }
            .neo-tabs .q-tab--active { color: var(--btn-primary-text) !important; }
            
            .neo-tabs .q-tab__indicator {
                height: 100% !important;
                top: 0 !important;
                background: var(--btn-primary-bg) !important;
                z-index: -1 !important;
                border-radius: var(--radius-pill) !important;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
                transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
            }
            .q-tab-panels { background: transparent !important; }

            /* === TABS NEUMÓRFICOS (CORTE RECTO AL CENTRO) - Sobreescritura === */
            .neo-tabs.method-tabs {
                padding: 0 !important;
                width: 320px !important;
                overflow: hidden !important;
            }
            .neo-tabs.method-tabs .q-tab {
                min-height: 44px !important;
                flex: 1 !important;
                padding: 0 !important;
                border-radius: 0 !important;
            }
            .neo-tabs.method-tabs .q-focus-helper { border-radius: 0 !important; }
            .neo-tabs.method-tabs .q-tab__indicator { border-radius: 0 !important; }

            /* === BOTONES NEUMÓRFICOS (ICONOS) === */
            .btn-neo-icon {
                background: var(--bg-panel) !important;
                color: var(--text-main) !important;
                border-radius: var(--radius-pill) !important;
                width: 44px !important;
                height: 44px !important;
                padding: 0 !important;
                box-shadow: 6px 6px 12px var(--shadow-dark), -6px -6px 12px var(--shadow-light) !important;
                transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
            }
            .btn-neo-icon:active {
                box-shadow: inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light) !important;
                transform: scale(0.95);
            }

            /* === BOTONES CALCULADORA === */
            .btn-neo-calc {
                background: var(--bg-calc-btn) !important;
                color: var(--text-main) !important;
                border-radius: var(--radius-btn) !important;
                padding: 0 !important;
                box-shadow: 6px 6px 12px var(--shadow-dark), -6px -6px 12px var(--shadow-light) !important;
                transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
            }
            .btn-neo-calc:active {
                box-shadow: inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light) !important;
                transform: scale(0.95);
            }

            /* === MENU DESPLEGABLE (Q-MENU) === */
            .q-menu {
                background: var(--bg-panel) !important;
                color: var(--text-main) !important;
                border-radius: var(--radius-input) !important;
                box-shadow: 6px 6px 12px var(--shadow-dark), -6px -6px 12px var(--shadow-light) !important;
            }

            /* === ANIMACIONES === */
            @keyframes slideUpFadeIn {
                0% { opacity: 0; transform: translateY(30px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            .animate-slide-up {
                animation: slideUpFadeIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards !important;
            }

            @keyframes slideBounceVertical {
                0% { opacity: 0; transform: translateY(-30px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            .animate-slide-bounce {
                animation: slideBounceVertical 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards !important;
            }

            /* === ANIMACIONES DE VIEW TRANSITIONS (TEMA) === */
            ::view-transition-old(root),
            ::view-transition-new(root) {
                animation: none;
                mix-blend-mode: normal;
            }
            ::view-transition-old(root) { z-index: 1; }
            ::view-transition-new(root) { z-index: 2; }

            /* === ANIMACION SQUASH BOUNCE (BOTON LIMPIAR) === */
            @keyframes squashBounce {
                0% { transform: scale(1); }
                30% { transform: scale(1.1, 0.9); }
                50% { transform: scale(0.9, 1.1); }
                70% { transform: scale(1.05, 0.95); }
                100% { transform: scale(1); }
            }
            .squash-bounce {
                animation: squashBounce 400ms cubic-bezier(0.34, 1.56, 0.64, 1) forwards !important;
            }
        </style>
        
        <script>
            // Rastreador del clic del mouse para animación de onda expansiva
            window.lastMouseClick = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
            document.addEventListener('click', e => {
                window.lastMouseClick = { x: e.clientX, y: e.clientY };
            }, { capture: true });
            
            document.addEventListener("DOMContentLoaded", () => {
                let savedTheme = localStorage.getItem('theme') || 'claro';
                document.body.setAttribute('data-theme', savedTheme);
            });
            
            function applyTheme(themeName) {
                document.body.setAttribute('data-theme', themeName);
                localStorage.setItem('theme', themeName);
            }

            function setTheme(themeName) {
                if (!document.startViewTransition) {
                    applyTheme(themeName);
                    return;
                }
                
                const x = window.lastMouseClick.x;
                const y = window.lastMouseClick.y;
                const endRadius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
                
                const transition = document.startViewTransition(() => {
                    applyTheme(themeName);
                });
                
                transition.ready.then(() => {
                    document.documentElement.animate(
                        [
                            { clipPath: `circle(0px at ${x}px ${y}px)` },
                            { clipPath: `circle(${endRadius}px at ${x}px ${y}px)` }
                        ],
                        {
                            duration: 500,
                            easing: 'ease-in-out',
                            pseudoElement: '::view-transition-new(root)',
                        }
                    );
                });
            }

            // === ANIMACIÓN DE RECOLECCIÓN DE BASURA ===
            function animateGarbageCollection() {
                const btn = document.getElementById('btn-limpiar-main');
                if (!btn) return;
                
                const iconElem = btn.querySelector('.q-icon');
                if (iconElem) {
                    iconElem.textContent = 'delete_sweep'; // Cambiar a ícono animado/abierto
                    iconElem.classList.add('text-negative'); // Darle un tinte si se desea
                }
                
                const btnRect = btn.getBoundingClientRect();
                const inputs = document.querySelectorAll('.matrix-input input');
                
                let delay = 0;
                let animatedCount = 0;
                
                inputs.forEach((input) => {
                    if (!input.value || input.value === '0' || input.value.trim() === '') return;
                    animatedCount++;
                    
                    const rect = input.getBoundingClientRect();
                    const clone = document.createElement('div');
                    
                    // Igualar estilos del input clonado
                    clone.textContent = input.value;
                    clone.style.position = 'fixed';
                    clone.style.left = rect.left + 'px';
                    clone.style.top = rect.top + 'px';
                    clone.style.width = rect.width + 'px';
                    clone.style.height = rect.height + 'px';
                    clone.style.margin = '0';
                    clone.style.zIndex = '9999';
                    clone.style.display = 'flex';
                    clone.style.alignItems = 'center';
                    clone.style.justifyContent = 'center';
                    
                    // Copiar diseño del contenedor padre (caja neumórfica)
                    const container = input.closest('.q-field__control');
                    if (container) {
                        const style = window.getComputedStyle(container);
                        clone.style.background = style.background;
                        clone.style.borderRadius = style.borderRadius;
                        clone.style.boxShadow = style.boxShadow;
                    }
                    
                    const inputStyle = window.getComputedStyle(input);
                    clone.style.fontFamily = inputStyle.fontFamily;
                    clone.style.fontSize = inputStyle.fontSize;
                    clone.style.color = inputStyle.color;
                    
                    clone.style.transition = 'all 600ms cubic-bezier(0.34, 1.56, 0.64, 1)';
                    clone.style.pointerEvents = 'none';
                    
                    // Ocultar texto original
                    input.style.color = 'transparent';
                    
                    document.body.appendChild(clone);
                    
                    setTimeout(() => {
                        input.value = ''; // Vaciar la celda visualmente
                        
                        const targetX = btnRect.left + btnRect.width / 2 - rect.width / 2;
                        const targetY = btnRect.top + btnRect.height / 2 - rect.height / 2;
                        clone.style.transform = `translate(${targetX - rect.left}px, ${targetY - rect.top}px) scale(0.1)`;
                        clone.style.opacity = '0';
                    }, delay);
                    
                    setTimeout(() => clone.remove(), delay + 600);
                    
                    delay += 30; // Stagger effect
                });
                
                // Efecto de Squash & Bounce al final
                if (animatedCount > 0) {
                    setTimeout(() => {
                        btn.classList.add('squash-bounce');
                        setTimeout(() => {
                            btn.classList.remove('squash-bounce');
                            if (iconElem) {
                                iconElem.textContent = 'delete';
                                iconElem.classList.remove('text-negative');
                            }
                            // Restaurar colores transparentes
                            inputs.forEach(i => i.style.color = '');
                        }, 400);
                    }, delay + 200); // Trigger cuando la última celda está casi llegando
                } else {
                    if (iconElem) {
                        iconElem.textContent = 'delete';
                        iconElem.classList.remove('text-negative');
                    }
                    inputs.forEach(i => i.style.color = '');
                }
            }
        </script>
    ''')

@ui.page('/')
def index():
    ui.navigate.to('/sistemas-lineales')

@ui.page('/gauss')
def redirect_gauss():
    ui.navigate.to('/sistemas-lineales?method=gauss')

@ui.page('/gauss-jordan')
def redirect_gauss_jordan():
    ui.navigate.to('/sistemas-lineales?method=gauss-jordan')

@ui.page('/sistemas-lineales')
def linear_systems_page(method: str = 'gauss'):
    setup_theme()
    app_ui = LinearSystemsUI(initial_method=method)
    app_ui.build()

@ui.page('/operaciones-matrices')
def matrix_ops_page():
    from src.frontend.views.matrix_ops.view_matrix_ops import MatrixOpsUI
    setup_theme()
    app_ui = MatrixOpsUI()
    app_ui.build()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Calculadora Álgebra Lineal UAM")