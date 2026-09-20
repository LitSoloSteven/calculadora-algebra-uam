from nicegui import ui, app
from fastapi.responses import RedirectResponse
# Servir assets para el splash screen
app.add_static_files('/assets', 'src/frontend/assets')

def setup_theme():
    ui.add_head_html('''
        <!-- Prevenir FOUC (Flash of Unstyled Content) de tema claro -->
        <script>
        (function () {
          var mapa = {claro: 'papel', aqua: 'marea', oscuro: 'medianoche'};
          var t = localStorage.getItem('theme') || 'papel';
          if (mapa[t]) { t = mapa[t]; localStorage.setItem('theme', t); }
          var r = document.documentElement;
          r.setAttribute('data-theme', t);
          r.style.colorScheme = (t === 'medianoche') ? 'dark' : 'light';
        })();
        </script>

        <!-- Overlay Animación de Inicio -->
        <script>
        (function () {
          if (sessionStorage.getItem('splash-shown')) return;
          sessionStorage.setItem('splash-shown', '1');
          var reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
          var dur = reduced ? 400 : 3000;
          var tema = document.documentElement.getAttribute('data-theme');
          var logo = (tema === 'medianoche') ? '/assets/LogoClaro.png' : '/assets/LogoOscuro.png';
          
          var overlay = document.createElement('div');
          overlay.id = 'agy-splash-overlay';
          overlay.style.cssText = 'position: fixed; inset: 0; z-index: 99999; background: var(--bg-page); display: flex; flex-direction: column; align-items: center; justify-content: center; view-transition-name: none; transform-origin: center;';
          
          overlay.innerHTML = `
            <div style="position: relative; display: flex; align-items: center; justify-content: center; width: 120px; height: 120px;">
              <img id="splash-logo" src="${logo}" style="width: 80px; height: 80px; object-fit: contain; opacity: 0; transform: scale(0.88);" alt="Logo">
              <svg id="splash-ring" style="position: absolute; inset: 0; width: 100%; height: 100%; transform: rotate(-90deg);" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="58" fill="none" stroke="var(--accent)" stroke-width="2" stroke-dasharray="365" stroke-dashoffset="365"></circle>
              </svg>
            </div>
            <div style="margin-top: 24px; font-family: 'Space Grotesk', sans-serif; font-size: 24px; font-weight: 700; color: var(--text-main); display: flex; align-items: center; gap: 8px;">
              <div style="display: flex; gap: 6px;">
                <span id="splash-t1" style="clip-path: inset(0 100% 0 0);">Álgebra</span>
                <span id="splash-t2" style="clip-path: inset(0 100% 0 0);">Lineal</span>
              </div>
              <span id="splash-t3" style="opacity: 0; color: var(--accent);">UAM</span>
            </div>
          `;
          document.documentElement.appendChild(overlay);

          if (reduced) {
              overlay.animate([ { opacity: 1 }, { opacity: 0 } ], { duration: dur, fill: 'forwards' });
              setTimeout(() => overlay.remove(), dur);
              return;
          }

          var logoEl = overlay.querySelector('#splash-logo');
          var ringCircle = overlay.querySelector('#splash-ring circle');
          var ringEl = overlay.querySelector('#splash-ring');
          var t1 = overlay.querySelector('#splash-t1');
          var t2 = overlay.querySelector('#splash-t2');
          var t3 = overlay.querySelector('#splash-t3');

          // 0-600: Logo entra
          logoEl.animate(
              [ { transform: 'scale(0.88)', opacity: 0 }, { transform: 'scale(1)', opacity: 1 } ],
              { duration: 600, easing: 'cubic-bezier(0.32, 0.72, 0, 1)', fill: 'forwards' }
          );

          // 600-1800: Anillo traza y textos
          ringCircle.animate(
              [ { strokeDashoffset: 365 }, { strokeDashoffset: 0 } ],
              { duration: 1200, delay: 600, easing: 'ease-in-out', fill: 'forwards' }
          );
          t1.animate(
              [ { clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)' } ],
              { duration: 400, delay: 800, easing: 'ease-out', fill: 'forwards' }
          );
          t2.animate(
              [ { clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)' } ],
              { duration: 400, delay: 920, easing: 'ease-out', fill: 'forwards' }
          );
          t3.animate(
              [ { opacity: 0 }, { opacity: 1 } ],
              { duration: 400, delay: 1200, easing: 'ease-out', fill: 'forwards' }
          );

          // 1800-2600: Pulso del anillo y barra
          ringEl.animate(
              [ { transform: 'rotate(-90deg) scale(1)' }, { transform: 'rotate(-90deg) scale(1.03)', offset: 0.5 }, { transform: 'rotate(-90deg) scale(1)' } ],
              { duration: 800, delay: 1800, easing: 'ease-in-out' }
          );

          var bar = document.createElement('div');
          bar.style.cssText = 'height: 2px; background: var(--accent); width: 0; margin-top: 12px; border-radius: 2px;';
          overlay.appendChild(bar);
          bar.animate(
              [ { width: '0' }, { width: '120px' } ],
              { duration: 600, delay: 1800, easing: 'ease-out', fill: 'forwards' }
          );

          // 2600-3000: Overlay se desvanece y body entra
          setTimeout(() => overlay.style.pointerEvents = 'none', 2600);
          overlay.animate(
              [ { opacity: 1, transform: 'scale(1)', filter: 'blur(0)' }, { opacity: 0, transform: 'scale(1.04)', filter: 'blur(4px)' } ],
              { duration: 400, delay: 2600, easing: 'ease-in-out', fill: 'forwards' }
          );

          setTimeout(() => {
              if(document.body) {
                  document.body.animate(
                      [ { transform: 'translateY(16px)' }, { transform: 'translateY(0)' } ],
                      { duration: 400, easing: 'ease-out', fill: 'forwards' }
                  );
              }
          }, 2600);

          setTimeout(() => overlay.remove(), 3100);
        })();
        </script>

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
            /* ======================================================================
               SISTEMA DE TOKENS — Calculadora Álgebra Lineal UAM
               Concepto: "Neumorfismo editorial de precisión"
               ====================================================================== */

            /* === TOKENS ESTRUCTURALES (compartidos por todos los temas) === */
            :root {
                /* Espaciado (base 4 px) */
                --space-1: 4px;   --space-2: 8px;   --space-3: 12px;
                --space-4: 16px;  --space-5: 20px;  --space-6: 24px;
                --space-8: 32px;  --space-10: 40px; --space-12: 48px;

                /* Bordes */
                --radius-card: 20px;
                --radius-input: 12px;
                --radius-btn: 12px;
                --radius-badge: 8px;
                --radius-pill: 999px;

                /* Tipografía — Escala */
                --fs-display: 2rem;
                --fw-display: 700;
                --ls-display: -0.02em;
                --fs-h1: 1.5rem;
                --fw-h1: 700;
                --ls-h1: -0.015em;
                --fs-h2: 1.125rem;
                --fw-h2: 600;
                --fs-body: 0.9375rem;
                --fw-body: 400;
                --fs-small: 0.8125rem;
                --fw-small: 500;
                --fs-mono-math: 1.0625rem;

                /* Movimiento */
                --dur-fast: 120ms;
                --dur-med: 240ms;
                --dur-slow: 500ms;
                --ease-std: cubic-bezier(0.32, 0.72, 0, 1);
                --ease-elastic: cubic-bezier(0.34, 1.56, 0.64, 1);
            }

            /* === SCROLLBARS GLOBALES === */
            ::-webkit-scrollbar { width: 8px; height: 8px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: color-mix(in srgb, var(--text-sec) 25%, transparent); border-radius: 9999px; }
            * { scrollbar-color: color-mix(in srgb, var(--text-sec) 25%, transparent) transparent; }

            /* === TEMA PAPEL (Default · #F2F0EB) === */
            :root, :root[data-theme="papel"] {
                color-scheme: light;

                --bg-page      : #F2F0EB;
                --bg-panel     : #EDEAE3;
                --bg-elevated  : #F7F5F1;
                --bg-calc-btn  : #F6F4EF;
                --input-bg     : #E5E1D8;

                --text-main       : #23262E;
                --text-sec        : #5A6070;
                --text-placeholder: #9AA0AE;
                --input-text      : #23262E;

                --border-input : rgba(35, 38, 46, 0.08);
                --shadow-dark  : rgba(58, 52, 40, 0.11);
                --shadow-light : rgba(255, 255, 255, 0.90);

                --accent       : #1F6B64;
                --accent-soft  : #D8E8E5;
                --btn-primary-bg  : var(--accent);
                --btn-primary-text: #F7F5F1;
                --focus-ring   : #1F6B64;

                --error   : #B23A31;
                --badge-err-bg  : #F6DED9;
                --badge-err-text: #8E2A22;
                --success : #1F7A4D;
                --badge-suc-bg  : #DCEEE2;
                --badge-suc-text: #14603A;
                --warning : #A6710B;
                --badge-warn-bg : #F7E7CB;
                --badge-warn-text: #7A5208;

                /* Elevación neumórfica claro */
                --elev-0: none;
                --elev-1: 4px 4px 8px var(--shadow-dark), -4px -4px 8px var(--shadow-light);
                --elev-2: 6px 6px 12px var(--shadow-dark), -6px -6px 12px var(--shadow-light);
                --elev-3: 10px 10px 20px var(--shadow-dark), -10px -10px 20px var(--shadow-light);
                --elev-inset: inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light);
            }

            /* === TEMA MAREA (saturación panel −8 %) === */
            :root[data-theme="marea"] {
                color-scheme: light;

                --bg-page      : #EDF2F8;
                --bg-panel     : #E1E9F1;
                --bg-elevated  : #F2F5FA;
                --bg-calc-btn  : #EAF0F7;
                --input-bg     : #D4DCE8;

                --text-main       : #0B1F33;
                --text-sec        : #3A5068;
                --text-placeholder: #8494A7;
                --input-text      : #0B1F33;

                --border-input : rgba(11, 31, 51, 0.08);
                --shadow-dark  : rgba(11, 31, 51, 0.10);
                --shadow-light : rgba(255, 255, 255, 0.75);

                --accent       : #14605A;
                --accent-soft  : #D0E4E1;
                --btn-primary-bg  : var(--accent);
                --btn-primary-text: #F2F5FA;
                --focus-ring   : #14605A;

                --error   : #B23A31;
                --badge-err-bg  : #F6DED9;
                --badge-err-text: #8E2A22;
                --success : #1F7A4D;
                --badge-suc-bg  : #DCEEE2;
                --badge-suc-text: #14603A;
                --warning : #A6710B;
                --badge-warn-bg : #F7E7CB;
                --badge-warn-text: #7A5208;

                /* Elevación neumórfica aqua */
                --elev-0: none;
                --elev-1: 4px 4px 8px var(--shadow-dark), -4px -4px 8px var(--shadow-light);
                --elev-2: 6px 6px 12px var(--shadow-dark), -6px -6px 12px var(--shadow-light);
                --elev-3: 10px 10px 20px var(--shadow-dark), -10px -10px 20px var(--shadow-light);
                --elev-inset: inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light);
            }

            /* === TEMA MEDIANOCHE (elevación por borde + sombra difusa) === */
            :root[data-theme="medianoche"] {
                color-scheme: dark;

                --bg-page      : #082338;
                --bg-panel     : #0A2B45;
                --bg-elevated  : #0D3554;
                --bg-calc-btn  : #0D3554;
                --input-bg     : #061D2E;

                --text-main       : #EAF6FF;
                --text-sec        : #B1D4F0;
                --text-placeholder: #5F87A6;
                --input-text      : #EAF6FF;

                --border-input : rgba(234, 246, 255, 0.08);
                --shadow-dark  : rgba(0, 0, 0, 0.35);
                --shadow-light : rgba(255, 255, 255, 0.03);

                --accent       : #BFE6E1;
                --accent-soft  : #14403C;
                --btn-primary-bg  : var(--accent);
                --btn-primary-text: #082338;
                --focus-ring   : #BFE6E1;

                --error   : #E8897D;
                --badge-err-bg  : #4A2523;
                --badge-err-text: #F0A79D;
                --success : #8FCBA6;
                --badge-suc-bg  : #1D4331;
                --badge-suc-text: #A8DBBC;
                --warning : #E3B27E;
                --badge-warn-bg : #4A3820;
                --badge-warn-text: #EDC99A;

                /* Elevación oscura: borde superior sutil + sombra difusa */
                --elev-0: none;
                --elev-1: inset 0 1px 0 rgba(255,255,255,0.06), 0 2px 8px var(--shadow-dark);
                --elev-2: inset 0 1px 0 rgba(255,255,255,0.06), 0 4px 16px var(--shadow-dark);
                --elev-3: inset 0 1px 0 rgba(255,255,255,0.06), 0 8px 24px var(--shadow-dark);
                --elev-inset: inset 2px 2px 6px rgba(0,0,0,0.45), inset -1px -1px 3px rgba(255,255,255,0.04);
            }

            /* === BASE === */
            html {
                background-color: var(--bg-page);
            }
            body {
                background-color: var(--bg-page);
                color: var(--text-main);
                font-family: 'Space Grotesk', sans-serif;
                font-size: var(--fs-body);
                font-weight: var(--fw-body);
                transition: background-color var(--dur-slow) var(--ease-std),
                            color var(--dur-slow) var(--ease-std);
            }

            .q-btn, .q-toolbar, .q-item, .q-tooltip {
                font-family: 'Space Grotesk', sans-serif !important;
            }

            /* === UTILIDADES DE COLOR === */
            .text-main        { color: var(--text-main) !important; }
            .text-sec         { color: var(--text-sec)  !important; }
            .text-accent      { color: var(--accent)    !important; }
            .text-placeholder { color: var(--text-placeholder) !important; }
            .bg-elevated      { background-color: var(--bg-elevated) !important; }
            
            /* === MATH SCROLL CONTAINER === */
            .math-scroll-container {
                overflow-x: auto;
                width: 100%;
                padding-bottom: 8px;
            }
            
            /* Font scale para math label en móviles */
            @media (max-width: 600px) {
                .math-label { font-size: clamp(0.75rem, 3vw, 1.25rem) !important; }
            }

            /* === ESCALA TIPOGRÁFICA === */
            .fs-display {
                font-size: var(--fs-display);
                font-weight: var(--fw-display);
                letter-spacing: var(--ls-display);
            }
            .fs-h1 {
                font-size: var(--fs-h1);
                font-weight: var(--fw-h1);
                letter-spacing: var(--ls-h1);
            }
            .fs-h2 {
                font-size: var(--fs-h2);
                font-weight: var(--fw-h2);
            }
            .fs-body {
                font-size: var(--fs-body);
                font-weight: var(--fw-body);
            }
            .fs-small {
                font-size: var(--fs-small);
                font-weight: var(--fw-small);
            }

            /* === PANELES Y CONTENEDORES (Outset Neumorphism) === */
            .panel-card {
                background-color: var(--bg-panel) !important;
                border-radius: var(--radius-card) !important;
                box-shadow: var(--elev-3) !important;
                transition: box-shadow var(--dur-med) var(--ease-std),
                            background-color var(--dur-med) var(--ease-std);
            }

            /* === INPUTS DE MATRIZ (Inset Neumorphism) === */
            .matrix-input .q-field__control {
                background: var(--input-bg);
                border: none !important;
                border-radius: var(--radius-input) !important;
                box-shadow: var(--elev-inset) !important;
                transition: box-shadow var(--dur-fast) var(--ease-std),
                            background var(--dur-fast) var(--ease-std);
            }
            .matrix-input .q-field__control:before,
            .matrix-input .q-field__control:after { display: none !important; }

            .matrix-input .q-field--focused .q-field__control {
                outline: 2px solid var(--focus-ring) !important;
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
                font-family: 'Space Grotesk', 'Cambria Math', serif !important;
                font-size: var(--fs-mono-math) !important;
                font-variant-numeric: tabular-nums;
                color: var(--input-text) !important;
                -webkit-text-fill-color: var(--input-text) !important;
                text-align: center;
                transition: color var(--dur-fast) var(--ease-std);
            }

            .matrix-input input::placeholder {
                color: var(--text-placeholder) !important;
                -webkit-text-fill-color: var(--text-placeholder) !important;
                opacity: 0.5 !important;
            }

            /* === ETIQUETAS MATEMÁTICAS === */
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

            /* === BOTONES PRIMARIOS === */
            .btn-primary {
                background: var(--btn-primary-bg) !important;
                color: var(--btn-primary-text) !important;
                border-radius: var(--radius-btn) !important;
                font-weight: 700;
                box-shadow: var(--elev-2) !important;
                transition: box-shadow var(--dur-fast) var(--ease-std),
                            transform var(--dur-fast) var(--ease-std);
            }
            .btn-primary:hover, .btn-ghost:hover, .btn-neo-icon:hover, .btn-neo-calc:hover {
                box-shadow: var(--elev-3) !important;
                transform: scale(1.02);
            }
            .btn-primary:active {
                box-shadow: var(--elev-inset) !important;
                transform: scale(0.97);
            }

            /* === BOTONES FANTASMA === */
            .btn-ghost {
                background: transparent !important;
                color: var(--text-main) !important;
                border: none !important;
                border-radius: var(--radius-btn) !important;
                font-weight: 600;
                box-shadow: var(--elev-1) !important;
                transition: box-shadow var(--dur-fast) var(--ease-std),
                            transform var(--dur-fast) var(--ease-std);
            }
            .btn-ghost:active {
                box-shadow: var(--elev-inset) !important;
                transform: scale(0.97);
            }

            /* === BADGES DE ESTADO (Embossed) === */
            .badge-error, .badge-success, .badge-warning {
                border-radius: var(--radius-badge) !important;
                box-shadow: var(--elev-1) !important;
                transition: box-shadow var(--dur-fast) var(--ease-std);
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
                padding: var(--space-1) !important;
                box-shadow: var(--elev-inset) !important;
            }
            .neo-tabs .q-tab {
                border-radius: var(--radius-pill) !important;
                min-height: 40px !important;
                padding: 0 var(--space-6) !important;
                color: var(--text-sec) !important;
                font-weight: 600 !important;
                transition: color var(--dur-med) var(--ease-std) !important;
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
                box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
                transition: all var(--dur-slow) var(--ease-elastic) !important;
            }
            .q-tab-panels { background: transparent !important; }

            /* === TABS MÉTODO (corte recto al centro) === */
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
                box-shadow: var(--elev-2) !important;
                transition: box-shadow var(--dur-med) var(--ease-elastic),
                            transform var(--dur-med) var(--ease-elastic) !important;
            }
            .btn-neo-icon:active {
                box-shadow: var(--elev-inset) !important;
                transform: scale(0.95);
            }

            /* === BOTONES CALCULADORA === */
            .btn-neo-calc {
                background: var(--bg-calc-btn) !important;
                color: var(--text-main) !important;
                border-radius: var(--radius-btn) !important;
                padding: 0 !important;
                box-shadow: var(--elev-2) !important;
                transition: box-shadow var(--dur-fast) var(--ease-elastic),
                            transform var(--dur-fast) var(--ease-elastic) !important;
            }
            .btn-neo-calc:active {
                box-shadow: var(--elev-inset) !important;
                transform: scale(0.95);
            }

            /* === MENÚ DESPLEGABLE Y QUASAR THEMING === */
            .q-menu, .q-tooltip, .q-select, .q-notification {
                background: var(--bg-elevated) !important;
                color: var(--text-main) !important;
                border-radius: var(--radius-input) !important;
                box-shadow: var(--elev-2) !important;
                font-family: 'Space Grotesk', sans-serif !important;
            }

            /* === ANIMACIONES === */
            @keyframes slideUpFadeIn {
                0%   { opacity: 0; transform: translateY(30px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            .animate-slide-up {
                animation: slideUpFadeIn var(--dur-slow) var(--ease-elastic) forwards !important;
            }

            @keyframes slideBounceVertical {
                0%   { opacity: 0; transform: translateY(-30px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            .animate-slide-bounce {
                animation: slideBounceVertical var(--dur-slow) var(--ease-elastic) forwards !important;
            }

            @keyframes shake {
              0%,100% { transform: translateX(0); }
              25% { transform: translateX(-4px); }
              75% { transform: translateX(4px); }
            }
            .animate-shake { animation: shake 120ms ease-in-out 2; }

            /* === MICRO-FEEDBACK TIPADO === */
            @keyframes keyPulse {
              0%   { transform: scale(1);    background: var(--input-bg); }
              40%  { transform: scale(1.04); background: color-mix(in srgb, var(--accent) 14%, var(--input-bg)); }
              100% { transform: scale(1);    background: var(--input-bg); }
            }
            @keyframes keyPulseColor {
                0% { opacity: 0; }
                100% { opacity: 1; }
            }
            .key-pulse .q-field__control { animation: keyPulse 180ms var(--ease-std); }
            .key-pulse input { animation: keyPulseColor 90ms ease-out forwards; }

            /* === TYPEWRITER CURSOR === */
            @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
            .tw-cursor { animation: blink 1s step-end infinite; color: var(--accent); margin-left: 2px; }

            /* === TIMELINE EXPANSION (Stagger) === */
            .timeline-expansion .q-expansion-item__content > * {
                opacity: 0;
                transform: translateY(10px);
                animation: slideUpFadeIn var(--dur-med) var(--ease-std) forwards;
            }
            .timeline-expansion .q-expansion-item__content > *:nth-child(1) { animation-delay: 0ms; }
            .timeline-expansion .q-expansion-item__content > *:nth-child(2) { animation-delay: 40ms; }
            .timeline-expansion .q-expansion-item__content > *:nth-child(3) { animation-delay: 80ms; }
            .timeline-expansion .q-expansion-item__content > *:nth-child(4) { animation-delay: 120ms; }
            .timeline-expansion .q-expansion-item__content > *:nth-child(5) { animation-delay: 160ms; }
            .timeline-expansion .q-expansion-item__content > *:nth-child(6) { animation-delay: 200ms; }
            .timeline-expansion .q-expansion-item__content > *:nth-child(7) { animation-delay: 240ms; }
            .timeline-expansion .q-expansion-item__content > *:nth-child(8) { animation-delay: 280ms; }
            .timeline-expansion .q-expansion-item__content > *:nth-child(9) { animation-delay: 320ms; }
            .timeline-expansion .q-expansion-item__content > *:nth-child(n+10) { animation-delay: 360ms; }

            /* === VIEW TRANSITIONS (TEMA Y NAVEGACIÓN) === */
            @view-transition { navigation: auto; }

            ::view-transition-old(root),
            ::view-transition-new(root) {
                animation: none;
                mix-blend-mode: normal;
            }
            ::view-transition-old(root) { z-index: 1; }
            ::view-transition-new(root) { z-index: 2; }
            
            /* Fallback para navegadores sin View Transitions */
            @keyframes viewFadeIn {
                0% { opacity: 0; }
                100% { opacity: 1; }
            }
            .q-page, .nicegui-content {
                animation: viewFadeIn .18s ease-out both;
            }

            /* === SQUASH BOUNCE (BOTÓN LIMPIAR) === */
            @keyframes squashBounce {
                0%   { transform: scale(1); }
                30%  { transform: scale(1.1, 0.9); }
                50%  { transform: scale(0.9, 1.1); }
                70%  { transform: scale(1.05, 0.95); }
                100% { transform: scale(1); }
            }
            .squash-bounce {
                animation: squashBounce var(--dur-slow) var(--ease-elastic) forwards !important;
            }

            /* === ACCESIBILIDAD: Focus visible === */
            :focus-visible {
                outline: 2px solid var(--focus-ring) !important;
                outline-offset: 2px;
            }
            /* Los inputs de matriz manejan focus vía Quasar (.q-field--focused) */
            .matrix-input input:focus-visible {
                outline: none !important;
            }

            /* === ACCESIBILIDAD: Reduced motion === */
            @media (prefers-reduced-motion: reduce) {
                *, *::before, *::after {
                    animation-duration: 120ms !important;
                    animation-timing-function: ease !important;
                    transition-duration: 120ms !important;
                }
            }
        </style>
        
        <script>
            // Constantes de movimiento (espejo de los tokens CSS para uso en JS)
            window.MOTION = { fast: 120, med: 240, slow: 500 };

            // Rastreador del clic del mouse para animación de onda expansiva
            window.lastMouseClick = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
            document.addEventListener('click', e => {
                window.lastMouseClick = { x: e.clientX, y: e.clientY };
            }, { capture: true });
            
            // Micro-feedback al escribir en inputs de matriz/ecuación
            document.addEventListener('input', e => {
                if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
                const target = e.target;
                if (target.matches('.matrix-input input')) {
                    const wrapper = target.closest('.matrix-input');
                    if (wrapper) {
                        wrapper.classList.remove('key-pulse');
                        void wrapper.offsetWidth; // force reflow
                        wrapper.classList.add('key-pulse');
                        wrapper.addEventListener('animationend', () => wrapper.classList.remove('key-pulse'), {once: true});
                    }
                }
            });

            // Función global robusta para MathJax con fallback de carga asíncrona
            window.typesetMathWhenReady = function(elementIds, maxWaitMs) {
                maxWaitMs = maxWaitMs || 5000;
                var start = Date.now();
                function attempt() {
                    if (window.MathJax && window.MathJax.typesetPromise) {
                        if (elementIds && elementIds.length) {
                            var els = elementIds.map(id => document.getElementById(id)).filter(Boolean);
                            if (els.length > 0) {
                                window.MathJax.typesetClear(els);
                                window.MathJax.typesetPromise(els).catch(err => console.log(err));
                            }
                        } else {
                            window.MathJax.typesetClear();
                            window.MathJax.typesetPromise().catch(err => console.log(err));
                        }
                    } else if (Date.now() - start < maxWaitMs) {
                        setTimeout(attempt, 100);
                    }
                }
                attempt();
            };

            // Máquina de escribir para explicaciones
            window.typewriterEffect = function(elementId, text, speed = 18) {
                if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
                    const el = document.getElementById(elementId);
                    if(el) el.textContent = text;
                    return;
                }
                const el = document.getElementById(elementId);
                if (!el) return;
                
                el.innerHTML = '<span class="tw-text"></span><span class="tw-cursor">▌</span>';
                const textSpan = el.querySelector('.tw-text');
                const cursorSpan = el.querySelector('.tw-cursor');
                let i = 0;
                
                const skip = () => {
                    textSpan.textContent = text;
                    cursorSpan.style.display = 'none';
                    el.removeEventListener('click', skip);
                };
                el.addEventListener('click', skip);
                
                function type() {
                    if (i < text.length) {
                        textSpan.textContent += text.charAt(i);
                        i++;
                        setTimeout(type, speed);
                    } else {
                        cursorSpan.style.display = 'none';
                        el.removeEventListener('click', skip);
                    }
                }
                type();
            };
            
            function updatePlotlyTheme(theme) {
                let textColor = '#23262E';
                let gridColor = 'rgba(128,128,128,0.2)';
                if(theme === 'medianoche') { textColor = '#EAF6FF'; gridColor = 'rgba(255,255,255,0.06)'; }
                if(theme === 'marea') { textColor = '#0B1F33'; gridColor = 'rgba(11,31,51,0.1)'; }
                
                document.querySelectorAll('.js-plotly-plot').forEach(plot => {
                    Plotly.relayout(plot, {
                        'font.color': textColor,
                        'scene.xaxis.gridcolor': gridColor,
                        'scene.yaxis.gridcolor': gridColor,
                        'scene.zaxis.gridcolor': gridColor
                    }).catch(() => {}); // Ignorar si no está inicializado
                });
            }

            function applyTheme(themeName) {
                document.documentElement.setAttribute('data-theme', themeName);
                document.documentElement.style.colorScheme = (themeName === 'medianoche') ? 'dark' : 'light';
                localStorage.setItem('theme', themeName);
                setTimeout(() => updatePlotlyTheme(themeName), 100);
            }

            /* 1. Guardar el origen del clic antes de navegar */
            addEventListener('click', function (e) {
              try {
                sessionStorage.setItem('nav-origin', JSON.stringify({ x: e.clientX, y: e.clientY }));
              } catch (_) {}
            }, { capture: true });

            /* 2. Animar el documento entrante con el mismo reveal circular */
            addEventListener('pagereveal', function (e) {
              if (!e.viewTransition) return;
              var o = { x: innerWidth / 2, y: innerHeight / 2 };
              try { o = JSON.parse(sessionStorage.getItem('nav-origin')) || o; } catch (_) {}
              if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

              e.viewTransition.ready.then(function () {
                var r = Math.hypot(Math.max(o.x, innerWidth - o.x), Math.max(o.y, innerHeight - o.y));
                document.documentElement.animate(
                  { clipPath: ['circle(0px at ' + o.x + 'px ' + o.y + 'px)',
                               'circle(' + r + 'px at ' + o.x + 'px ' + o.y + 'px)'] },
                  { duration: 500, easing: 'cubic-bezier(0.32, 0.72, 0, 1)',
                    pseudoElement: '::view-transition-new(root)' }
                );
              });
            });

            function setTheme(themeName) {
                if (!document.startViewTransition) {
                    applyTheme(themeName);
                    return;
                }
                
                const x = window.lastMouseClick.x;
                const y = window.lastMouseClick.y;
                const endRadius = Math.hypot(
                    Math.max(x, window.innerWidth - x),
                    Math.max(y, window.innerHeight - y)
                );
                
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
                            duration: MOTION.slow,
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
                    iconElem.textContent = 'delete_sweep';
                    iconElem.classList.add('text-negative');
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
                    
                    clone.style.transition = `all ${MOTION.slow}ms cubic-bezier(0.34, 1.56, 0.64, 1)`;
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
                    
                    setTimeout(() => clone.remove(), delay + MOTION.slow);
                    
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
                        }, MOTION.slow);
                    }, delay + MOTION.med);
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

@app.get('/')
def index_redirect():
    return RedirectResponse('/sistemas-lineales')

@app.get('/gauss')
def redirect_gauss():
    return RedirectResponse('/sistemas-lineales?method=gauss')

@app.get('/gauss-jordan')
def redirect_gauss_jordan():
    return RedirectResponse('/sistemas-lineales?method=gauss-jordan')

@ui.page('/sistemas-lineales')
def linear_systems_page(method: str = 'gauss'):
    from src.frontend.views.linear_systems.view_linear_systems import LinearSystemsUI
    setup_theme()
    app_ui = LinearSystemsUI(initial_method=method)
    app_ui.build()

@ui.page('/operaciones-matrices')
def matrix_ops_page():
    from src.frontend.views.matrix_ops.view_matrix_ops import MatrixOpsUI
    setup_theme()
    app_ui = MatrixOpsUI()
    app_ui.build()



# ---> AQUÍ PEGÁS LO NUEVO <---
@ui.page('/conversor')
def conversor_page():
    from src.frontend.views.numeric_systems.view_numeric_systems import NumericSystemsUI
    setup_theme()
    app_ui = NumericSystemsUI()
    app_ui.build()
# ------------------------------

@app.get('/ia')
def vista_ia_redirect():
    return RedirectResponse('/sistemas-lineales')

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Calculadora Álgebra Lineal UAM",
           favicon="src/frontend/assets/LogoOscuro.png",
           storage_secret="alg_lineal_uam_secreto")