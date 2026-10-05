"""Vista principal del Hub de Scalaris: matriz aumentada [ I | b ]."""
from __future__ import annotations

import html
from nicegui import ui

from src.frontend.components.ai_panel import AIPanel
from src.frontend.components.app_shell import create_app_shell
from src.frontend.components.icons import icon_svg
from src.frontend.components.theme_switcher import render_theme_button
from src.frontend.navigation import HUB_ROUTE
from ._model import TileModel, format_item_count, hub_pillars, initial_selection


def _text_element(tag: str, text: str, classes: str, title: str | None = None) -> ui.html:
    """Crea un elemento semantico con texto escapado para prevenir inyecciones."""
    el = ui.html(html.escape(text), tag=tag, sanitize=False).classes(classes)
    if title:
        el.props(f'title="{html.escape(title)}"')
    return el


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
        ui.query('body').classes('hub-page')
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=HUB_ROUTE)

        pillars = hub_pillars()

        with ui.element('main').classes('hub-root view-root'):
            with ui.element('header').classes('hub-head'):
                with ui.element('div').classes('hub-brand'):
                    ui.html('''
                        <div class="brand-logo-container flex items-center justify-center" style="width: 40px; height: 40px;">
                            <img src="/assets/LogoOscuro.png" alt="" class="brand-logo brand-logo-dark" style="height: 40px; width: 40px; object-fit: contain;" />
                            <img src="/assets/LogoClaro.png" alt="" class="brand-logo brand-logo-light" style="height: 40px; width: 40px; object-fit: contain;" />
                        </div>
                    ''')
                    _text_element('h1', 'Scalaris', 'hub-title')
                _text_element('p', 'Álgebra lineal y utilidades numéricas, con cada paso a la vista.', 'hub-lead')
                with ui.element('div').classes('hub-theme'):
                    render_theme_button()

            with ui.element('div').classes('hub-stage'):
                with ui.element('div').classes('hub-carousel'):
                    with ui.element('div').classes('hub-viewport'):
                        with ui.element('div').classes('hub-track').props('id="hub-track" role="tablist" aria-orientation="horizontal" aria-label="Áreas de Scalaris"'):
                            for row_idx, pillar in enumerate(pillars):
                                is_first = (row_idx == 0)
                                card_cls = 'hub-card' + (' is-active' if is_first else '')
                                card_props = (
                                    f'role="tab" id="hub-tab-{pillar.id}" '
                                    f'aria-selected="{"true" if is_first else "false"}" '
                                    f'aria-controls="hub-panel-{pillar.id}" '
                                    f'aria-label="{html.escape(pillar.short_name)}" '
                                    f'tabindex="{"0" if is_first else "-1"}"'
                                )
                                with ui.element('button').classes(card_cls).props(card_props):
                                    with ui.element('div').classes('hub-card-body'):
                                        with ui.element('div').classes('hub-card-icon').props('aria-hidden="true"'):
                                            ui.html(icon_svg(pillar.icon))
                                        with ui.element('div').classes('hub-card-content'):
                                            _text_element('h2', pillar.short_name, 'hub-card-title', title=pillar.short_name)
                                            _text_element('p', pillar.blurb, 'hub-card-blurb', title=pillar.blurb)
                                            count_str = format_item_count(len(pillar.tiles), pillar.unit_singular, pillar.unit_plural)
                                            _text_element('span', count_str, 'hub-card-count')

                    with ui.element('div').classes('hub-carousel-nav'):
                        with ui.element('button').classes('hub-nav-btn hub-prev').props('type="button" aria-label="Área anterior" aria-controls="hub-track" aria-disabled="true"'):
                            ui.html('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 20px; height: 20px;"><polyline points="15 18 9 12 15 6"></polyline></svg>''')
                        next_props = 'type="button" aria-label="Área siguiente" aria-controls="hub-track"'
                        if len(pillars) <= 1:
                            next_props += ' aria-disabled="true" disabled'
                        with ui.element('button').classes('hub-nav-btn hub-next').props(next_props):
                            ui.html('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 20px; height: 20px;"><polyline points="9 18 15 12 9 6"></polyline></svg>''')

                with ui.element('div').classes('hub-panels hub-aug'):
                    for row_idx, pillar in enumerate(pillars):
                        is_first = (row_idx == 0)
                        panel_cls = 'hub-panel' + (' is-active' if is_first else '')
                        panel_props = f'role="tabpanel" id="hub-panel-{pillar.id}" aria-labelledby="hub-tab-{pillar.id}"'
                        if not is_first:
                            panel_props += ' inert'
                        with ui.element('section').classes(panel_cls).props(panel_props):
                            if len(pillar.tiles) == 0:
                                with ui.element('div').classes('hub-empty-area'):
                                    _text_element('p', 'Esta área aún no tiene herramientas.', 'hub-empty-msg')
                            else:
                                with ui.element('ul').classes('hub-tool-list'):
                                    for tile_model in pillar.tiles:
                                        with ui.element('li'):
                                            self._build_tile(tile_model)

        self.ai_panel.build()
        # En H3, el Hub no abre Glosa bajo ninguna circunstancia

        await self._apply_featured(client)
