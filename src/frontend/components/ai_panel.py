import json
import html
import logging
from nicegui import ui, app, run
from src.ai.openrouter_ai import OpenRouterIA
from src.frontend import flags
from src.frontend.components.glosa_dock import GlosaDockMixin
from src.ai.context import serialize_context, AIContext
from src.ai.prompts import trim_history
import time
import threading

logger = logging.getLogger(__name__)

class AIPanel(GlosaDockMixin):
    @property
    def _storage(self):
        try:
            # Check if app.storage.user is available (requires storage_secret)
            app.storage.user.get('__test_storage__')
            return app.storage.user
        except Exception as e:
            if not hasattr(self, '_storage_warned'):
                logger.warning(f"No se pudo usar app.storage.user (¿falta STORAGE_SECRET?): {e}. Fallback a app.storage.client.")
                self._storage_warned = True
            return app.storage.client

    @property
    def is_open(self):
        """Devuelve True si el panel legacy está abierto. En dock, la verdad vive en html[data-glosa]."""
        return self._storage.get('ai_panel_open', False)

    @is_open.setter
    def is_open(self, value):
        self._storage['ai_panel_open'] = value

    @property
    def chat_history(self):
        if 'ai_chat_history' not in self._storage:
            self._storage['ai_chat_history'] = []
        return self._storage['ai_chat_history']

    @chat_history.setter
    def chat_history(self, value):
        self._storage['ai_chat_history'] = value

    def __init__(self, active_ui):
        self.active_ui = active_ui
        self.motor_ia = OpenRouterIA()
        self.panel_container = None
        self.overlay = None
        self.chat_area = None
        self.input_field = None
        self.context_chip = None
        self.attached_context = ""
        
        storage = self._storage
        if 'ai_chat_history' not in storage:
            storage['ai_chat_history'] = []
        else:
            # Migrar historial antiguo: eliminar api_text y saludos viejos
            hist = storage['ai_chat_history']
            if hist and hist[0].get('text', '').startswith('¡Hola! Estoy aquí'):
                hist = hist[1:]
            for msg in hist:
                msg.pop('api_text', None)
            storage['ai_chat_history'] = hist
                
        if 'ai_panel_open' not in storage:
            storage['ai_panel_open'] = False
            
        if 'ai_ctx_enabled' not in storage:
            storage['ai_ctx_enabled'] = True
            
        self._last_send_time = 0.0
        self._ctx_version = 0

    def toggle(self):
        if flags.dock_enabled():
            ui.run_javascript('if(window.scalarisGlosa) window.scalarisGlosa.toggle();')
            return
        self.is_open = not self.is_open
        self._update_visibility()
        
    def open(self):
        if flags.dock_enabled():
            ui.run_javascript('if(window.scalarisGlosa) window.scalarisGlosa.open();')
            return
        if not self.is_open:
            self.toggle()

    def _update_visibility(self):
        if not self.panel_container: return
        if self.is_open:
            self.panel_container.style('transform: translateX(0); opacity: 1; visibility: visible; pointer-events: auto;')
            self.overlay.style('opacity: 1; pointer-events: auto;')
        else:
            self.panel_container.style('transform: translateX(calc(100% + 32px)); opacity: 0; visibility: hidden; pointer-events: none;')
            self.overlay.style('opacity: 0; pointer-events: none;')
            
    def notify_context_changed(self):
        if not flags.dock_enabled():
            return
        self._ctx_version += 1

    def _collect_context(self) -> str:
        if not self._storage.get('ai_ctx_enabled', True):
            return ""
        if not hasattr(self.active_ui, 'get_ai_context'):
            return ""
        try:
            ctx_obj = self.active_ui.get_ai_context()
            if ctx_obj is None or getattr(ctx_obj, 'empty', False):
                return ""
            return serialize_context(ctx_obj)
        except Exception as e:
            logger.exception("Error al recopilar el contexto para la IA")
            ui.notify('No pudimos leer tu ejercicio; enviamos solo tu pregunta.', type='warning')
            return ""

    def attach_context(self):
        # Legacy
        ctx_text = self._collect_context()
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
        self.chat_history = []
        if flags.dock_enabled():
            self.render_chat_dock()
        else:
            self.render_chat()

    def render_chat(self):
        if not self.chat_area: return
        self.chat_area.clear()
        
        with self.chat_area:
            for i, msg in enumerate(self.chat_history):
                self._render_message(msg, idx=i)
                
        ui.run_javascript("setTimeout(() => { const el = document.getElementById('ai-chat-area'); if(el) el.scrollTop = el.scrollHeight; }, 100);")

    def _render_typing_indicator(self):
        ui.html('<div style="display:flex; gap:2px; font-weight:bold; font-size:1.2em;"><span style="animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.32s;">.</span><span style="animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.16s;">.</span><span style="animation: bounce 1.4s infinite ease-in-out both;">.</span></div>')

    def _render_message(self, msg, idx=None):
        text = msg.get('text', '')
        sent = msg.get('sent', False)
        align = 'justify-end' if sent else 'justify-start'
        bg = 'var(--btn-primary-bg)' if sent else 'var(--bg-panel)'
        color = 'var(--btn-primary-text)' if sent else 'var(--text-main)'
        radius = '16px 16px 4px 16px' if sent else '16px 16px 16px 4px'
        
        with ui.row().classes(f'w-full {align} mb-4'):
            container = ui.column().classes('p-3').style(f'background: {bg}; color: {color}; border-radius: {radius}; box-shadow: var(--elev-1); max-width: 85%;')
            with container:
                msg_id = f"ai-msg-{id(text)}-{idx}" if not sent and msg.get('animate') else None
                if msg_id:
                    msg['animate'] = False
                    ui.html(f'<div id="{msg_id}"></div>').classes('whitespace-pre-wrap math-label')
                    ui.timer(0.05, lambda t=text, mid=msg_id: ui.run_javascript(f'typewriterEffect("{mid}", {json.dumps(t)}, 15)'), once=True)
                else:
                    ui.html(html.escape(text).replace('\n', '<br>')).classes('whitespace-pre-wrap math-label')

    async def send_message(self):
        text = self.input_field.value
        if not text or not text.strip(): return
        
        now = time.monotonic()
        if now - self._last_send_time < 1.5:
            ui.notify('Espera un momento antes de enviar otra pregunta.', type='warning')
            return
        
        if getattr(self, '_is_sending', False): return
        
        full_text = text.strip()
        
        ctx_block = self.attached_context
        if not ctx_block:
            ctx_block = self._collect_context()
        self.clear_context()
            
        self.input_field.value = ''
        
        self.chat_history.append({"text": full_text, "sent": True})
        self.render_chat()
        
        await self._do_send_legacy(full_text, ctx_block)
        
    async def _do_send_legacy(self, full_text, ctx_block):
        self._is_sending = True
        self._last_send_time = time.monotonic()
        
        with self.chat_area:
            typing_row = ui.row().classes('w-full justify-start mb-4')
            with typing_row:
                with ui.column().classes('p-3').style('background: var(--bg-panel); color: var(--text-sec); border-radius: 16px 16px 16px 4px; box-shadow: var(--elev-1); max-width: 85%;'):
                    self._render_typing_indicator()
                
        ui.run_javascript("setTimeout(() => { const el = document.getElementById('ai-chat-area'); if(el) el.scrollTop = el.scrollHeight; }, 50);")
        
        cancel_event = threading.Event()
        self._request_counter = getattr(self, '_request_counter', 0) + 1
        current_req = self._request_counter
        cancel_btn_row = None
        
        async def show_cancel():
            await asyncio.sleep(5)
            if self._request_counter == current_req and getattr(self, '_is_sending', False):
                with self.chat_area:
                    nonlocal cancel_btn_row
                    cancel_btn_row = ui.row().classes('w-full justify-center mt-2')
                    with cancel_btn_row:
                        ui.button('Cancelar', on_click=lambda: cancel_req(current_req)).classes('btn-ghost text-xs text-sec')
                ui.run_javascript("setTimeout(() => { const el = document.getElementById('ai-chat-area'); if(el) el.scrollTop = el.scrollHeight; }, 50);")
                        
        def cancel_req(req_id):
            if self._request_counter == req_id:
                cancel_event.set()
                
        ui.timer(0, show_cancel, once=True)
            
        try:
            from src.ai.openrouter_ai import AIErrorKind
            result = await run.io_bound(self.motor_ia.ask, full_text, history=trim_history(self.chat_history), context_block=ctx_block, cancel=cancel_event)
        except Exception as e:
            from src.ai.openrouter_ai import AIResult
            result = AIResult(False, f"Error al procesar tu mensaje: {e}")
            
        if self._request_counter == current_req:
            try:
                typing_row.delete()
            except Exception: pass
            try:
                if cancel_btn_row: cancel_btn_row.delete()
            except Exception: pass
            
            self._is_sending = False
            
            if result.kind == "CANCELLED":
                return
                
            msg = {"text": result.text, "sent": False, "error": not result.ok, "animate": True}
            if not result.ok:
                msg["retry"] = result.kind not in ("NO_KEY", "AUTH")
                
            self.chat_history.append(msg)
            self.render_chat()

    def build(self):
        if flags.dock_enabled():
            self.build_dock()
            return
            
        self.overlay = ui.element('div').style('position: fixed; inset: 0; background: rgba(0,0,0,0.5); backdrop-filter: blur(2px); -webkit-backdrop-filter: blur(2px); z-index: 2999; transition: opacity 240ms var(--ease-std); pointer-events: none;')
        self.overlay.on('click', self.toggle)
        
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
