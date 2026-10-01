"""Componente para la captura e interacción con matrices cuadradas (SquareMatrixPanel).

Optimizado para redimensionado incremental sin regenerar la cuadrícula completa,
con soporte para animación fluida de hasta 50×50 elementos.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from nicegui import ui

from src.backend.constants import INVERSE_MAX_DIMENSION

logger = logging.getLogger(__name__)

MATRIX_ID = "A"
MIN_N = 1
MAX_N = INVERSE_MAX_DIMENSION
DEFAULT_N = 3
CELL_PX = 64


class SquareMatrixPanel:
    """Panel de captura de matriz cuadrada con un único control bidimensional (n×n)."""

    def __init__(self, initial_n: int = DEFAULT_N):
        self.n: int = min(max(initial_n, MIN_N), MAX_N)
        self.cache: dict[tuple[int, int], str] = {}
        self.rows_ui: list[ui.row] = []
        self.cells: list[list[ui.input]] = []

        self.on_data_change: Callable[[], None] | None = None
        self._suspend_events: bool = False
        self._pending: int = 0
        self._resizing: bool = False

        self.container: ui.column | None = None
        self.grid_container: ui.column | None = None
        self.lbl_n: ui.label | None = None
        self.lbl_badge: ui.html | None = None
        self.btn_dec: ui.button | None = None
        self.btn_inc: ui.button | None = None

    @staticmethod
    def inject_scripts():
        """Inyecta los scripts necesarios para navegación y animación de matriz cuadrada."""
        ui.add_head_html('<script src="/assets/js/matrix_capture.js"></script>')
        ui.add_head_html('<script src="/assets/js/square_matrix.js"></script>')

    def build_container(self) -> ui.column:
        """Construye el contenedor UI completo del panel."""
        self.container = ui.column().classes("w-full panel-card p-4")
        with self.container:
            # Fila superior de controles
            with ui.row().classes("w-full justify-between items-center mb-4 flex-wrap gap-2"):
                # Izquierda: Badge de matriz A
                with ui.row().classes("items-center gap-2"):
                    ui.label("Matriz A").classes("text-lg font-bold text-main")
                    self.lbl_badge = ui.html(
                        f'A <span style="color: var(--accent)">·</span> {self.n} &times; {self.n}'
                    ).classes("fs-small text-sec uppercase").style(
                        "letter-spacing: 0.08em; font-variant-numeric: tabular-nums; margin-bottom: -2px;"
                    )

                # Derecha: Control de tamaño y botón Pegar
                with ui.row().classes("items-center gap-3 flex-wrap"):
                    with ui.row().classes("items-center gap-1"):
                        ui.label("Tamaño:").classes("text-sm text-sec mr-1")
                        self.btn_dec = (
                            ui.button(icon="remove", color=None, on_click=lambda: self.resize(-1))
                            .props("ripple=false")
                            .classes("btn-neo-icon w-8 h-8 p-0")
                            .tooltip("Quitar fila y columna")
                        )
                        self.lbl_n = ui.label(str(self.n)).classes(
                            "font-bold w-6 text-center text-main"
                        )
                        self.btn_inc = (
                            ui.button(icon="add", color=None, on_click=lambda: self.resize(+1))
                            .props("ripple=false")
                            .classes("btn-neo-icon w-8 h-8 p-0")
                            .tooltip("Añadir fila y columna")
                        )

                    ui.button(
                        "Pegar",
                        icon="content_paste",
                        color=None,
                        on_click=self.paste_from_clipboard,
                    ).props("ripple=false").classes("btn-ghost").tooltip(
                        "Pegar matriz desde el portapapeles"
                    )

            # Cuadrícula con scroll propio
            with ui.column().classes("overflow-auto w-full").style("max-height: 60vh;"):
                self.grid_container = ui.column().style("min-width: max-content;")
                self._render_full()

            # Texto de ayuda
            ui.label(
                "Tab/flechas para moverte · Pegá desde Excel con Ctrl+V · Máx. 50×50"
            ).classes("fs-small text-sec mt-2")

        self._update_controls()
        return self.container

    def _make_cell(self, i: int, j: int) -> ui.input:
        """Crea un input individual para la celda (i, j)."""
        def handler(e):
            val = e.value.strip() if e.value is not None else ""
            if val == "":
                self.cache.pop((i, j), None)
            else:
                self.cache[(i, j)] = val
            if not self._suspend_events and self.on_data_change:
                self.on_data_change()

        val = self.cache.get((i, j), "")
        cell = (
            ui.input(value=val, placeholder="", on_change=handler)
            .classes("matrix-input")
            .style(f"width: {CELL_PX}px; min-width: {CELL_PX}px; flex-shrink: 0;")
            .props(
                f'data-matrix-id="{MATRIX_ID}" data-matrix-row="{i}" data-matrix-col="{j}" '
                f'borderless autocomplete="new-password" name="{MATRIX_ID}_r{i}c{j}"'
            )
        )
        return cell

    def _render_full(self):
        """Renderiza la cuadrícula completa de ceros / caché (solo para inicio o set_data)."""
        if self.grid_container is None:
            return
        self.grid_container.clear()
        self.rows_ui.clear()
        self.cells.clear()

        with self.grid_container:
            for i in range(self.n):
                with ui.row().classes("items-center gap-2 mb-2 no-wrap").props(
                    f'data-grid-row="{MATRIX_ID}_{i}"'
                ) as row_ui:
                    row_cells = []
                    for j in range(self.n):
                        cell = self._make_cell(i, j)
                        row_cells.append(cell)
                    self.rows_ui.append(row_ui)
                    self.cells.append(row_cells)

    async def resize(self, delta: int):
        """Maneja el cambio de tamaño acumulando deltas para clicks rápidos."""
        self._pending += delta
        if self._resizing:
            return
        self._resizing = True
        try:
            while self._pending != 0:
                paso = 1 if self._pending > 0 else -1
                if not (MIN_N <= self.n + paso <= MAX_N):
                    self._pending = 0
                    break
                self._pending -= paso
                await self._apply_step(paso)
        finally:
            self._resizing = False
            self._update_controls()

    async def _apply_step(self, delta: int):
        """Aplica un cambio atómico de dimensión ±1 con animación."""
        if delta == -1:
            try:
                await ui.run_javascript(
                    f"return window.animateSquareResize('{MATRIX_ID}', {self.n - 1}, 'remove');",
                    timeout=5.0,
                )
            except Exception:
                pass

            # 1. Quitar última columna de cada fila 0..n-2
            for i in range(self.n - 1):
                last_cell = self.cells[i].pop()
                last_cell.delete()

            # 2. Quitar última fila completa
            last_row = self.rows_ui.pop()
            last_row.delete()
            self.cells.pop()

            self.n -= 1
            # Purgar caché de celdas eliminadas
            self.cache = {
                (r, c): v for (r, c), v in self.cache.items()
                if r < self.n and c < self.n
            }

        elif delta == 1:
            # 1. Agregar nueva celda a cada fila existente
            for i in range(self.n):
                with self.rows_ui[i]:
                    new_cell = self._make_cell(i, self.n)
                    self.cells[i].append(new_cell)

            # 2. Agregar nueva fila con n+1 celdas
            if self.grid_container is not None:
                with self.grid_container:
                    with ui.row().classes("items-center gap-2 mb-2 no-wrap").props(
                        f'data-grid-row="{MATRIX_ID}_{self.n}"'
                    ) as new_row_ui:
                        new_row_cells = []
                        for j in range(self.n + 1):
                            cell = self._make_cell(self.n, j)
                            new_row_cells.append(cell)
                        self.rows_ui.append(new_row_ui)
                        self.cells.append(new_row_cells)

            self.n += 1
            await asyncio.sleep(0.05)
            try:
                await ui.run_javascript(
                    f"return window.animateSquareResize('{MATRIX_ID}', {self.n - 1}, 'add');",
                    timeout=5.0,
                )
            except Exception:
                pass

        self._update_controls()
        if not self._suspend_events and self.on_data_change:
            self.on_data_change()

    def _update_controls(self):
        """Actualiza etiquetas y estados de botones según la dimensión actual."""
        if self.lbl_n:
            self.lbl_n.set_text(str(self.n))
        if self.lbl_badge:
            self.lbl_badge.content = (
                f'{MATRIX_ID} <span style="color: var(--accent)">·</span> {self.n} &times; {self.n}'
            )
        if self.btn_dec:
            if self.n <= MIN_N:
                self.btn_dec.disable()
                self.btn_dec.tooltip("Mínimo 1×1")
            else:
                self.btn_dec.enable()
                self.btn_dec.tooltip("Quitar fila y columna")
        if self.btn_inc:
            if self.n >= MAX_N:
                self.btn_inc.disable()
                self.btn_inc.tooltip(f"Máximo {MAX_N}×{MAX_N}")
            else:
                self.btn_inc.enable()
                self.btn_inc.tooltip("Añadir fila y columna")

    def get_matrix_data(self) -> list[list[str]]:
        """Devuelve la matriz de datos como lista de listas de strings. Celdas vacías pasan a '0'."""
        res = []
        for i in range(self.n):
            row = []
            for j in range(self.n):
                val = self.cache.get((i, j), "").strip()
                row.append(val if val != "" else "0")
            res.append(row)
        return res

    def is_strictly_empty(self) -> bool:
        """Devuelve True si no hay ninguna celda con texto escrito."""
        return len(self.cache) == 0

    def is_empty(self) -> bool:
        """Devuelve True si todas las celdas están vacías o contienen '0'."""
        return all(v.strip() in ("", "0") for v in self.cache.values())

    def clear(self):
        """Limpia todas las celdas y vacía el caché."""
        self.cache.clear()
        self._suspend_events = True
        try:
            for row in self.cells:
                for cell in row:
                    cell.set_value("")
        finally:
            self._suspend_events = False
        if self.on_data_change:
            self.on_data_change()

    def set_data(self, data: list[list[Any]]):
        """Asigna datos a la matriz, validando que sea cuadrada y no supere MAX_N."""
        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("Los datos deben ser una lista no vacía.")
        new_n = len(data)
        if new_n > MAX_N or any(not isinstance(r, list) or len(r) != new_n for r in data):
            raise ValueError(f"Los datos deben formar una matriz cuadrada de máximo {MAX_N}×{MAX_N}.")

        self.n = new_n
        self.cache.clear()
        for i in range(new_n):
            for j in range(new_n):
                val = str(data[i][j]).strip()
                if val:
                    self.cache[(i, j)] = val

        self._render_full()
        self._update_controls()
        if not self._suspend_events and self.on_data_change:
            self.on_data_change()

    def flash_cell(self, r: int, c: int):
        """Aplica la animación de error (shake) y enfoque a la celda (r, c)."""
        ui.run_javascript(f"window.shakeMatrixCell('{MATRIX_ID}', {r}, {c});")

    async def paste_from_clipboard(self):
        """Pega una matriz desde el portapapeles y la carga si es cuadrada y válida."""
        try:
            raw_text = await ui.run_javascript("return navigator.clipboard.readText();", timeout=15.0)
        except Exception:
            ui.notify("Error al acceder al portapapeles: permiso denegado.", type="warning")
            return

        if not raw_text or not raw_text.strip():
            ui.notify("El portapapeles está vacío o no contiene texto.", type="warning")
            return

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not lines:
            ui.notify("No se encontraron líneas de datos válidas.", type="warning")
            return

        matrix_rows = []
        for line in lines:
            if "\t" in line:
                cells = [c.strip() for c in line.split("\t")]
            elif ";" in line:
                cells = [c.strip() for c in line.split(";")]
            elif "," in line:
                cells = [c.strip() for c in line.split(",")]
            else:
                cells = [c.strip() for c in line.split()]
            matrix_rows.append(cells)

        rows_count = len(matrix_rows)
        if any(len(r) != rows_count for r in matrix_rows):
            ui.notify("La matriz pegada no es cuadrada.", type="warning")
            return

        if rows_count > MAX_N:
            ui.notify(
                f"La matriz pegada ({rows_count}×{rows_count}) supera el límite de {MAX_N}×{MAX_N}.",
                type="warning",
            )
            return

        try:
            self.set_data(matrix_rows)
            ui.notify(f"Matriz {rows_count}×{rows_count} pegada correctamente.", type="positive")
        except Exception as e:
            ui.notify(f"Error al cargar la matriz: {e}", type="negative")
