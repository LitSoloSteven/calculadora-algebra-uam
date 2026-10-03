import html
from nicegui import ui

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
                    from_keyboard = (e.args == 0)
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
                    from_keyboard = (e.args == 0)
                    on_pick(item, from_keyboard)
                return handler
                
            btn.on('click', make_handler(f), args=['detail'])
            buttons.append(btn)
            
    return container, buttons
