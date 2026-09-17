import json
from nicegui import ui, app, run
from src.ai.openrouter_ai import OpenRouterIA


class AIPanel:
    @property
    def is_open(self):
        return app.storage.client.get('ai_panel_open', False)

    @is_open.setter
    def is_open(self, value):
        app.storage.client['ai_panel_open'] = value

    @property
    def chat_history(self):
        return app.storage.client.get('ai_chat_history', [])

    @chat_history.setter
    def chat_history(self, value):
        app.storage.client['ai_chat_history'] = value

    def __init__(self, active_ui):
        self.active_ui = active_ui
        self.motor_ia = OpenRouterIA()
        self.panel_container = None
        self.overlay = None
        self.chat_area = None
        self.input_field = None
        self.context_chip = None
        self.attached_context = ""
        
        if 'ai_chat_history' not in app.storage.client:
            app.storage.client['ai_chat_history'] = [{"text": "¡Hola! Estoy aquí para ayudarte con álgebra lineal: vectores, matrices, sistemas lineales y más.", "sent": False}]
        if 'ai_panel_open' not in app.storage.client:
            app.storage.client['ai_panel_open'] = False

    def toggle(self):
        self.is_open = not self.is_open
        self._update_visibility()

    def _update_visibility(self):
        if not self.panel_container: return
        if self.is_open:
            self.panel_container.style('transform: translateX(0); opacity: 1;')
            self.overlay.style('opacity: 1; pointer-events: auto;')
        else:
            self.panel_container.style('transform: translateX(calc(100% + 32px)); opacity: 0;')
            self.overlay.style('opacity: 0; pointer-events: none;')
            
    def attach_context(self):
        ctx_text = ""
        if hasattr(self.active_ui, 'grid') and hasattr(self.active_ui, 'mode_tabs'):
            # LinearSystemsUI
            if self.active_ui.mode_tabs.value == 'Ecuaciones':
                lineas = [inp.value for inp in self.active_ui.ecuaciones_inputs if inp.value]
                if lineas:
                    ctx_text = "Sistema de ecuaciones:\n" + "\n".join(lineas)
            else:
                eqs = self.active_ui.grid.export_to_equations()
                if eqs:
                    ctx_text = "Sistema (desde matriz):\n" + "\n".join(eqs)
        elif hasattr(self.active_ui, 'capture_panel'):
            # MatrixOpsUI
            try:
                mats = self.active_ui.capture_panel.get_matrices_dict()
                if mats:
                    ctx_text = "Matrices disponibles:\n"
                    for k, v in mats.items():
                        ctx_text += f"Matriz {k} ({v['rows']}x{v['cols']}): {v['data']}\n"
            except Exception:
                pass
                
        if ctx_text:
            self.attached_context = ctx_text
            self.context_chip.set_visibility(True)
            ui.notify('Contexto adjuntado', type='positive')
        else:
            ui.notify('No hay datos válidos para adjuntar en la vista actual.', type='warning')

    def clear_context(self):
        self.attached_context = ""
        self.context_chip.set_visibility(False)

    def clear_chat(self):
        self.chat_history = [{"text": "¡Hola! Estoy aquí para ayudarte con álgebra lineal: vectores, matrices, sistemas lineales y más.", "sent": False}]
        self.render_chat()

    def render_chat(self):
        if not self.chat_area: return
        self.chat_area.clear()
        
        with self.chat_area:
            for i, msg in enumerate(self.chat_history):
                self._render_message(msg['text'], msg['sent'], idx=i)
                
        ui.run_javascript("setTimeout(() => { const el = document.getElementById('ai-chat-area'); if(el) el.scrollTop = el.scrollHeight; }, 100);")

    def _render_typing_indicator(self):
        ui.html('<div style="display:flex; gap:2px; font-weight:bold; font-size:1.2em;"><span style="animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.32s;">.</span><span style="animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.16s;">.</span><span style="animation: bounce 1.4s infinite ease-in-out both;">.</span></div>')

    def _render_message(self, text, sent, idx=None, is_typing=False):
        align = 'justify-end' if sent else 'justify-start'
        bg = 'var(--btn-primary-bg)' if sent else 'var(--bg-panel)'
        color = 'var(--btn-primary-text)' if sent else 'var(--text-main)'
        radius = '16px 16px 4px 16px' if sent else '16px 16px 16px 4px'
        
        with ui.row().classes(f'w-full {align} mb-4'):
            container = ui.column().classes('p-3').style(f'background: {bg}; color: {color}; border-radius: {radius}; box-shadow: var(--elev-1); max-width: 85%;')
            with container:
                if is_typing:
                    self._render_typing_indicator()
                else:
                    msg_id = f"ai-msg-{id(text)}-{idx}" if not sent and idx == len(self.chat_history) - 1 else None
                    if msg_id:
                        ui.html(f'<div id="{msg_id}"></div>').classes('whitespace-pre-wrap math-label')
                        ui.timer(0.05, lambda t=text, mid=msg_id: ui.run_javascript(f'typewriterEffect("{mid}", {json.dumps(t)}, 15)'), once=True)
                    else:
                        ui.html(text.replace('\n', '<br>')).classes('whitespace-pre-wrap math-label')

    async def send_message(self):
        text = self.input_field.value
        if not text or not text.strip(): return
        
        full_text = text.strip()
        if self.attached_context:
            full_text = f"[Contexto adjunto]\n{self.attached_context}\n\nPregunta: {full_text}"
            self.clear_context()
            
        self.input_field.value = ''
        
        self.chat_history.append({"text": text.strip(), "sent": True})
        self.render_chat()
        
        with self.chat_area:
            typing_row = ui.row().classes('w-full justify-start mb-4')
            with typing_row:
                with ui.column().classes('p-3').style('background: var(--bg-panel); color: var(--text-sec); border-radius: 16px 16px 16px 4px; box-shadow: var(--elev-1); max-width: 85%;'):
                    self._render_typing_indicator()
                
        ui.run_javascript("setTimeout(() => { const el = document.getElementById('ai-chat-area'); if(el) el.scrollTop = el.scrollHeight; }, 50);")
        
        try:
            respuesta = await run.io_bound(self.motor_ia.analizar_sistema, full_text)
        except Exception as e:
            respuesta = f"Error al procesar tu mensaje: {str(e)}"
            
        typing_row.delete()
        self.chat_history.append({"text": respuesta, "sent": False})
        self.render_chat()

    def build(self):
        self.overlay = ui.element('div').style('position: fixed; inset: 0; background: rgba(0,0,0,0.5); backdrop-filter: blur(2px); -webkit-backdrop-filter: blur(2px); z-index: 2999; transition: opacity 240ms var(--ease-std); pointer-events: none;')
        self.overlay.on('click', self.toggle)
        
        ui.add_head_html('''
            <style>
                @keyframes bounce {
                  0%, 80%, 100% { transform: translateY(0); }
                  40% { transform: translateY(-5px); }
                }
                .ai-input-wrapper .q-field__control { height: auto !important; min-height: 48px; }
                
                @media (max-width: 639px) {
                    .ai-panel-card {
                        inset: 8px !important;
                        width: auto !important;
                        height: auto !important;
                    }
                }
            </style>
        ''')
        
        self.panel_container = ui.column().classes('no-wrap ai-panel-card').style('''
            position: fixed; right: 16px; top: 88px; width: min(420px, calc(100vw - 32px)); height: calc(100vh - 104px);
            background: var(--bg-elevated); z-index: 3000;
            border: 1px solid var(--border-input); border-radius: var(--radius-card);
            box-shadow: var(--elev-3); overflow: hidden;
            transition: transform 240ms var(--ease-std), opacity 240ms var(--ease-std);
        ''')
        
        with self.panel_container:
            with ui.row().classes('w-full items-center justify-between p-4 border-b border-[var(--border-input)]'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('smart_toy', size='sm').classes('text-accent')
                    ui.label('Tutor IA').classes('font-bold text-lg text-main')
                    
                with ui.row().classes('gap-2'):
                    ui.button(icon='attach_file', on_click=self.attach_context, color=None).classes('btn-neo-icon w-8 h-8 p-0 text-sec').props('ripple=false').tooltip('Adjuntar sistema actual')
                    ui.button(icon='delete_sweep', on_click=self.clear_chat, color=None).classes('btn-neo-icon w-8 h-8 p-0 text-sec').props('ripple=false').tooltip('Limpiar conversación')
                    ui.button(icon='close', on_click=self.toggle, color=None).classes('btn-neo-icon w-8 h-8 p-0').props('ripple=false')
                    
            self.chat_area = ui.column().classes('w-full flex-1 p-4 overflow-y-auto gap-2').props('id="ai-chat-area"')
            self.render_chat()
            
            with ui.column().classes('w-full p-4 border-t border-[var(--border-input)] bg-[var(--bg-elevated)]'):
                self.context_chip = ui.chip('Sistema adjunto', icon='data_object', color=None).props('removable').on('remove', self.clear_context).classes('mb-2 badge-success')
                self.context_chip.set_visibility(False)
                if self.attached_context:
                    self.context_chip.set_visibility(True)
                
                with ui.row().classes('w-full items-end gap-2 ai-input-wrapper'):
                    self.input_field = ui.textarea(placeholder='Preguntá algo...').classes('flex-1 matrix-input text-sm').props('borderless autogrow').style('max-height: 120px; overflow-y: auto;')
                    self.input_field.on('keydown.enter.prevent.exact', self.send_message)
                    
                    ui.button(icon='send', on_click=self.send_message, color=None).classes('btn-primary w-10 h-10 p-0 mb-1').props('ripple=false').style('border-radius: 12px;')
                    
        self._update_visibility()
