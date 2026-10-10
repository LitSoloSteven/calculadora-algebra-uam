"""Vista de Transformaciones Lineales T: R^n → R^m (P5 — LIT-8).

Layout:
  - Panel izquierdo: captura de la matriz A (m×n), nombres de variables
    y 4 presets geométricos (identidad 2D, reflexión, proyección, rotación 90°,
    shear, expansión a 3D).
  - Panel derecho: resultados (ker(T), Im(T), rango, nulidad, Teorema de la
    Dimensión, callout de convención de subespacios).
"""
import json
import asyncio
import logging
import html

from nicegui import ui

logger = logging.getLogger(__name__)

from src.frontend.components.app_shell import create_app_shell
from src.frontend.navigation import route_of
from src.frontend.controllers.matrix_ops.controller_transformaciones import TransformacionesController


# ══════════════════════════════════════════════════════════════════════════
# Presets de demostración geométrica
# ══════════════════════════════════════════════════════════════════════════

PRESETS_TRANSFORMACIONES = [
    {
        "nombre": "Identidad 2D",
        "descripcion": "T(x)=x. Biyectiva, rango=2, nulidad=0.",
        "A": [["1", "0"], ["0", "1"]],
        "variables": ["x₁", "x₂"],
    },
    {
        "nombre": "Reflexión eje x",
        "descripcion": "T reflejan en el eje x. Biyectiva.",
        "A": [["1", "0"], ["0", "-1"]],
        "variables": ["x₁", "x₂"],
    },
    {
        "nombre": "Proyección sobre eje x",
        "descripcion": "T proyecta en el eje x. No inyectiva (ker ≠ {0}). Núcleo = span{e₂}.",
        "A": [["1", "0"], ["0", "0"]],
        "variables": ["x₁", "x₂"],
    },
    {
        "nombre": "Rotación 90°",
        "descripcion": "T rota vectores 90° en sentido antihorario. Biyectiva.",
        "A": [["0", "-1"], ["1", "0"]],
        "variables": ["x₁", "x₂"],
    },
    {
        "nombre": "R² → R³ (inyectiva)",
        "descripcion": "Embedding de R² en R³. Inyectiva, no sobreyectiva.",
        "A": [["1", "0"], ["0", "1"], ["0", "0"]],
        "variables": ["x₁", "x₂"],
    },
    {
        "nombre": "R³ → R² (sobreyectiva)",
        "descripcion": "Proyección de R³ a R². Sobreyectiva, no inyectiva.",
        "A": [["1", "0", "0"], ["0", "1", "0"]],
        "variables": ["x₁", "x₂", "x₃"],
    },
]


class TransformacionesUI:
    """Vista completa de Transformaciones Lineales."""

    def __init__(self):
        self.m = 2  # filas de A (dimensión del codominio)
        self.n = 2  # columnas de A (dimensión del dominio)
        self.entradas_A: list[list] = []
        self.entradas_vars: list = []
        self.contenedor_A = None
        self.contenedor_vars = None
        self.contenedor_resultados = None
        self.last_result = None

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self):
        create_app_shell(self, active_route=route_of("transformaciones"))

        with ui.column().classes("w-full max-w-7xl mx-auto p-6 mt-4 view-root"):
            # Header
            with ui.row().classes("w-full items-center gap-3 mb-6"):
                ui.icon("transform", size="2rem").classes("text-accent")
                with ui.column().classes("gap-0"):
                    ui.label("Transformaciones Lineales").classes("text-2xl font-bold text-main")
                    ui.label("T: Rⁿ → Rᵐ · Núcleo · Imagen · Rango · Nulidad").classes("text-sm text-sec")

            with ui.element("div").classes("layout-split mb-8"):
                # ── Panel izquierdo ────────────────────────────────────
                with ui.column().classes("layout-pane"):
                    self._build_presets()
                    self._build_tamano_selector()
                    self._build_panel_A()
                    self._build_panel_variables()

                    with ui.row().classes("w-full mt-6 gap-4"):
                        ui.button(
                            "Analizar", icon="analytics",
                            on_click=lambda e: self._analizar(e.sender),
                            color=None,
                        ).classes("btn-primary flex-[2] py-3").props("ripple=false")

                # ── Panel derecho ──────────────────────────────────────
                with ui.column().classes("layout-pane"):
                    self.contenedor_resultados = ui.column().classes(
                        "w-full panel-card p-6 items-center justify-center min-h-[400px]"
                    ).props('id="resultados-transformaciones"')
                    self._reset_resultados()

    # ------------------------------------------------------------------
    # Sub-builders panel izquierdo
    # ------------------------------------------------------------------

    def _build_presets(self):
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Ejemplos geométricos").classes("font-bold text-main mb-2 text-sm uppercase tracking-wide")
            with ui.row().classes("gap-2 flex-wrap"):
                for preset in PRESETS_TRANSFORMACIONES:
                    ui.button(
                        preset["nombre"],
                        on_click=lambda p=preset: self._cargar_preset(p),
                        color=None,
                    ).classes("btn-ghost text-xs py-1 px-3").props("ripple=false").tooltip(preset["descripcion"])

    def _build_tamano_selector(self):
        with ui.row().classes("w-full items-center gap-3 mb-2 flex-wrap"):
            ui.label("Dimensiones A (m×n):").classes("text-sm font-bold text-sec")
            from functools import partial
            with ui.row().classes("gap-1 items-center"):
                ui.label("m=").classes("text-sm text-sec")
                ui.button(icon="remove", on_click=partial(self._ajustar_m, -1), color=None).classes("btn-neo-icon w-7 h-7 p-0").props("ripple=false")
                ui.button(icon="add", on_click=partial(self._ajustar_m, 1), color=None).classes("btn-neo-icon w-7 h-7 p-0").props("ripple=false")
            with ui.row().classes("gap-1 items-center"):
                ui.label("n=").classes("text-sm text-sec")
                ui.button(icon="remove", on_click=partial(self._ajustar_n, -1), color=None).classes("btn-neo-icon w-7 h-7 p-0").props("ripple=false")
                ui.button(icon="add", on_click=partial(self._ajustar_n, 1), color=None).classes("btn-neo-icon w-7 h-7 p-0").props("ripple=false")

    def _build_panel_A(self):
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Matriz A de la transformación").classes("font-bold text-main mb-3")
            ui.html(
                '<p class="text-xs text-sec mb-2">'
                "Ingresa la matriz A tal que T(x) = Ax. "
                "Filas m = dimensión del codominio R<sup>m</sup>, "
                "columnas n = dimensión del dominio R<sup>n</sup>.</p>"
            )
            self.contenedor_A = ui.column().classes("w-full")
            self._generar_cuadricula_A()

    def _build_panel_variables(self):
        with ui.column().classes("w-full panel-card p-4"):
            ui.label("Nombres de variables (opcional)").classes("font-bold text-main mb-2 text-sm")
            self.contenedor_vars = ui.column().classes("w-full")
            self._generar_entradas_vars()

    # ------------------------------------------------------------------
    # Generadores de cuadrícula
    # ------------------------------------------------------------------

    def _generar_cuadricula_A(self):
        self.contenedor_A.clear()
        self.entradas_A = []
        with self.contenedor_A:
            for i in range(self.m):
                fila_widgets = []
                with ui.row().classes("gap-1"):
                    for j in range(self.n):
                        inp = ui.input(placeholder="0").classes(
                            "matrix-input w-16 text-center"
                        ).props(f'aria-label="A[{i+1},{j+1}]"')
                        fila_widgets.append(inp)
                self.entradas_A.append(fila_widgets)

    def _generar_entradas_vars(self):
        self.contenedor_vars.clear()
        self.entradas_vars = []
        with self.contenedor_vars:
            with ui.row().classes("gap-2 flex-wrap"):
                for j in range(self.n):
                    inp = ui.input(placeholder=f"x{j+1}", label=f"Var {j+1}").classes(
                        "matrix-input w-16 text-center"
                    ).props(f'aria-label="variable {j+1}"')
                    self.entradas_vars.append(inp)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _ajustar_m(self, delta: int):
        nuevo = self.m + delta
        if not (1 <= nuevo <= 8):
            return
        self.m = nuevo
        self._generar_cuadricula_A()

    def _ajustar_n(self, delta: int):
        nuevo = self.n + delta
        if not (1 <= nuevo <= 8):
            return
        self.n = nuevo
        self._generar_cuadricula_A()
        self._generar_entradas_vars()

    def _cargar_preset(self, preset: dict):
        A = preset["A"]
        nuevo_m = len(A)
        nuevo_n = len(A[0]) if nuevo_m > 0 else 2
        if nuevo_m != self.m or nuevo_n != self.n:
            self.m, self.n = nuevo_m, nuevo_n
            self._generar_cuadricula_A()
            self._generar_entradas_vars()
        for i in range(self.m):
            for j in range(self.n):
                self.entradas_A[i][j].value = A[i][j]
        vars_ = preset.get("variables", [])
        for j, inp in enumerate(self.entradas_vars):
            inp.value = vars_[j] if j < len(vars_) else ""
        ui.notify(f"Preset '{preset['nombre']}' cargado.", type="positive", position="top")

    async def _analizar(self, btn):
        btn.props("loading=true")
        try:
            await asyncio.sleep(0.1)
            await self._analizar_core()
        except Exception as e:
            logger.error("Error inesperado en Transformaciones", exc_info=e)
            self.contenedor_resultados.clear()
            with self.contenedor_resultados:
                with ui.row().classes("items-center gap-2 px-4 py-2 badge-error mb-4 w-fit"):
                    ui.icon("close", size="sm")
                    ui.label("Error inesperado. Revisa los datos e inténtalo de nuevo.").classes("font-bold")
        finally:
            btn.props("loading=false")

    async def _analizar_core(self):
        A_raw = []
        for i in range(self.m):
            fila = [self.entradas_A[i][j].value or "0" for j in range(self.n)]
            A_raw.append(fila)

        vars_raw = [inp.value.strip() for inp in self.entradas_vars]
        variables = [v if v else f"x{j+1}" for j, v in enumerate(vars_raw)]

        payload = json.dumps({"A": A_raw, "variables": variables})
        respuesta_str = TransformacionesController.procesar(payload)
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
            "setTimeout(() => { const el = document.getElementById('resultados-transformaciones'); "
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

        m, n = r.get("m"), r.get("n")
        rango = r.get("rango")
        nulidad = r.get("nulidad")
        es_iny = r.get("es_inyectiva")
        es_sob = r.get("es_sobreyectiva")

        # ── Banner éxito ───────────────────────────────────────────────
        with ui.row().classes("items-center gap-2 px-4 py-2 badge-success mb-4 w-fit"):
            ui.icon("check", size="sm")
            ui.label(r.get("message", "")).classes("font-bold")

        # ── Callout de convención (IMPORTANTE pedagógico) ──────────────
        callout = r.get("callout_convencion", "")
        if callout:
            with ui.row().classes("w-full items-start gap-2 px-4 py-3 rounded-lg mb-4").style(
                "background: var(--bg-accent-subtle, rgba(var(--accent-rgb), 0.08)); "
                "border-left: 3px solid var(--accent);"
            ):
                ui.icon("info", size="sm").classes("text-accent mt-0.5 flex-shrink-0")
                ui.label(callout).classes("text-xs text-sec")

        # ── Resumen rango / nulidad ────────────────────────────────────
        with ui.row().classes("w-full gap-4 mb-4 flex-wrap"):
            for label, val, color_class in [
                ("Rango", rango, "text-accent"),
                ("Nulidad", nulidad, "text-sec"),
                (f"T: R^{n} → R^{m}", "", ""),
            ]:
                with ui.column().classes("panel-card p-4 flex-1 items-center text-center gap-1"):
                    if val != "":
                        ui.label(str(val)).classes(f"text-3xl font-bold {color_class}")
                    ui.label(label).classes("text-sm text-sec")

        # Teorema de la dimensión
        with ui.row().classes("w-full panel-card p-3 mb-4 items-center gap-2"):
            ui.icon("functions", size="sm").classes("text-accent")
            ui.html(
                f'<span class="font-bold text-main">Teorema de la Dimensión:</span> '
                f'<span class="text-sec">{html.escape(r.get("teorema_dimension", ""))}</span>'
            )

        # ── Inyectividad / Sobreyectividad ─────────────────────────────
        conclusiones = r.get("conclusiones", {})
        with ui.column().classes("w-full panel-card p-4 mb-4 gap-2"):
            ui.label("Propiedades de T").classes("font-bold text-main mb-1")
            for clave, texto in conclusiones.items():
                if texto:
                    badge = "badge-success" if ("es INYECTIVA" in texto or "es SOBREYECTIVA" in texto or "BIYECTIVA" in texto) else "badge-warning"
                    with ui.row().classes(f"items-center gap-2 px-3 py-2 {badge} w-fit rounded"):
                        ui.label(texto).classes("text-sm font-bold")

        # ── Núcleo ker(T) ──────────────────────────────────────────────
        base_nucleo = r.get("base_nucleo", [])
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label(f"Núcleo  ker(T)  [dim = {nulidad}]").classes("font-bold text-main mb-2")
            if not base_nucleo:
                ui.html(
                    '<div class="math-scroll-container math-label text-lg text-center">'
                    r'$$ \ker(T) = \{\mathbf{0}\} $$</div>'
                )
            else:
                for vec_info in base_nucleo:
                    param = vec_info["parametro"]
                    vec = vec_info["vector"]
                    vec_tex = r"\begin{pmatrix} " + r" \\ ".join(html.escape(v) for v in vec) + r" \end{pmatrix}"
                    ui.html(
                        f'<div class="math-scroll-container math-label text-lg text-center">'
                        f'$$ \\mathbf{{v}}_{{{html.escape(param)}}} = {vec_tex} $$</div>'
                    )

        # ── Imagen Im(T) ───────────────────────────────────────────────
        base_imagen = r.get("base_imagen", [])
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label(f"Imagen  Im(T)  [dim = {rango}]").classes("font-bold text-main mb-2")
            ui.html(
                '<p class="text-xs text-sec mb-2">'
                "Base formada por las columnas pivote de A "
                "(convención columna estándar).</p>"
            )
            if not base_imagen:
                ui.label("Imagen = {0}").classes("text-sec italic")
            else:
                for vec_info in base_imagen:
                    idx = vec_info["indice_columna"]
                    vec = vec_info["vector"]
                    vec_tex = r"\begin{pmatrix} " + r" \\ ".join(html.escape(v) for v in vec) + r" \end{pmatrix}"
                    ui.html(
                        f'<div class="math-scroll-container math-label text-lg text-center">'
                        f"$$ \\mathbf{{a}}_{{{idx}}} = {vec_tex} $$</div>"
                    )

        # ── Pasos de reducción ─────────────────────────────────────────
        pasos = r.get("pasos_reduccion", [])
        if pasos:
            with ui.expansion("Ver reducción Gauss-Jordan de A", icon="visibility").classes(
                "w-full panel-card mt-4 timeline-expansion"
            ).props('header-class="font-bold text-main"'):
                for paso in pasos:
                    with ui.column().classes(
                        "w-full p-4 border-l-2 border-l-[var(--accent)] ml-2 mb-2 bg-[var(--bg-panel)] rounded-r-lg"
                    ):
                        ui.label(paso["descripcion"]).classes("text-sm font-semibold mb-1 text-sec")
                        ui.html(
                            f'<div class="math-scroll-container math-label text-lg">'
                            f'$$ {paso["matriz"]} $$</div>'
                        )

    def _reset_resultados(self):
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.icon("transform", size="4rem").classes("text-placeholder mb-4")
            ui.label("Listo para analizar").classes("text-xl font-bold text-main")
            ui.label("Ingresa la matriz A y presiona Analizar.").classes(
                "text-sm text-sec mt-2 text-center"
            )

    # ------------------------------------------------------------------
    # AI context stub
    # ------------------------------------------------------------------

    def get_ai_context(self):
        return None

    def get_ai_signals(self):
        return None
