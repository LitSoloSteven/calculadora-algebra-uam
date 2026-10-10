"""Vista principal del Hub de Scalaris: matriz de áreas con popovers por pilar."""
from __future__ import annotations

import html
from nicegui import ui

from src.frontend.components.ai_panel import AIPanel
from src.frontend.components.app_shell import create_app_shell
from src.frontend.components.icons import icon_svg
from src.frontend.navigation import HUB_ROUTE
from ._model import TileModel, format_item_count, hub_pillars, initial_selection


def _text_element(tag: str, text: str, classes: str, title: str | None = None) -> ui.html:
    """Crea un elemento semántico con texto escapado para prevenir inyecciones."""
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
        self.rows: dict[str, ui.element] = {}
        self.row_marks: dict[str, ui.html] = {}

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
        """Marca el tile reciente y su fila, o Sistemas de ecuaciones como inicio."""
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
        row = self.rows.get(sel.pillar_id)
        row_mark = self.row_marks.get(sel.pillar_id)
        mark_text = 'Sigue aquí' if sel.has_history else 'Empieza aquí'

        if tile is not None:
            tile.classes(add='is-featured')
        if mark is not None:
            mark.set_content(html.escape(mark_text))
        if row is not None:
            row.classes(add='is-featured')
        if row_mark is not None:
            row_mark.set_content(html.escape(mark_text))

    async def build(self, client):
        """Construye la matriz, los diálogos nativos y activa Glosa si corresponde."""
        ui.query('body').classes('hub-page')
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=HUB_ROUTE)

        pillars = hub_pillars()

        with ui.element('main').classes('hub-root view-root'):
            with ui.element('header').classes('hub-head'):
                with ui.element('div').classes('hub-brand'):
                    ui.html('''
                        <div class="brand-logo-container flex items-center justify-center" style="width: 56px; height: 56px;">
                            <img src="/assets/LogoOscuro.png" alt="" class="brand-logo brand-logo-dark" style="height: 56px; width: 56px; object-fit: contain;" />
                            <img src="/assets/LogoClaro.png" alt="" class="brand-logo brand-logo-light" style="height: 56px; width: 56px; object-fit: contain;" />
                        </div>
                    ''')
                    _text_element('h1', 'Scalaris', 'hub-title')
                _text_element('p', 'Álgebra lineal y utilidades numéricas, con cada paso a la vista.', 'hub-lead')
            with ui.element('div').classes('hub-matrix').props(
                'role="group" aria-label="Áreas de Scalaris"'
            ):
                row_index = 0
                for pillar in pillars:
                    row_props = (
                        f'type="button" id="hub-row-{pillar.id}" '
                        f'aria-haspopup="dialog" aria-expanded="false" '
                        f'aria-controls="hub-pop-{pillar.id}"'
                    )
                    with ui.element('button').classes('hub-row').props(
                        f'{row_props} style="--i:{row_index}"'
                    ) as row:
                        with ui.element('span').classes('hub-row-body'):
                            with ui.element('span').classes('hub-spot-layer').props('aria-hidden="true"'):
                                ui.element('span').classes('hub-spot')
                            with ui.element('span').classes('hub-cell hub-cell-icon').props('aria-hidden="true"'):
                                ui.html(icon_svg(pillar.icon))
                            with ui.element('span').classes('hub-cell hub-cell-name'):
                                _text_element(
                                    'span',
                                    pillar.short_name,
                                    'hub-row-title',
                                    title=pillar.short_name,
                                )
                                _text_element(
                                    'span',
                                    pillar.blurb,
                                    'hub-row-blurb',
                                    title=pillar.blurb,
                                )
                            with ui.element('span').classes('hub-cell hub-cell-meta'):
                                count_str = format_item_count(
                                    len(pillar.tiles),
                                    pillar.unit_singular,
                                    pillar.unit_plural,
                                )
                                _text_element('span', count_str, 'hub-row-count')
                                row_mark = _text_element('span', '', 'hub-row-mark')
                                with ui.element('span').classes('hub-row-chevron').props('aria-hidden="true"'):
                                    ui.html(icon_svg('abrir'))
                    self.rows[pillar.id] = row
                    self.row_marks[pillar.id] = row_mark
                    row_index += 1

            for pillar in pillars:
                dialog_props = (
                    f'id="hub-pop-{pillar.id}" '
                    f'aria-labelledby="hub-pop-title-{pillar.id}"'
                )
                with ui.element('dialog').classes('hub-pop').props(dialog_props):
                    with ui.element('div').classes('hub-pop-card'):
                        with ui.element('header').classes('hub-pop-head'):
                            with ui.element('span').classes('hub-pop-icon').props('aria-hidden="true"'):
                                ui.html(icon_svg(pillar.icon))
                            title = _text_element(
                                'h2',
                                pillar.short_name,
                                'hub-pop-title',
                                title=pillar.short_name,
                            )
                            title.props(f'id="hub-pop-title-{pillar.id}"')
                            count_str = format_item_count(
                                len(pillar.tiles),
                                pillar.unit_singular,
                                pillar.unit_plural,
                            )
                            _text_element('span', count_str, 'hub-pop-count')
                            with ui.element('button').classes('hub-pop-close').props(
                                'type="button" aria-label="Cerrar"'
                            ):
                                with ui.element('span').classes('hub-pop-close-icon').props('aria-hidden="true"'):
                                    ui.html(icon_svg('cerrar'))

                        if len(pillar.tiles) == 0:
                            with ui.element('div').classes('hub-empty-area'):
                                _text_element(
                                    'p',
                                    'Esta área aún no tiene herramientas.',
                                    'hub-empty-msg',
                                )
                        else:
                            with ui.element('ul').classes('hub-tool-list'):
                                tile_index = 0
                                for tile_model in pillar.tiles:
                                    with ui.element('li').props(
                                        f'style="--i:{min(tile_index, 3)}"'
                                    ):
                                        self._build_tile(tile_model)
                                    tile_index += 1

        self.ai_panel.build()
        # El Hub mantiene Glosa cerrada al entrar.

        await self._apply_featured(client)
