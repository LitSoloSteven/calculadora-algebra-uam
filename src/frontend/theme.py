"""Configuración de temas, paletas y assets estáticos de Scalaris."""
from nicegui import ui

CHART_PALETTE = ['#E8466D', '#2EB88A', '#4B9FE8', '#E89F42', '#8B5CF6']
CHART_MARKER_LIGHT = '#FFFFFF'
CHART_MARKER_BORDER = '#23262E'
CHART_GRID_COLOR = 'rgba(128,128,128,0.2)'
CHART_ZERO_COLOR = 'rgba(128,128,128,0.5)'
CHART_FONT_COLOR = {'papel': '#23262E', 'marea': '#0B1F33', 'medianoche': '#EAF6FF'}
CHART_SOLUTION_COLOR = '#E11D48'

_HEAD_HTML = """
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
    <script src="/assets/js/splash.js"></script>

    <!-- Configuración e importación de MathJax -->
    <script src="/assets/js/mathjax_config.js"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

    <!-- Tipografía Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">

    <!-- Estilos de tema y diseño visual -->
    <link rel="stylesheet" href="/assets/css/theme.css">
    <link rel="stylesheet" href="/assets/css/reproductor_pasos.css">

    <!-- Scripts de interactividad y tema -->
    <script src="/assets/js/theme.js"></script>
    <script src="/assets/js/app.js"></script>
    <script src="/assets/js/reproductor_pasos.js"></script>
    <script src="/assets/js/hub.js"></script>
"""

from src.frontend import flags

_DOCK_HEAD_HTML = """
    <!-- Pre-paint de Glosa -->
    <script>
    try {
        if (window.matchMedia('(min-width: 1024px)').matches) {
            const state = localStorage.getItem('scalaris:glosa');
            if (state === 'open') {
                document.documentElement.setAttribute('data-glosa', 'open');
            } else {
                document.documentElement.setAttribute('data-glosa', 'closed');
            }
        } else {
            document.documentElement.setAttribute('data-glosa', 'closed');
        }
    } catch(e) {}
    </script>
    <script src="/assets/js/glosa_dock.js"></script>
    <script src="/assets/js/layout_sync.js"></script>
"""

def setup_theme():
    """Configura fuentes, hojas de estilo, MathJax y scripts globales."""
    ui.add_head_html(_HEAD_HTML)
    if flags.dock_enabled():
        ui.add_head_html(_DOCK_HEAD_HTML)
