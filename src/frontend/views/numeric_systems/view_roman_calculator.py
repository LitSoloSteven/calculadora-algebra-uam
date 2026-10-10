"""Vista principal de la Calculadora de Números Romanos en Scalaris."""

from __future__ import annotations

import logging
import re
from typing import Any

from nicegui import ui

from src.ai.context import AIContext, fingerprint, is_stale, sanitize_user_string
from src.backend.solvers.numeric_systems.roman_calculator import (
    RomanCalculator,
    RomanNumeralError,
)
from src.frontend.components.ai_panel import AIPanel
from src.frontend.components.app_shell import create_app_shell
from src.frontend.navigation import route_of
from .roman_result_mixin import RomanResultMixin

logger = logging.getLogger(__name__)

ROMAN_REGEX = r"^(M{0,3})(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$"


class RomanCalculatorUI(RomanResultMixin):
    """Controlador de vista modular para operaciones con números romanos."""

    def __init__(self) -> None:
        self.ai_panel = None
        self.last_result = None
        self.last_error = None
        self._result_fp = None
        self.reproductor = None
        self.chips_container = None
        self.resultado_container = None
        self.input_a = None
        self.input_b = None
        self.tabs_op = None
        self.lbl_signo = None
        self.lbl_error = None

    def build(self) -> None:
        """Construye la interfaz de usuario de la calculadora romana."""
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=route_of("romanos"))

        with ui.column().classes("w-full max-w-4xl mx-auto items-center q-pa-md mt-6 view-root"):
            with ui.column().classes("w-full panel-card p-6 gap-6"):
                ui.label("Números romanos").classes("text-2xl font-bold text-main")

                with ui.row().classes("w-full items-center gap-3"):
                    with ui.tabs().classes("neo-tabs method-tabs tabs-wide w-full") as self.tabs_op:
                        ui.tab("suma", label="Suma")
                        ui.tab("resta", label="Resta")
                        ui.tab("mult", label="Mult")

                self._build_quick_examples()
                self._build_input_fields()

                self.chips_container = ui.column().classes("w-full mt-2")
                ui.button(
                    "CALCULAR", on_click=self.operar_romanos, color=None
                ).classes("btn-primary w-full py-3 text-lg mt-2 font-bold")

            self.resultado_container = ui.column().classes("w-full gap-6 mt-6")

        self.tabs_op.on_value_change(self.actualizar_signo)
        self.tabs_op.set_value("suma")
        self.input_a.on_value_change(lambda _: self._notify_change())
        self.input_b.on_value_change(lambda _: self._notify_change())
        self.input_a.on("keydown.enter", self.operar_romanos)
        self.input_b.on("keydown.enter", self.operar_romanos)
        self.ai_panel.build()

    def _build_quick_examples(self) -> None:
        """Construye los botones de ejemplos rápidos preconfigurados."""
        with ui.row().classes("w-full items-center gap-3 flex-wrap"):
            with ui.row().classes("items-center gap-1.5 text-sec"):
                ui.icon("bolt", size="xs").style("color: var(--accent);")
                ui.label("Ejemplos rápidos:").classes("text-xs font-semibold tracking-wider uppercase")

            with ui.row().classes("gap-2.5 flex-wrap"):
                self.chip_ejemplo("XIV + IX", "XIV", "IX", "suma")
                self.chip_ejemplo("XX − VIII", "XX", "VIII", "resta")
                self.chip_ejemplo("III × IV", "III", "IV", "mult")

    def _build_input_fields(self) -> None:
        """Construye los inputs de operandos y la etiqueta de operación."""
        with ui.column().classes("w-full gap-1"):
            with ui.row().classes("w-full items-center gap-3 flex-nowrap"):
                self.input_a = ui.input(placeholder="Operando A (ej: XIV)").classes(
                    "flex-1 matrix-input conversor-input text-center"
                ).style("font-size: 1.5rem !important; padding: 18px 20px; text-transform: uppercase; min-width: 0;")
                self.input_a.props('autocomplete="off" spellcheck="false"')

                self.lbl_signo = ui.label("+").classes("text-2xl font-bold text-sec flex-shrink-0")

                self.input_b = ui.input(placeholder="Operando B (ej: IX)").classes(
                    "flex-1 matrix-input conversor-input text-center"
                ).style("font-size: 1.5rem !important; padding: 18px 20px; text-transform: uppercase; min-width: 0;")
                self.input_b.props('autocomplete="off" spellcheck="false"')

            self.lbl_error = ui.label("").classes("fs-small").style(
                "color: var(--error); margin-left: 8px; min-height: 20px;"
            )

    def chip_ejemplo(self, label_txt: str, a_val: str, b_val: str, op_val: str):
        """Crea un botón estilizado de ejemplo rápido."""
        return ui.button(
            label_txt, on_click=lambda: self.cargar_ejemplo(a_val, b_val, op_val), color=None
        ).classes(
            "px-3.5 py-1.5 rounded-lg border text-main font-mono text-xs font-bold tracking-wide transition-all duration-200 cursor-pointer"
        ).style(
            "background: var(--bg-panel); border-color: var(--border-input); box-shadow: var(--elev-2);"
        ).props("no-caps flat ripple=false")

    def cargar_ejemplo(self, a_val: str, b_val: str, op_val: str) -> None:
        """Carga los operandos y la operación del ejemplo seleccionado."""
        self.input_a.value = a_val
        self.input_b.value = b_val
        self.tabs_op.set_value(op_val)
        self.lbl_error.text = ""

    def actualizar_signo(self, e) -> None:
        """Actualiza el glifo del operador visual."""
        signos = {"suma": "+", "resta": "−", "mult": "×"}
        self.lbl_signo.text = signos.get(e.value, "+")
        self.lbl_error.text = ""
        self._notify_change()

    def copiar(self, texto: str) -> None:
        """Copia el texto al portapapeles y notifica al usuario."""
        ui.clipboard.write(texto)
        ui.notify(f"Copiado: {texto}", type="positive", position="top")

    def _notify_change(self) -> None:
        """Notifica al panel de Glosa para recalcular contexto."""
        p = getattr(self, "ai_panel", None)
        if p and hasattr(p, "schedule_context_refresh"):
            p.schedule_context_refresh()

    def operar_romanos(self) -> None:
        """Ejecuta la operación aritmética romana y monta el resultado y los pasos."""
        self.lbl_error.text = ""
        self.resultado_container.clear()

        val_a = (self.input_a.value or "").strip().upper()
        val_b = (self.input_b.value or "").strip().upper()
        op = getattr(self.tabs_op, "value", "suma") or "suma"

        if not val_a or not val_b:
            self.lbl_error.text = "Ingresa ambos operandos en números romanos."
            return

        try:
            res, simbolo_op, nombre_op = self._ejecutar_solver(op, val_a, val_b)
            self.last_result = res
            self.last_error = None
            self._render_success_view(res, val_a, val_b, simbolo_op, nombre_op, op)
        except RomanNumeralError as err:
            self._handle_error(err, str(err))
        except Exception:
            logger.exception("Error inesperado en calculadora de números romanos")
            self._handle_error(None, "Ocurrió un error inesperado al procesar la operación. Inténtalo de nuevo.")
        finally:
            self._finalizar_calculo(val_a, val_b, op)

    def _ejecutar_solver(self, op: str, val_a: str, val_b: str) -> tuple[Any, str, str]:
        """Invoca el método correspondiente de RomanCalculator."""
        if op == "suma":
            return RomanCalculator.sumar(val_a, val_b), "+", "Suma"
        if op == "resta":
            return RomanCalculator.restar(val_a, val_b), "−", "Resta"
        return RomanCalculator.multiplicar_un_digito(val_a, val_b), "×", "Multiplicación"

    def _render_success_view(self, res: Any, val_a: str, val_b: str, simbolo: str, nombre: str, op: str) -> None:
        """Pinta la tarjeta destacada y monta el reproductor interactivo."""
        if getattr(self, "ai_panel", None) and getattr(self, "chips_container", None):
            self.chips_container.clear()
            with self.chips_container:
                self.ai_panel.render_inline_chips()

        with self.resultado_container:
            self._render_hero_result_card(val_a, val_b, simbolo, nombre, res.resultado_romano)
            self._render_roman_player(res, op)

    def _handle_error(self, err: Exception | None, mensaje: str) -> None:
        """Maneja las excepciones registrando estado y actualizando chips."""
        self.last_result = None
        self.last_error = err
        self.lbl_error.text = mensaje
        if getattr(self, "ai_panel", None) and getattr(self, "chips_container", None):
            self.chips_container.clear()
            with self.chips_container:
                self.ai_panel.render_inline_chips()

    def _finalizar_calculo(self, val_a: str, val_b: str, op: str) -> None:
        """Actualiza el fingerprint y el contexto de IA."""
        entrada = {"a": val_a, "b": val_b, "operacion": op}
        self._result_fp = fingerprint(entrada)
        self._notify_change()

    @staticmethod
    def classify_roman_error(exc: Exception) -> str | None:
        """Clasifica una excepción de números romanos en un código de sugerencia."""
        by_code = {
            "ZERO_NOT_REPRESENTABLE": "err_sub_zero",
            "NEGATIVE_NOT_REPRESENTABLE": "err_sub_neg",
            "INVALID_SYNTAX": "err_syntax",
            "NOT_CANONICAL": "err_syntax",
            "EMPTY_INPUT": "err_syntax",
        }
        code = getattr(exc, "code", None)
        if code in by_code:
            return by_code[code]
        msg = str(exc).lower()
        if "no existe el número cero" in msg:
            return "err_sub_zero"
        if "no existen los números negativos" in msg:
            return "err_sub_neg"
        if "sintaxis válida" in msg or "canónica" in msg:
            return "err_syntax"
        return None

    def get_ai_context(self) -> AIContext:
        """Construye el contexto de IA para el panel de Glosa."""
        val_a = self.input_a.value if self.input_a else ""
        val_b = self.input_b.value if self.input_b else ""
        op_val = getattr(self.tabs_op, "value", "suma") if self.tabs_op else "suma"
        if not val_a and not val_b:
            return AIContext("romanos", "Números romanos", "Calculadora Romana", {}, empty=True)

        ctx = AIContext(
            "romanos", "Números romanos", f"Operación: {op_val}",
            {
                "operando_a": sanitize_user_string(val_a, 32) if val_a else "",
                "operando_b": sanitize_user_string(val_b, 32) if val_b else "",
                "operacion": op_val,
            },
        )
        entrada_actual = {"a": (val_a or "").strip().upper(), "b": (val_b or "").strip().upper(), "operacion": op_val}
        ctx.stale = is_stale(entrada_actual, getattr(self, "_result_fp", None))

        if getattr(self, "last_result", None):
            ctx.result = None if ctx.stale else {
                "status": "SUCCESS",
                "resultado_romano": self.last_result.resultado_romano,
                "resultado_decimal": self.last_result.resultado_decimal,
            }
        elif self.lbl_error and self.lbl_error.text:
            ctx.result = None if ctx.stale else {
                "status": "ERROR",
                "message": self.lbl_error.text,
            }
        return ctx

    def get_ai_signals(self) -> Any:
        """Determina las señales y estados para las sugerencias de Glosa."""
        from src.frontend.suggestions import InvalidCell, Signals
        try:
            state, flags, invalid = "none", set(), None
            v_a = (self.input_a.value or "").strip().upper() if self.input_a else ""
            v_b = (self.input_b.value or "").strip().upper() if self.input_b else ""

            if v_a and not re.match(ROMAN_REGEX, v_a):
                invalid = InvalidCell(label="Operando A")
            elif v_b and not re.match(ROMAN_REGEX, v_b):
                invalid = InvalidCell(label="Operando B")

            if not getattr(self.get_ai_context(), "stale", False):
                if getattr(self, "last_result", None):
                    state = "ok"
                elif getattr(self, "last_error", None):
                    state = "error"
                    err_flag = self.classify_roman_error(self.last_error)
                    if err_flag:
                        flags.add(err_flag)

            if getattr(self.tabs_op, "value", None) == "mult":
                flags.add("op_mult")

            return Signals(tool="romanos", state=state, flags=frozenset(flags), invalid=invalid)
        except Exception:
            return None