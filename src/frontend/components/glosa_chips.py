import html
from nicegui import ui

def _is_keyboard_event(e) -> bool:
    args = getattr(e, 'args', e)
    if isinstance(args, dict):
        return args.get('detail') == 0
    if isinstance(args, (int, float)):
        return args == 0
    if isinstance(args, (list, tuple)) and len(args) > 0:
        first = args[0]
        if isinstance(first, dict):
            return first.get('detail') == 0
        return first == 0
    return False

def render_chip_row(suggestions, on_pick, *, variant='dock', disabled=False):
    cls_container = 'glosa-chips'
    if variant == 'inline':
        cls_container += ' glosa-chips-inline'
        
    container = ui.element('div').classes(cls_container).props('role="group" aria-label="Preguntas sugeridas"')
    
    if disabled:
        container.props('aria-disabled="true"')
        container.style('opacity: 0.6; pointer-events: none;')
        
    buttons = []
    with container:
        for s in suggestions:
            btn_cls = 'glosa-chip'
            if variant == 'inline':
                btn_cls += ' glosa-chip-inline'
                
            btn = ui.element('button').classes(btn_cls).props('type="button"')
            with btn:
                # Usar ui.html para inyectar el texto directamente sin contenedores extras
                ui.html(f'<span style="pointer-events: none;">{html.escape(s.text)}</span>')
                
            if disabled:
                btn.props('disabled aria-disabled="true"')
                
            def make_handler(item):
                def handler(e):
                    from_keyboard = _is_keyboard_event(e)
                    on_pick(item, from_keyboard)
                return handler
                
            btn.on('click', make_handler(s), args=['detail'])
            buttons.append(btn)
            
    return container, buttons

def render_followups(followups, on_pick, *, disabled=False):
    container = ui.element('div').classes('glosa-followups w-full mt-2').props('role="group" aria-label="Seguimientos" aria-live="off"')
    
    if disabled:
        container.props('aria-disabled="true"')
        container.style('opacity: 0.6; pointer-events: none;')
        
    buttons = []
    with container:
        for f in followups:
            btn = ui.element('button').classes('glosa-followup').props('type="button"')
            with btn:
                ui.html(f'<span style="pointer-events: none;">{html.escape(f.label)}</span>')
                
            if disabled:
                btn.props('disabled aria-disabled="true"')
                
            def make_handler(item):
                def handler(e):
                    from_keyboard = _is_keyboard_event(e)
                    on_pick(item, from_keyboard)
                return handler
                
            btn.on('click', make_handler(f), args=['detail'])
            buttons.append(btn)
            
    return container, buttons

def render_explain_button(step_index: int, total_steps: int, op: str, on_click, *, is_loading=False) -> ui.button | None:
    """Renderiza el botón 'Explicar paso' para un paso específico."""
    from src.frontend import flags
    from src.frontend.suggestions import glosa_configured
    from src.frontend.components.icons import icon_svg

    if not flags.dock_enabled():
        return None

    configured = glosa_configured()
    with ui.button(color=None).classes('glosa-explain-btn').props(
        f'aria-label="Explicar paso {step_index}" round flat ripple=false'
    ) as btn:
        ui.html(icon_svg('explicar_paso'))

    btn.tooltip("Explicar este paso" if configured else "Glosa no está configurada")

    if is_loading:
        btn.props('disabled')
        btn.classes('is-loading')
        return btn
    if not configured:
        btn.props('disabled')
        return btn

    def handler(e):
        from_keyboard = _is_keyboard_event(e)
        if from_keyboard:
            ui.run_javascript("document.documentElement.setAttribute('data-glosa-instant', 'true'); setTimeout(() => document.documentElement.removeAttribute('data-glosa-instant'), 100);")
        on_click(step_index)

    btn.on('click', handler, args=['detail'])
    return btn

def render_focus_chip(text: str, on_remove) -> ui.element:
    """Renderiza el chip de foco en el dock."""
    chip = ui.element('div').classes('glosa-explain-focus').props(f'title="{html.escape(text)}"')
    with chip:
        ui.icon('center_focus_strong').classes('glosa-explain-focus-icon')
        ui.label(text).classes('glosa-explain-focus-text')
        ui.button(icon='close', color=None, on_click=on_remove).classes('glosa-explain-focus-close').props('round flat size=xs ripple=false').tooltip("Quitar foco")
    return chip
