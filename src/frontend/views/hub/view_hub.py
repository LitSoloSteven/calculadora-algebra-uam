"""Vista principal del Hub de Scalaris: matriz aumentada [ I | b ]."""
from __future__ import annotations

import html
from nicegui import ui

from src.frontend.components.ai_panel import AIPanel
from src.frontend.components.app_shell import create_app_shell
from src.frontend.components.icons import icon_svg
from src.frontend.components.theme_switcher import render_theme_button
from src.frontend.navigation import HUB_ROUTE
from ._model import TileModel, hub_pillars, initial_selection, matrix_cells


def _text_element(tag: str, text: str, classes: str) -> ui.html:
    """Crea un elemento semantico con texto escapado para prevenir inyecciones."""
    return ui.html(html.escape(text), tag=tag, sanitize=False).classes(classes)


class HubUI:
    """Controlador de vista del Hub de inicio."""

    def __init__(self, glosa_open: bool = False):
        self.glosa_open = glosa_open
        self.ai_panel = None
        self.tiles: dict[str, ui.element] = {}
        self.marks: dict[str, ui.html] = {}

    def _build_tile(self, tile_model: TileModel):
        """Construye un tile de herramienta o escena como enlace accesible."""
        with ui.element('a').classes('hub-tile').props(f'href="{tile_model.href}" data-key="{tile_model.key}"') as tile:
            with ui.element('span').classes('hub-tile-icon').props('aria-hidden="true"'):
                ui.html(icon_svg(tile_model.icon))
            _text_element('span', tile_model.name, 'hub-tile-name')
            _text_element('span', tile_model.desc, 'hub-tile-desc')
            mark = _text_element('span', '', 'hub-tile-mark')

        self.tiles[tile_model.key] = tile
        self.marks[tile_model.key] = mark
        return tile

    async def _apply_featured(self, client):
        """Marca el tile del punto focal y preselecciona su pilar sin saltos de layout."""
        ids = None
        try:
            await client.connected()
            res = await client.run_javascript(
                "return window.scalarisReadRecent ? window.scalarisReadRecent() : {ok: false, ids: []};",
                timeout=3.0,
            )
            if isinstance(res, dict) and res.get('ok'):
                ids = res.get('ids')
        except Exception:
            ids = None

        if getattr(client, 'is_deleted', False):
            return

        sel = initial_selection(ids)
        tile = self.tiles.get(sel.tile_key)
        mark = self.marks.get(sel.tile_key)
        if tile is not None and mark is not None:
            tile.classes(add='is-featured')
            mark_text = 'Sigue aquí' if sel.has_history else 'Empieza aquí'
            if hasattr(mark, 'set_content'):
                mark.set_content(html.escape(mark_text))
            elif hasattr(mark, 'set_text'):
                mark.set_text(mark_text)

        try:
            await client.run_javascript(
                f"window.scalarisHubSelect && window.scalarisHubSelect('{sel.pillar_id}', {{instant: true}});",
                timeout=1.0,
            )
        except Exception:
            pass

    async def build(self, client):
        """Construye el arbol de componentes del Hub y activa Glosa si corresponde."""
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=HUB_ROUTE)

        pillars = hub_pillars()
        cells = matrix_cells(len(pillars))

        with ui.element('main').classes('w-full max-w-7xl mx-auto p-6 mt-4 hub-root view-root'):
            with ui.element('header').classes('hub-head'):
                with ui.element('div').classes('hub-brand'):
                    ui.html('''
                        <div class="brand-logo-container flex items-center justify-center" style="width: 48px; height: 48px;">
                            <img src="/assets/LogoOscuro.png" alt="" class="brand-logo brand-logo-dark" style="height: 48px; width: 48px; object-fit: contain;" />
                            <img src="/assets/LogoClaro.png" alt="" class="brand-logo brand-logo-light" style="height: 48px; width: 48px; object-fit: contain;" />
                        </div>
                    ''')
                    _text_element('h1', 'Scalaris', 'hub-title')
                _text_element('p', 'Álgebra lineal y utilidades numéricas, con cada paso a la vista.', 'hub-lead')
                with ui.element('div').classes('hub-theme'):
                    render_theme_button()

            with ui.element('div').classes('hub-stage'):
                with ui.element('div').classes('hub-matrix').props('role="tablist" aria-orientation="vertical" aria-label="Áreas de Scalaris"'):
                    for row_idx, pillar in enumerate(pillars):
                        is_first = (row_idx == 0)
                        tab_cls = 'hub-row' + (' is-active' if is_first else '')
                        tab_props = (
                            f'role="tab" id="hub-tab-{pillar.id}" '
                            f'aria-selected="{"true" if is_first else "false"}" '
                            f'aria-controls="hub-panel-{pillar.id}" '
                            f'aria-label="{html.escape(pillar.short_name)}" '
                            f'tabindex="{"0" if is_first else "-1"}"'
                        )
                        with ui.element('button').classes(tab_cls).props(tab_props):
                            with ui.element('span').classes('hub-cells').props('aria-hidden="true"'):
                                for col_idx, val in enumerate(cells[row_idx]):
                                    cell_cls = 'hub-cell' + (' is-pivot' if val == '1' else '')
                                    _text_element('span', val, cell_cls)
                            _text_element('span', pillar.short_name, 'hub-row-name')

                ui.element('div').classes('hub-bar').props('aria-hidden="true"')

                with ui.element('div').classes('hub-aug'):
                    for row_idx, pillar in enumerate(pillars):
                        is_first = (row_idx == 0)
                        panel_cls = 'hub-panel' + (' is-active' if is_first else '')
                        panel_props = f'role="tabpanel" id="hub-panel-{pillar.id}" aria-labelledby="hub-tab-{pillar.id}"'
                        if not is_first:
                            panel_props += ' inert'
                        with ui.element('section').classes(panel_cls).props(panel_props):
                            with ui.element('ul').classes('hub-tool-list'):
                                for tile_model in pillar.tiles:
                                    with ui.element('li'):
                                        self._build_tile(tile_model)

        self.ai_panel.build()
        if self.glosa_open:
            self.ai_panel.open()

        await self._apply_featured(client)
