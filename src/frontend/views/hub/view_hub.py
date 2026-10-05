import html
from nicegui import ui
from src.frontend.components.app_shell import create_app_shell
from src.frontend.components.ai_panel import AIPanel
from src.frontend.components.icons import icon_svg
from src.frontend.navigation import HUB_ROUTE, nav_groups
from ._layout import board_classes, step_class
from ._recent import pick_featured


def _text_element(tag: str, text: str, classes: str) -> ui.html:
    return ui.html(html.escape(text), tag=tag, sanitize=False).classes(classes)


class HubUI:
    def __init__(self, glosa_open: bool = False):
        self.glosa_open = glosa_open
        self.ai_panel = None
        self.tiles = {}
        self.marks = {}

    def _build_tile(self, tool):
        with ui.link(target=tool.route).classes('hub-tile').props(f'data-tool="{tool.id}"') as tile:
            with ui.element('span').classes('hub-tile-icon').props('aria-hidden="true"'):
                ui.html(icon_svg(tool.icon))
            _text_element('span', tool.name, 'hub-tile-name')
            _text_element('span', tool.descriptor, 'hub-tile-desc')
            mark = ui.label('').classes('hub-tile-mark')

        self.tiles[tool.id] = tile
        self.marks[tool.id] = mark
        return tile

    async def _apply_featured(self, client):
        """Marca el tile del punto focal sin mover el layout (sin transicion)."""
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
        tool, has_history = pick_featured(ids)
        tile = self.tiles.get(tool.id)
        mark = self.marks.get(tool.id)
        if tile is None or mark is None:
            return
        tile.classes(add='is-featured')
        mark.set_text('Sigue aquí' if has_history else 'Empieza aquí')

    async def build(self, client):
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=HUB_ROUTE)

        with ui.element('div').classes('w-full max-w-7xl mx-auto p-6 mt-4 hub-root view-root'):
            with ui.element('header').classes('hub-head'):
                _text_element('h1', 'Scalaris', 'hub-title')
                _text_element('p', 'Álgebra lineal y utilidades numéricas, con cada paso a la vista.', 'hub-lead')

            with ui.element('nav').classes(board_classes()).props('aria-label="Herramientas de Scalaris"'):
                for index, (pillar, tools) in enumerate(nav_groups()):
                    with ui.element('section').classes(step_class(index)):
                        _text_element('h2', pillar.short_name, 'hub-step-title')
                        with ui.element('ul').classes('hub-step-list'):
                            for tool in tools:
                                with ui.element('li'):
                                    self._build_tile(tool)

        self.ai_panel.build()
        if self.glosa_open:
            self.ai_panel.open()

        await self._apply_featured(client)
