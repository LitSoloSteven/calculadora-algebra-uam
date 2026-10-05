import html
import json
from nicegui import ui
from src.frontend import flags
from src.frontend.components.icons import icon_svg
from src.frontend.components.theme_switcher import render_theme_button
from src.frontend.navigation import (
    HUB_ROUTE,
    NAV_FLAT_ORDER,
    default_item_key,
    nav_item_href,
    nav_items,
    pillar_for_route,
    tool_by_id,
    tool_by_route,
)


def create_navbar(active_ui=None, active_route='/', active_key=None):
    """Genera la barra de navegacion contextual por pilares o plana segun flags."""
    if active_key is None:
        active_key = default_item_key(active_route)

    with ui.header().classes(
        'nav-header px-4 sm:px-8 py-2 sm:py-4 flex items-center justify-center w-full bg-transparent relative pointer-events-none'
    ).style('view-transition-name: navbar;').props('reveal'):
        with ui.link(target='/').classes(
            'brand-logo-link brand-corner-link pointer-events-auto absolute left-6 sm:left-10 top-1/2 -translate-y-1/2 flex items-center justify-center select-none no-underline z-10'
        ).props('aria-label="Scalaris - Inicio"').tooltip('Scalaris: Inicio'):
            ui.html('''
                <div class="brand-logo-container flex items-center justify-center" style="width: 72px; height: 72px;">
                    <img src="/assets/LogoOscuro.png" alt="Scalaris" class="brand-logo brand-logo-dark" style="height: 72px; width: 72px; object-fit: contain;" />
                    <img src="/assets/LogoClaro.png" alt="Scalaris" class="brand-logo brand-logo-light" style="height: 72px; width: 72px; object-fit: contain;" />
                </div>
            ''')

        with ui.element('div').classes('panel-card nav-pill pointer-events-auto'):
            if not flags.nav_v2():
                with ui.row().classes('items-center gap-4'):
                    for tool_id in NAV_FLAT_ORDER:
                        tool = tool_by_id(tool_id)
                        is_active = (active_route == tool.route)
                        aria_current = ' aria-current="page"' if is_active else ''
                        props_str = f'flat ripple=false href="{tool.route}" aria-label="{tool.name}"{aria_current}'
                        with ui.button(color=None).classes('btn-neo-icon p-0' + (' nav-active' if is_active else '')).props(props_str).tooltip(tool.name):
                            ui.html(icon_svg(tool.icon))

                    if not flags.dock_enabled():
                        def toggle_ai_panel():
                            if active_ui and hasattr(active_ui, 'ai_panel'):
                                active_ui.ai_panel.toggle()

                        with ui.button(on_click=toggle_ai_panel, color=None).classes('btn-neo-icon p-0 text-main').props('flat ripple=false aria-label="Glosa"').tooltip('Glosa'):
                            ui.html(icon_svg('tutor_ia'))

                    ui.element('div').classes('nav-sep')
                    render_theme_button()
            else:
                with ui.element('a').classes('nav-trigger nav-home').props(f'href="{HUB_ROUTE}" aria-label="Inicio"').tooltip('Inicio'):
                    ui.html(icon_svg('inicio'))

                pillar = pillar_for_route(active_route)
                if pillar is not None:
                    ui.element('div').classes('nav-sep')
                    with ui.element('span').classes('nav-pillar'):
                        ui.html(icon_svg(pillar.icon))
                        ui.html(html.escape(pillar.short_name), tag='span').classes('nav-pillar-name')

                    with ui.element('nav').classes('nav-items').props(f'aria-label="Herramientas de {pillar.short_name}"'):
                        for item in nav_items(pillar.id):
                            is_active = (item.key == active_key)
                            item_classes = 'nav-trigger nav-item' + (' nav-active' if is_active else '')
                            item_props = f'href="{nav_item_href(item)}" aria-label="{item.label}"'
                            if is_active:
                                item_props += ' aria-current="page"'
                            with ui.element('a').classes(item_classes).props(item_props).tooltip(item.label):
                                ui.html(icon_svg(item.icon))
                                ui.html(html.escape(item.label), tag='span').classes('nav-label-full')
                                ui.html(html.escape(item.short_label), tag='span').classes('nav-label-short')

                ui.element('div').classes('nav-sep')
                render_theme_button()

    if flags.nav_v2():
        active_tool = tool_by_route(active_route)
        if active_tool is not None:
            ui.add_body_html(
                '<script>try { window.scalarisRecordVisit && window.scalarisRecordVisit('
                + json.dumps(active_tool.id)
                + '); } catch (_) {}</script>'
            )
        ui.add_body_html('''
            <script>
            try {
                var el = document.querySelector('.nav-items .nav-active');
                if (el) el.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'auto' });
            } catch (_) {}
            </script>
        ''')