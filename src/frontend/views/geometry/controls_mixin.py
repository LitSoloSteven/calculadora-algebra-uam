"""Mixin de controles de entrada para el Visualizador Geométrico."""
from __future__ import annotations

import json
import logging
from nicegui import ui

logger = logging.getLogger(__name__)


class GeometryControlsMixin:
    """Gestiona entradas, slider y debounce para el Visualizador."""

    def _build_controls(self, scene: str):
        """Build the input controls for the given scene."""
        if not self.controls_container:
            return

        self.controls_container.clear()

        with self.controls_container:
            if scene == 'rectas-planos':
                self._build_lines_controls()
            elif scene == 'vectores':
                self._build_vectors_controls()
            elif scene == 'combinacion':
                self._build_combination_controls()

    def _build_lines_controls(self):
        """Build EquationGrid for lines/planes."""
        from src.frontend.components.equation_grid import EquationGrid

        self.grid = EquationGrid(default_m=2, default_n=2)
        self.grid.inject_scripts()
        self.grid.on_data_change = self._on_data_change
        self.grid.build_grid_container()

    def _build_vectors_controls(self):
        """Build VectorCapturePanel for vectors scene (2 vectors)."""
        from src.frontend.components.vector_capture import VectorCapturePanel

        self.vec_panel = VectorCapturePanel(
            panel_id="geo_vec",
            min_vectors=2,
            max_vectors=2,
        )
        self.vec_panel.inject_scripts()
        self.vec_panel.build_container()

        # Hook data change
        self._hook_vector_panel(self.vec_panel)

    def _build_combination_controls(self):
        """Build VectorCapturePanel for combination scene."""
        from src.frontend.components.vector_capture import VectorCapturePanel

        self.comb_panel = VectorCapturePanel(
            panel_id="geo_comb",
            min_vectors=2,
            max_vectors=5,
            allow_orientation_toggle=False,
            first_vector_fixed_label="b",
        )
        self.comb_panel.inject_scripts()
        self.comb_panel.build_container()

        # Hook data change
        self._hook_vector_panel(self.comb_panel)

    def _hook_vector_panel(self, panel):
        """Attach on_data_change hook to a VectorCapturePanel (aditivo)."""
        if hasattr(panel, 'on_data_change') and panel.on_data_change is None:
            panel.on_data_change = self._on_data_change

    def _build_slider(self, result: dict, scene: str):
        """Build a ui.slider for vector frames (no server events)."""
        if not self.slider_container:
            return

        self.slider_container.clear()

        if scene != 'vectores':
            return

        frames = result.get("frames", [])
        if not frames:
            return

        default_idx = result.get("default_frame", 16)
        wrap_id = f"geo-fig-{id(self)}"

        with self.slider_container:
            with ui.row().classes('geo-slider-row w-full items-center gap-4 mt-2'):
                ui.label('k =').classes('font-bold text-sm text-main')
                self._slider_label = ui.label(
                    frames[default_idx].get("k_exact", "1")
                ).classes('font-bold text-sm text-main geo-slider-value')

                # Slider nativo (sin round-trips al servidor)
                ui.element('input').classes('flex-1 geo-slider-input').style('accent-color: var(--accent)').props(
                    f'type="range" min="0" max="{len(frames) - 1}" step="1" value="{default_idx}" '
                    f'data-geo-slider="{wrap_id}" aria-label="Valor del parámetro k" aria-valuetext="{frames[default_idx].get("k_exact", "1")}"'
                )
