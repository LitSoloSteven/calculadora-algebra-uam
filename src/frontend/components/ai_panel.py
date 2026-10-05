import logging
from nicegui import ui, app
from src.ai.openrouter_ai import OpenRouterIA
from src.frontend import flags
from src.frontend.components.glosa_dock import GlosaDockMixin, MAX_HISTORY
from src.ai.context import serialize_context

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
        try:
            self._client = ui.context.client
        except Exception:
            self._client = None

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
            if len(hist) > MAX_HISTORY:
                hist = hist[-MAX_HISTORY:]
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
            
    def schedule_context_refresh(self):
        if not flags.dock_enabled():
            return
            
        task = getattr(self, '_refresh_task', None)
        if task and not task.done():
            task.cancel()
            
        async def _debounced():
            try:
                await asyncio.sleep(0.25)
                if hasattr(self, 'chat_area') and getattr(self.chat_area, 'is_deleted', False):
                    return
                if hasattr(self, 'panel_container') and getattr(self.panel_container, 'is_deleted', False):
                    return
                self.notify_context_changed()
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.debug(f"Context refresh cancelado o abortado: {e}")
                
        try:
            self._refresh_task = self._spawn(_debounced())
        except RuntimeError:
            pass

    def _collect_context(self) -> str:
        if not self._storage.get('ai_ctx_enabled', True):
            return ""
        if not hasattr(self.active_ui, 'get_ai_context'):
            return ""
        try:
            ctx_obj = self.active_ui.get_ai_context()
            if ctx_obj is None or getattr(ctx_obj, 'empty', False):
                return ""
                
            foc = getattr(self, 'explain_focus', None)
            if foc:
                from src.ai.context import StepRef
                import dataclasses
                # Si context_obj.focus ya existe, podríamos reemplazar, pero aquí lo asignamos
                new_focus = StepRef(
                    index=foc['index'],
                    total=foc['total'],
                    kind=foc['kind'],
                    op=foc['op'],
                    rows_before=foc.get('rows_before', {}),
                    rows_after=foc.get('rows_after', {}),
                    cols=tuple(foc['cols']) if foc.get('cols') else None,
                    detail=foc.get('detail')
                )
                if hasattr(ctx_obj, 'focus') and ctx_obj.focus:
                    ctx_obj.focus = new_focus
                else:
                    ctx_obj.focus = new_focus

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
        await self._submit(text)
        
    def render_inline_chips(self, limit=2):
        from src.frontend.suggestions import chips_active, suggest
        if not chips_active() or not hasattr(self.active_ui, 'get_ai_signals'):
            return
            
        try:
            signals = self.active_ui.get_ai_signals()
        except Exception as e:
            logger.error(f"Error en get_ai_signals inline: {e}")
            signals = None
            
        if not signals:
            return
            
        enabled = self._storage.get('ai_ctx_enabled', True)
        suggs = suggest(signals, limit=limit, include_specific=enabled)
        if not suggs:
            return
            
        from src.frontend.components.glosa_chips import render_chip_row
        is_sending = getattr(self, '_is_sending', False)
        render_chip_row(suggs, self.ask_suggestion, variant='inline', disabled=is_sending)

    def build(self):
        if self._client is None:
            try:
                self._client = ui.context.client
            except Exception:
                pass

        if flags.dock_enabled():
            self.build_dock()
            return
            
        self.overlay = ui.element('div').style('position: fixed; inset: 0; background: var(--scrim); z-index: calc(var(--z-dock) - 1); transition: opacity 240ms var(--ease-std); pointer-events: none;')
        self.overlay.on('click', self.toggle)
        
        self.panel_container = ui.column().classes('no-wrap ai-panel-card').style('''
            position: fixed; right: 16px; top: 88px; width: min(420px, calc(100vw - 32px)); height: 100dvh;
            background: var(--bg-elevated); z-index: var(--z-dock);
            border: 1px solid var(--border-input); border-radius: var(--radius-card);
            box-shadow: var(--elev-3); overflow: hidden;
            transition: transform 240ms var(--ease-std), opacity 240ms var(--ease-std);
        ''')
        
        with self.panel_container:
            with ui.row().classes('w-full items-center justify-between p-4 border-b border-[var(--border-input)]'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('smart_toy', size='sm').classes('text-accent')
                    ui.label('Glosa').classes('font-bold text-lg text-main')
                    
                with ui.row().classes('gap-2'):
                    ui.button(icon='attach_file', on_click=self.attach_context, color=None).classes('btn-neo-icon w-8 h-8 p-0 text-sec').props('ripple=false aria-label="Adjuntar sistema actual"').tooltip('Adjuntar sistema actual')
                    ui.button(icon='delete_sweep', on_click=self.clear_chat, color=None).classes('btn-neo-icon w-8 h-8 p-0 text-sec').props('ripple=false aria-label="Limpiar conversación"').tooltip('Limpiar conversación')
                    ui.button(icon='close', on_click=self.toggle, color=None).classes('btn-neo-icon w-8 h-8 p-0').props('ripple=false aria-label="Cerrar Glosa"').tooltip('Cerrar')
                    
            self.chat_area = ui.column().classes('w-full flex-1 p-4 overflow-y-auto gap-2').props('id="ai-chat-area"')
            self.render_chat()
            
            with ui.column().classes('w-full p-4 border-t border-[var(--border-input)] bg-[var(--bg-elevated)]'):
                self.context_chip = ui.chip('Sistema adjunto', icon='data_object', color=None).props('removable').on('remove', self.clear_context).classes('mb-2 badge-success')
                self.context_chip.set_visibility(False)
                if self.attached_context:
                    self.context_chip.set_visibility(True)
                
                with ui.row().classes('w-full items-end gap-2 ai-input-wrapper'):
                    self.input_field = ui.textarea(placeholder='Pregunta algo...').classes('flex-1 matrix-input text-sm').props('borderless autogrow').style('max-height: 120px; overflow-y: auto;')
                    self.input_field.on('keydown.enter.prevent.exact', self.send_message)
                    
                    ui.button(icon='send', on_click=self.send_message, color=None).classes('btn-primary w-10 h-10 p-0 mb-1').props('ripple=false aria-label="Enviar mensaje"').tooltip('Enviar').style('border-radius: 12px;')
                    
        self._update_visibility()
