"""Configuración de temas, paletas y assets estáticos de Scalaris."""
import json
from nicegui import ui

from src.frontend import flags

# Paletas de color con ratio de contraste no textual >= 3.0:1 verificado en cada tema
PALETAS_POR_TEMA: dict[str, list[str]] = {
    "papel": ["#C71F47", "#0D7A53", "#1D6FB8", "#B45309", "#6D28D9"],
    "marea": ["#B91C47", "#0D6E48", "#145A96", "#9A4500", "#5B21B6"],
    "medianoche": ["#FB7185", "#34D399", "#38BDF8", "#FBBF24", "#A78BFA"],
}

COLORES_SOLUCION_POR_TEMA: dict[str, str] = {
    "papel": "#BE123C",
    "marea": "#B91C47",
    "medianoche": "#F43F5E",
}

COLORES_TEXTO_GRAFICOS: dict[str, str] = {
    "papel": "#23262E",
    "marea": "#0B1F33",
    "medianoche": "#EAF6FF",
}

COLORES_CUADRICULA_GRAFICOS: dict[str, str] = {
    "papel": "rgba(128,128,128,0.2)",
    "marea": "rgba(11,31,51,0.1)",
    "medianoche": "rgba(255,255,255,0.06)",
}

# Constantes públicas para compatibilidad con escenas existentes
CHART_PALETTE = PALETAS_POR_TEMA["papel"]
CHART_MARKER_LIGHT = "#FFFFFF"
CHART_MARKER_BORDER = "#23262E"
CHART_GRID_COLOR = "rgba(128,128,128,0.2)"
CHART_ZERO_COLOR = "rgba(128,128,128,0.5)"
CHART_FONT_COLOR = COLORES_TEXTO_GRAFICOS
CHART_SOLUTION_COLOR = COLORES_SOLUCION_POR_TEMA["papel"]


def obtener_paleta_tema(tema: str = "papel") -> list[str]:
    """Devuelve la paleta de colores con contraste óptimo para el tema solicitado."""
    return PALETAS_POR_TEMA.get(tema, PALETAS_POR_TEMA["papel"])


def obtener_color_solucion(tema: str = "papel") -> str:
    """Devuelve el color de solución con contraste garantizado para el tema."""
    return COLORES_SOLUCION_POR_TEMA.get(tema, COLORES_SOLUCION_POR_TEMA["papel"])


_CONFIG_GRAFICOS_JSON = json.dumps(
    {
        "paletas": PALETAS_POR_TEMA,
        "solucion": COLORES_SOLUCION_POR_TEMA,
        "texto": COLORES_TEXTO_GRAFICOS,
        "cuadricula": COLORES_CUADRICULA_GRAFICOS,
    }
)

_HEAD_HTML = f"""
    <!-- Prevenir FOUC (Flash of Unstyled Content) y exponer tokens a JS -->
    <script>
    (function () {{
      var mapa = {{claro: 'papel', aqua: 'marea', oscuro: 'medianoche'}};
      var t = localStorage.getItem('theme') || 'papel';
      if (mapa[t]) {{ t = mapa[t]; localStorage.setItem('theme', t); }}
      var r = document.documentElement;
      r.setAttribute('data-theme', t);
      r.style.colorScheme = (t === 'medianoche') ? 'dark' : 'light';
      window.scalaris = window.scalaris || {{}};
      window.scalaris.graficos = {_CONFIG_GRAFICOS_JSON};
    }})();
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
    """Configura fuentes, hojas de estilo, MathJax y scripts globales de interfaz."""
    ui.add_head_html(_HEAD_HTML)
    if flags.dock_enabled():
        ui.add_head_html(_DOCK_HEAD_HTML)
