import logging
import asyncio
from nicegui import ui, run
from src.frontend.components.icons import icon_svg
from src.frontend.components.glosa_render import render_glosa_text

logger = logging.getLogger(__name__)

class GlosaDockMixin:
    def open(self):
        ui.run_javascript('if(window.scalarisGlosa) window.scalarisGlosa.open();')

    def build_dock(self):
        with ui.element('aside').classes('glosa-dock flex flex-col no-wrap').props('id="glosa-dock" role="complementary" aria-label="Glosa, asistente de álgebra lineal" data-glosa-keep'):
            
            # Header
            with ui.row().classes('w-full items-center justify-between p-4 border-b border-[var(--border-input)] flex-shrink-0'):
                with ui.row().classes('items-center gap-3 min-w-0 flex-1'):
                    ui.html(icon_svg('glosa')).classes('text-accent flex-shrink-0')
                    with ui.column().classes('gap-0 min-w-0 w-full'):
                        ui.label('Glosa').classes('font-bold text-lg text-main truncate w-full').tooltip('Glosa')
                        ui.label('Notas al margen de cada paso').classes('text-sec fs-small truncate w-full').tooltip('Notas al margen de cada paso')
                        
                with ui.row().classes('gap-2 flex-shrink-0 ml-2'):
                    ui.button(icon='attach_file', on_click=self.attach_context, color=None).classes('btn-neo-icon w-8 h-8 p-0 text-sec').props('ripple=false aria-label="Adjuntar sistema actual"').tooltip('Adjuntar sistema actual')
                    ui.button(icon='delete_sweep', on_click=self.clear_chat, color=None).classes('btn-neo-icon w-8 h-8 p-0 text-sec').props('ripple=false aria-label="Limpiar conversación"').tooltip('Limpiar conversación')
                    ui.button(icon='close', color=None).classes('btn-neo-icon w-8 h-8 p-0').props('ripple=false data-glosa-close aria-label="Cerrar Glosa"').tooltip('Cerrar')

            # Log
            self.chat_area = ui.column().classes('w-full flex-1 p-4 overflow-y-auto gap-4').style('min-height: 0; overscroll-behavior: contain;').props('id="glosa-log" role="log" aria-live="polite"')
            self.render_chat_dock()

            # Footer
            with ui.column().classes('w-full p-4 border-t border-[var(--border-input)] bg-[var(--bg-elevated)] flex-shrink-0'):
                self.context_chip = ui.chip('Sistema adjunto', icon='data_object', color=None).props('removable').on('remove', self.clear_context).classes('mb-2 badge-success')
                self.context_chip.set_visibility(bool(getattr(self, 'attached_context', '')))
                
                with ui.row().classes('w-full items-end gap-2 no-wrap'):
                    self.input_field = ui.textarea(placeholder='Pregunta algo sobre tu ejercicio...').classes('flex-1 glosa-input').props('borderless autogrow').style('max-height: 120px; min-width: 0;')
                    self.input_field.on('keydown.enter.prevent.exact', self.send_message_dock)
                    
                    ui.button(icon='send', on_click=self.send_message_dock, color=None).classes('btn-primary w-10 h-10 p-0 mb-1 flex-shrink-0').props('ripple=false').style('border-radius: 12px;').tooltip('Enviar')
                    
        # FAB
        ui.button(on_click=self.open, color=None).classes('glosa-fab').props('ripple=false data-glosa-toggle aria-label="Abrir Glosa"').tooltip('Abrir Glosa').style('padding:0;')._props['icon'] = '' # we use html inside
        with list(ui.context.client.elements.values())[-1]: # it's the fab
            ui.html(icon_svg('glosa')).classes('text-accent')

        # Scrim
        ui.element('div').classes('glosa-scrim').props('data-glosa-close')

    def render_chat_dock(self):
        if not hasattr(self, 'chat_area') or not self.chat_area: return
        self.chat_area.clear()
        
        with self.chat_area:
            if not self.chat_history:
                # Estado vacío
                with ui.column().classes('w-full items-center justify-center h-full gap-4 text-center mt-8 text-sec'):
                    ui.html(icon_svg('glosa')).style('width: 48px; height: 48px; opacity: 0.5;')
                    ui.label('¡Hola! Soy Glosa.').classes('font-bold text-lg text-main')
                    ui.label('Explicar un paso').classes('fs-small')
                    ui.label('Revisar una operación').classes('fs-small')
                    ui.label('Aclarar un concepto').classes('fs-small')
            else:
                for msg in self.chat_history:
                    self._render_message_dock(msg)
                    
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        ui.run_javascript("setTimeout(() => { const el = document.getElementById('glosa-log'); if(el) el.scrollTop = el.scrollHeight; }, 50);")

    def _render_message_dock(self, msg):
        sent = msg.get('sent', False)
        error = msg.get('error', False)
        text = msg.get('text', '')
        
        align = 'justify-end' if sent else 'justify-start'
        bg = 'var(--btn-primary-bg)' if sent else 'var(--bg-panel)'
        color = 'var(--btn-primary-text)' if sent else 'var(--text-main)'
        radius = '16px 16px 4px 16px' if sent else '16px 16px 16px 4px'
        
        with ui.row().classes(f'w-full {align} mb-0'):
            if error:
                with ui.column().classes('p-3 gap-2').style(f'background: var(--badge-err-bg); color: var(--badge-err-text); border-radius: {radius}; box-shadow: none; max-width: 85%;'):
                    ui.label(text).classes('whitespace-pre-wrap')
                    ui.button('Reintentar', icon='refresh', on_click=self._retry_last_dock).classes('btn-primary text-xs').props('flat')
            else:
                container = ui.column().classes('p-3').style(f'background: {bg}; color: {color}; border-radius: {radius}; box-shadow: none; max-width: 85%; min-width: 0;')
                with container:
                    html_content = render_glosa_text(text)
                    ui.html(html_content).classes('w-full')
                    
    def _retry_last_dock(self):
        last_user = None
        for m in reversed(self.chat_history):
            if m.get('sent'):
                last_user = m
                break
        
        if self.chat_history and self.chat_history[-1].get('error'):
            self.chat_history.pop()
            
        self.render_chat_dock()
        
        if last_user:
            asyncio.create_task(self._do_send_dock(last_user.get('api_text', last_user.get('text')), is_retry=True))

    async def send_message_dock(self):
        if getattr(self, '_is_sending', False): return
        
        text = self.input_field.value
        if not text or not text.strip(): return
        
        full_text = text.strip()
        api_text = full_text
        if getattr(self, 'attached_context', ""):
            api_text = f"[Contexto adjunto]\\n{self.attached_context}\\n\\nPregunta: {full_text}"
            self.clear_context()
            
        self.input_field.value = ''
        
        msg = {"text": full_text, "sent": True, "api_text": api_text}
        self.chat_history.append(msg)
        
        with self.chat_area:
            self._render_message_dock(msg)
            
        self._scroll_to_bottom()
        await self._do_send_dock(api_text, is_retry=False)
        
    async def _do_send_dock(self, api_text, is_retry=False):
        self._is_sending = True
        self.input_field.disable()
        
        MAX_HISTORY = 10
        history = [
            {"role": "user" if m.get("sent") else "assistant", "content": m.get("api_text", m.get("text"))}
            for m in self.chat_history
            if not m.get("error")
        ][-MAX_HISTORY:]
        
        with self.chat_area:
            typing_row = ui.row().classes('w-full justify-start mb-0')
            with typing_row:
                with ui.column().classes('p-3').style('background: var(--bg-panel); color: var(--text-sec); border-radius: 16px 16px 16px 4px; box-shadow: none; max-width: 85%;'):
                    ui.html('<div class="glosa-typing-indicator" role="status" aria-label="Glosa está escribiendo"><span>.</span><span>.</span><span>.</span></div>')
        self._scroll_to_bottom()
        
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
                self._scroll_to_bottom()
                        
        def cancel_req(req_id):
            if self._request_counter == req_id:
                self._request_counter += 1
                self._finish_send(typing_row, cancel_btn_row)
                
        ui.timer(0, show_cancel, once=True)
            
        try:
            ok, respuesta = await run.io_bound(self.motor_ia.analizar_sistema, api_text, history)
        except Exception as e:
            logger.exception("Error en _do_send_dock")
            ok, respuesta = False, str(e)
            
        if self._request_counter == current_req:
            self._finish_send(typing_row, cancel_btn_row)
            if not ok:
                msg = {"text": "Glosa no pudo responder ahora. Revisa tu conexión y vuelve a intentarlo.", "sent": False, "error": True}
                logger.error(f"Error AI: {respuesta}")
            else:
                msg = {"text": respuesta, "sent": False, "error": False}
                
            self.chat_history.append(msg)
            with self.chat_area:
                self._render_message_dock(msg)
            self._scroll_to_bottom()
            
    def _finish_send(self, typing_row, cancel_btn_row):
        try:
            typing_row.delete()
        except: pass
        try:
            if cancel_btn_row: cancel_btn_row.delete()
        except: pass
        self._is_sending = False
        self.input_field.enable()
