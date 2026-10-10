"""Vista del Modelo de Insumo-Producto de Leontief (P5 - LIT-8).

Layout:
  - Panel izquierdo: captura de C (n×n) y d (vector de demanda), selector de sectores
    y 3 presets (2 sectores simple, 3 sectores, economía inviable).
  - Panel derecho: resultados del solver (M = I-C, multiplicador, Hawkins-Simon,
    vector de producción x, análisis sectorial).
"""
import json
import asyncio
import logging
import html
from functools import partial

from nicegui import ui

logger = logging.getLogger(__name__)

from src.frontend.components.app_shell import create_app_shell
from src.frontend.navigation import route_of
from src.frontend.controllers.matrix_ops.controller_leontief import LeontiefController


# ══════════════════════════════════════════════════════════════════════════
# Presets de demostración
# ══════════════════════════════════════════════════════════════════════════

PRESETS_LEONTIEF = [
    {
        "nombre": "2 Sectores (simple)",
        "descripcion": "Economía de 2 sectores viable con solución entera.",
        "sectores": ["Agricultura", "Industria"],
        "C": [["0.2", "0.3"], ["0.4", "0.1"]],
        "d": ["120", "80"],
    },
    {
        "nombre": "3 Sectores",
        "descripcion": "Economía completa de 3 sectores con Hawkins-Simon ✓.",
        "sectores": ["Agricultura", "Industria", "Servicios"],
        "C": [["0.1", "0.2", "0.1"], ["0.2", "0.3", "0.2"], ["0.1", "0.1", "0.3"]],
        "d": ["100", "200", "150"],
    },
    {
        "nombre": "Inviable (H-S falla)",
        "descripcion": "Coeficientes excesivos: no satisface Hawkins-Simon.",
        "sectores": ["Sector A", "Sector B"],
        "C": [["0.8", "0.5"], ["0.6", "0.9"]],
        "d": ["50", "50"],
    },
]


class LeontiefUI:
    """Vista completa del Modelo de Leontief."""

    def __init__(self):
        self.n = 2
        self.entradas_C: list[list] = []   # widgets de entrada de C
        self.entradas_d: list = []          # widgets de entrada de d
        self.entradas_sectores: list = []   # widgets de nombre de sector
        self.contenedor_C = None
        self.contenedor_resultados = None
        self.last_result = None

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self):
        create_app_shell(self, active_route=route_of("leontief"))

        with ui.column().classes("w-full max-w-7xl mx-auto p-6 mt-4 view-root"):
            # Header
            with ui.row().classes("w-full items-center gap-3 mb-6"):
                ui.icon("matriz_inversa", size="2rem").classes("text-accent")
                with ui.column().classes("gap-0"):
                    ui.label("Modelo de Leontief").classes("text-2xl font-bold text-main")
                    ui.label("Insumo-Producto · x = (I - C)^(-1) d").classes("text-sm text-sec")

            with ui.element("div").classes("layout-split mb-8"):
                # ── Panel izquierdo ────────────────────────────────────
                with ui.column().classes("layout-pane"):
                    self._build_presets()
                    self._build_tamano_selector()
                    self._build_panel_C()
                    self._build_panel_d()
                    self._build_panel_sectores()

                    with ui.row().classes("w-full mt-6 gap-4"):
                        ui.button(
                            "Calcular", icon="calculate",
                            on_click=lambda e: self._calcular(e.sender),
                            color=None
                        ).classes("btn-primary flex-[2] py-3").props("ripple=false")

                # ── Panel derecho ──────────────────────────────────────
                with ui.column().classes("layout-pane"):
                    self.contenedor_resultados = ui.column().classes(
                        "w-full panel-card p-6 items-center justify-center min-h-[400px]"
                    ).props('id="resultados-leontief"')
                    self._reset_resultados()

    # ------------------------------------------------------------------
    # Sub-builders de panel izquierdo
    # ------------------------------------------------------------------

    def _build_presets(self):
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Ejemplos precargados").classes("font-bold text-main mb-2 text-sm uppercase tracking-wide")
            with ui.row().classes("gap-2 flex-wrap"):
                for preset in PRESETS_LEONTIEF:
                    ui.button(
                        preset["nombre"],
                        on_click=lambda p=preset: self._cargar_preset(p),
                        color=None,
                    ).classes("btn-ghost text-xs py-1 px-3").props("ripple=false").tooltip(preset["descripcion"])

    def _build_tamano_selector(self):
        with ui.row().classes("w-full items-center gap-3 mb-2"):
            ui.label("Tamaño n×n:").classes("text-sm font-bold text-sec")
            ui.button(icon="remove", on_click=partial(self._ajustar_tamano, -1), color=None).classes("btn-neo-icon w-7 h-7 p-0").props('ripple=false aria-label="Reducir dimension"')
            ui.button(icon="add", on_click=partial(self._ajustar_tamano, 1), color=None).classes("btn-neo-icon w-7 h-7 p-0").props('ripple=false aria-label="Aumentar dimension"')

    def _build_panel_C(self):
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Matriz de coeficientes técnicos C").classes("font-bold text-main mb-3")
            ui.html(
                '<p class="text-xs text-sec mb-2">Cada c<sub>ij</sub> indica la fracción de la producción del sector '
                "<i>i</i> que consume el sector <i>j</i> por unidad producida.</p>"
            )
            self.contenedor_C = ui.column().classes("w-full")
            self._generar_cuadricula_C()

    def _build_panel_d(self):
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Vector de demanda final d").classes("font-bold text-main mb-3")
            self.contenedor_d = ui.column().classes("w-full")
            self._generar_entradas_d()

    def _build_panel_sectores(self):
        with ui.column().classes("w-full panel-card p-4"):
            ui.label("Nombres de sectores (opcional)").classes("font-bold text-main mb-3 text-sm")
            self.contenedor_sectores = ui.column().classes("w-full")
            self._generar_entradas_sectores()

    # ------------------------------------------------------------------
    # Generadores de cuadrícula
    # ------------------------------------------------------------------

    def _generar_cuadricula_C(self):
        self.contenedor_C.clear()
        self.entradas_C = []
        with self.contenedor_C:
            for i in range(self.n):
                fila_widgets = []
                with ui.row().classes("gap-1"):
                    for j in range(self.n):
                        inp = ui.input(placeholder="0").classes(
                            "matrix-input w-16 text-center"
                        ).props(f'aria-label="C[{i+1},{j+1}]"')
                        fila_widgets.append(inp)
                self.entradas_C.append(fila_widgets)

    def _generar_entradas_d(self):
        self.contenedor_d.clear()
        self.entradas_d = []
        with self.contenedor_d:
            with ui.row().classes("gap-2 flex-wrap"):
                for i in range(self.n):
                    inp = ui.input(placeholder="0", label=f"d{i+1}").classes(
                        "matrix-input w-20 text-center"
                    ).props(f'aria-label="d[{i+1}]"')
                    self.entradas_d.append(inp)

    def _generar_entradas_sectores(self):
        self.contenedor_sectores.clear()
        self.entradas_sectores = []
        with self.contenedor_sectores:
            with ui.row().classes("gap-2 flex-wrap"):
                for i in range(self.n):
                    inp = ui.input(placeholder=f"Sector {i+1}", label=f"Sector {i+1}").classes(
                        "matrix-input w-28"
                    ).props(f'aria-label="nombre sector {i+1}"')
                    self.entradas_sectores.append(inp)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _ajustar_tamano(self, delta: int):
        nuevo_n = self.n + delta
        if not (2 <= nuevo_n <= 8):
            return
        self.n = nuevo_n
        self._generar_cuadricula_C()
        self._generar_entradas_d()
        self._generar_entradas_sectores()

    def _cargar_preset(self, preset: dict):
        C = preset["C"]
        nuevo_n = len(C)
        if nuevo_n != self.n:
            self.n = nuevo_n
            self._generar_cuadricula_C()
            self._generar_entradas_d()
            self._generar_entradas_sectores()

        for i in range(self.n):
            for j in range(self.n):
                self.entradas_C[i][j].value = C[i][j]
        for i, v in enumerate(preset["d"]):
            self.entradas_d[i].value = v
        sectores = preset.get("sectores", [])
        for i, inp in enumerate(self.entradas_sectores):
            inp.value = sectores[i] if i < len(sectores) else ""
        ui.notify(f"Preset '{preset['nombre']}' cargado.", type="positive", position="top")

    async def _calcular(self, btn):
        btn.props("loading=true")
        try:
            await asyncio.sleep(0.1)
            await self._calcular_core()
        except Exception as e:
            logger.error("Error inesperado en Leontief", exc_info=e)
            self.contenedor_resultados.clear()
            with self.contenedor_resultados:
                with ui.row().classes("items-center gap-2 px-4 py-2 badge-error mb-4 w-fit"):
                    ui.icon("close", size="sm")
                    ui.label("Error inesperado. Revisa los datos e inténtalo de nuevo.").classes("font-bold")
        finally:
            btn.props("loading=false")

    async def _calcular_core(self):
        # Recoger C
        C_raw = []
        for i in range(self.n):
            fila = []
            for j in range(self.n):
                fila.append(self.entradas_C[i][j].value or "0")
            C_raw.append(fila)

        d_raw = [inp.value or "0" for inp in self.entradas_d]
        sectores_raw = [inp.value.strip() for inp in self.entradas_sectores]
        sectores = [s if s else f"Sector {i+1}" for i, s in enumerate(sectores_raw)]

        payload = json.dumps({"C": C_raw, "d": d_raw, "sectores": sectores})
        respuesta_str = LeontiefController.procesar(payload)
        respuesta = json.loads(respuesta_str)
        self.last_result = respuesta

        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            self.contenedor_resultados.classes(
                remove="items-center justify-center", add="items-start justify-start"
            )
            self._renderizar_resultado(respuesta)

        ui.run_javascript("typesetMathWhenReady();")
        ui.run_javascript(
            "setTimeout(() => { const el = document.getElementById('resultados-leontief'); "
            "if(el) el.scrollIntoView({behavior: 'smooth', block: 'start'}) }, 300);"
        )

    # ------------------------------------------------------------------
    # Renderizado de resultados
    # ------------------------------------------------------------------

    def _renderizar_resultado(self, r: dict):
        status = r.get("status")

        if status == "ERROR":
            with ui.row().classes("items-center gap-2 px-4 py-2 badge-error mb-4 w-fit"):
                ui.icon("close", size="sm")
                ui.label(r.get("message", "Error")).classes("font-bold")
            return

        if status == "SINGULAR":
            with ui.row().classes("items-center gap-2 px-4 py-2 badge-error mb-4 w-fit"):
                ui.icon("warning_amber", size="sm")
                ui.label(r.get("message")).classes("font-bold")
            hs = r.get("hawkins_simon", {})
            if hs:
                self._renderizar_hawkins_simon(hs)
            return

        # ── SUCCESS ────────────────────────────────────────────────────
        with ui.row().classes("items-center gap-2 px-4 py-2 badge-success mb-4 w-fit"):
            ui.icon("check", size="sm")
            ui.label(r.get("message", "")).classes("font-bold")

        # ── Hawkins-Simon ──────────────────────────────────────────────
        self._renderizar_hawkins_simon(r.get("hawkins_simon", {}))

        # ── Fórmula M = I − C ─────────────────────────────────────────
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Matriz de Leontief  M = I - C").classes("font-bold text-main mb-2")
            m_tex = html.escape(r.get("matriz_leontief_latex", ""))
            ui.html(f'<div class="math-scroll-container math-label text-xl text-center">$$ M = {m_tex} $$</div>')

        # ── Multiplicador M^{-1} ──────────────────────────────────────
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Multiplicador de Leontief  (I - C)^(-1)").classes("font-bold text-main mb-2")
            mul_tex = html.escape(r.get("matriz_multiplicador_latex", ""))
            ui.html(f'<div class="math-scroll-container math-label text-xl text-center">$$ (I-C)^{{-1}} = {mul_tex} $$</div>')

        # ── Vector de producción x = (I-C)^{-1} d ─────────────────────
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Vector de producción  x = (I - C)^(-1) · d").classes("font-bold text-main mb-3")
            sectores = r.get("sectores", [])
            prods = r.get("vector_produccion", [])
            dems = r.get("vector_demanda", [])
            with ui.column().classes("w-full gap-2"):
                for i, (sect, prod, dem) in enumerate(zip(sectores, prods, dems)):
                    with ui.row().classes("w-full items-center gap-3 panel-card p-3"):
                        ui.label(sect).classes("font-bold text-main min-w-[100px]")
                        with ui.column().classes("gap-0"):
                            ui.html(f'<span class="text-sm text-sec">Demanda final: <b>{html.escape(dem)}</b></span>')
                            ui.html(f'<span class="font-bold text-accent">Producción total: {html.escape(prod)}</span>')

        # ── Análisis sectorial ─────────────────────────────────────────
        analisis = r.get("analisis_sectorial", [])
        if analisis:
            with ui.column().classes("w-full panel-card p-4 mb-4"):
                ui.label("Análisis Sectorial").classes("font-bold text-main mb-3")
                with ui.expansion("Ver desglose por sector", icon="table_chart").classes("w-full").props('header-class="font-bold text-main"'):
                    with ui.column().classes("w-full gap-2 mt-2"):
                        headers = ["Sector", "Producción Total", "Insumos Intermedios", "Demanda Final", "Valor Añadido"]
                        with ui.row().classes("gap-3 w-full"):
                            for h in headers:
                                ui.label(h).classes("text-xs font-bold text-sec uppercase tracking-wide flex-1")
                        for fila in analisis:
                            with ui.row().classes("w-full gap-3 panel-card p-2"):
                                ui.label(fila["sector"]).classes("font-bold text-main flex-1 text-sm")
                                ui.label(fila["produccion_total"]).classes("flex-1 text-sm")
                                ui.label(fila["insumos_intermedios"]).classes("flex-1 text-sm")
                                ui.label(fila["demanda_final"]).classes("flex-1 text-sm")
                                ui.label(fila["valor_anadido"]).classes("flex-1 text-sm")

    def _renderizar_hawkins_simon(self, hs: dict):
        if not hs:
            return
        viable = hs.get("viable", False)
        badge = "badge-success" if viable else "badge-warning"
        icon = "verified" if viable else "warning_amber"
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            with ui.row().classes(f"items-center gap-2 px-4 py-2 {badge} mb-3 w-fit"):
                ui.icon(icon, size="sm")
                label_text = "Condición de Hawkins-Simon: SATISFECHA ✓" if viable else "Condición de Hawkins-Simon: NO satisfecha ✗"
                ui.label(label_text).classes("font-bold")
            ui.label(hs.get("conclusion", "")).classes("text-sm text-sec mb-2")
            menores = hs.get("menores", [])
            if menores:
                with ui.row().classes("gap-2 flex-wrap mt-2"):
                    for m in menores:
                        badge_m = "badge-success" if m["positivo"] else "badge-error"
                        ui.html(
                            f'<span class="px-3 py-1 rounded-full text-xs font-bold {badge_m}">'
                            f'Δ<sub>{m["orden"]}</sub> = {html.escape(m["determinante"])}</span>'
                        )

    def _reset_resultados(self):
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.icon("matriz_inversa", size="4rem").classes("text-placeholder mb-4")
            ui.label("Listo para calcular").classes("text-xl font-bold text-main")
            ui.label("Ingresa la matriz C y el vector d, luego presiona Calcular.").classes(
                "text-sm text-sec mt-2 text-center"
            )

    # ------------------------------------------------------------------
    # AI context stub (requerido por create_app_shell si usa ai_panel)
    # ------------------------------------------------------------------

    def get_ai_context(self):
        return None

    def get_ai_signals(self):
        return None