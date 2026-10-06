import logging
import asyncio
import time
import threading
from nicegui import ui, run
from src.frontend.components.icons import icon_svg
from src.frontend.components.glosa_render import render_glosa_text
from src.frontend.components.glosa_chips import render_chip_row, render_followups
from src.frontend.suggestions import suggest, FOLLOW_UPS, chips_active
from src.ai.openrouter_ai import AIResult, AIErrorKind

logger = logging.getLogger(__name__)

MAX_HISTORY = 60

class GlosaDockMixin:
    def _spawn(self, coro) -> asyncio.Task:
        """Crea una tarea async que entra al contexto del cliente antes de ejecutar la corrutina."""
        async def runner():
            client = getattr(self, '_client', None)
            if client is not None and not getattr(client, 'is_deleted', False):
                with client:
                    return await coro
            return await coro

        r = runner()
        try:
            task = asyncio.create_task(r)
            task.add_done_callback(lambda t: coro.close())
            return task
        except Exception:
            r.close()
            coro.close()
            raise

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
                    ui.button(icon='delete_sweep', on_click=self.clear_chat, color=None).classes('btn-neo-icon w-8 h-8 p-0 text-sec').props('ripple=false aria-label="Limpiar conversación"').tooltip('Limpiar conversación')
                    ui.button(icon='close', color=None).classes('btn-neo-icon w-8 h-8 p-0').props('ripple=false data-glosa-close aria-label="Cerrar Glosa"').tooltip('Cerrar')

            # Log
            self.chat_area = ui.column().classes('w-full flex-1 p-4 overflow-y-auto gap-4').style('min-height: 0; overscroll-behavior: contain;').props('id="glosa-log" role="log" aria-live="polite"')
            self.render_chat_dock()

            # Footer
            with ui.column().classes('w-full p-4 border-t border-[var(--border-input)] bg-[var(--bg-elevated)] flex-shrink-0'):
                self.render_context_pill()
                
                self.focus_chip_container = ui.row().classes('w-full mt-2 empty:hidden')
                with self.focus_chip_container:
                    self.render_focus_chip_ui()
                
                self.dock_chips_container = ui.column().classes('w-full mt-2')
                self._last_chips_ids = ()
                self._render_dock_chips()
                
                with ui.row().classes('w-full items-end gap-2 no-wrap mt-2'):
                    self.input_field = ui.textarea(placeholder='Pregunta algo sobre tu ejercicio...').classes('flex-1 glosa-input').props('borderless autogrow').style('max-height: 120px; min-width: 0;')
                    self.input_field.on('keydown.enter.prevent.exact', self.send_message_dock)
                    
                    ui.button(icon='send', on_click=self.send_message_dock, color=None).classes('btn-primary w-10 h-10 p-0 mb-1 flex-shrink-0').props('ripple=false aria-label="Enviar"').style('border-radius: 12px;').tooltip('Enviar')
                    
        # FAB
        with ui.button(color=None).classes('glosa-fab').props('ripple=false data-glosa-toggle aria-controls="glosa-dock" aria-expanded="false" aria-label="Abrir Glosa"') as fab:
            ui.html(icon_svg('glosa')).classes('text-accent')
        fab.tooltip('Abrir Glosa')

        # Scrim
        ui.element('div').classes('glosa-scrim').props('data-glosa-close')

    def _toggle_ctx(self, e):
        self._storage['ai_ctx_enabled'] = e.value
        self.render_context_pill.refresh()

    @ui.refreshable
    def render_context_pill(self):
        enabled = self._storage.get('ai_ctx_enabled', True)
        ctx_obj = None
        if enabled and hasattr(self.active_ui, 'get_ai_context'):
            try:
                ctx_obj = self.active_ui.get_ai_context()
            except Exception:
                pass
                
        if ctx_obj is None or getattr(ctx_obj, 'empty', False):
            with ui.row().classes('w-full items-center justify-between px-2 py-1').style('background: var(--bg-panel); border-radius: 8px;'):
                ui.label('Sin contexto del ejercicio').classes('text-xs text-sec')
                ui.switch('Auto-adjuntar', value=enabled, on_change=self._toggle_ctx).classes('text-xs').props('dense size=sm')
            return

        lbl = f"Viendo: {ctx_obj.label}"
        if ctx_obj.stale:
            lbl = "Los datos cambiaron desde el último cálculo"
        elif ctx_obj.window_note:
            lbl += f" ({ctx_obj.window_note})"
            
        classes = 'glosa-ctx row items-center gap-2 w-full justify-between px-3 py-2'
        if ctx_obj.stale:
            classes += ' desactualizado'
            
        with ui.row().classes(classes).style('background: var(--bg-panel); border-radius: 8px; border: 1px solid var(--border-input);'):
            with ui.row().classes('items-center gap-2 min-w-0 flex-1'):
                ui.icon('visibility', size='xs').classes('text-accent')
                ui.label(lbl).classes('glosa-ctx-label truncate text-xs font-semibold').tooltip(lbl)
                
            with ui.row().classes('items-center gap-3 flex-shrink-0'):
                ui.switch(value=enabled, on_change=self._toggle_ctx).props('dense size=sm aria-label="Incluir el contexto del ejercicio"').tooltip('Activar/desactivar contexto')

    def notify_context_changed(self):
        if hasattr(self, '_ctx_version'):
            self._ctx_version += 1
        self.render_context_pill.refresh()
        self._render_dock_chips()

    @ui.refreshable
    def render_focus_chip_ui(self):
        foc = getattr(self, 'explain_focus', None)
        if not foc: return
        from src.frontend.components.glosa_chips import render_focus_chip
        text = f"Paso {foc['index']}: {foc['op']}"
        render_focus_chip(text, self.clear_explain_focus)

    def set_explain_focus(self, step_meta):
        self.explain_focus = step_meta
        self.render_focus_chip_ui.refresh()
        
    def clear_explain_focus(self):
        self.explain_focus = None
        self.render_focus_chip_ui.refresh()

    def _render_dock_chips(self):
        if not hasattr(self, 'dock_chips_container') or not self.dock_chips_container:
            return
        if not chips_active():
            self.dock_chips_container.clear()
            return
            
        signals = None
        if hasattr(self.active_ui, 'get_ai_signals'):
            try:
                signals = self.active_ui.get_ai_signals()
            except Exception as e:
                logger.error(f"Error en get_ai_signals: {e}")
                
        enabled = self._storage.get('ai_ctx_enabled', True)
        suggs = suggest(signals, limit=3, include_specific=enabled)
        ids = tuple(s.id for s in suggs)
        
        if ids == self._last_chips_ids and not getattr(self, '_force_chips_render', False):
            return
            
        self._last_chips_ids = ids
        self._force_chips_render = False
        
        self.dock_chips_container.clear()
        if not suggs:
            return
            
        with self.dock_chips_container:
            is_sending = getattr(self, '_is_sending', False)
            render_chip_row(suggs, self.ask_suggestion, variant='dock', disabled=is_sending)

    def render_chat_dock(self):
        if not hasattr(self, 'chat_area') or not self.chat_area: return
        self.chat_area.clear()
        
        with self.chat_area:
            if not self.chat_history:
                with ui.column().classes('w-full items-center justify-center h-full gap-4 text-center mt-8 text-sec'):
                    ui.html(icon_svg('glosa')).style('width: 48px; height: 48px; opacity: 0.5;')
                    ui.label('Hola, soy Glosa.').classes('font-bold text-lg text-main')
                    ui.label('Explicar un paso').classes('fs-small')
                    ui.label('Revisar una operación').classes('fs-small')
                    ui.label('Aclarar un concepto').classes('fs-small')
            else:
                for i, msg in enumerate(self.chat_history):
                    self._render_message_dock(msg, is_last=(i == len(self.chat_history) - 1))
                    
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        client = getattr(self, '_client', None)
        if client is not None and not getattr(client, 'is_deleted', False):
            try:
                client.run_javascript("setTimeout(() => { const el = document.getElementById('glosa-log') || document.getElementById('ai-chat-area') || document.querySelector('.glosa-messages'); if(el) el.scrollTop = el.scrollHeight; }, 50);")
            except Exception as e:
                logger.debug("Error en _scroll_to_bottom: %s", e)
        else:
            try:
                ui.run_javascript("setTimeout(() => { const el = document.getElementById('glosa-log') || document.getElementById('ai-chat-area') || document.querySelector('.glosa-messages'); if(el) el.scrollTop = el.scrollHeight; }, 50);")
            except Exception:
                pass

    def _render_message_dock(self, msg, is_last=False):
        sent = msg.get('sent', False)
        error = msg.get('error', False)
        text = msg.get('text', '')
        retry = msg.get('retry', False)
        
        radius = '16px 16px 4px 16px' if sent else '16px 16px 16px 4px'
        col_align = 'items-end' if sent else 'items-start'
        
        with ui.column().classes(f'w-full {col_align} mb-0'):
            if error:
                with ui.column().classes('p-3 gap-2').style(f'background: var(--badge-err-bg); color: var(--badge-err-text); border-radius: {radius}; box-shadow: none; max-width: 85%;'):
                    ui.label(text).classes('whitespace-pre-wrap text-sm')
                    if retry:
                        ui.button('Reintentar', icon='refresh', on_click=self._retry_last_dock).classes('btn-primary text-xs').props('flat')
            else:
                bg = 'var(--btn-primary-bg)' if sent else 'var(--bg-panel)'
                color = 'var(--btn-primary-text)' if sent else 'var(--text-main)'
                container = ui.column().classes('p-3').style(f'background: {bg}; color: {color}; border-radius: {radius}; box-shadow: none; max-width: 85%; min-width: 0;')
                with container:
                    html_content = render_glosa_text(text)
                    ui.html(html_content).classes('w-full')
                    
            if is_last and not sent and not error and chips_active():
                self.followups_container = ui.column().classes('w-full mt-2')
                with self.followups_container:
                    render_followups(FOLLOW_UPS, self.ask_followup, disabled=getattr(self, '_is_sending', False))
                    
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
            self._spawn(self._submit(
                last_user.get('text', ''),
                cacheable=last_user.get('cacheable', False),
                simpler=last_user.get('simpler', False),
                is_retry=True
            ))

    async def send_message_dock(self):
        text = self.input_field.value
        await self._submit(text)

    def ask_suggestion(self, s, from_keyboard=False):
        if getattr(self, '_is_sending', False):
            ui.notify('Glosa está respondiendo. Espera a que termine.', type='warning')
            return
            
        if s.focus and hasattr(self.active_ui, 'focus_cell'):
            self.active_ui.focus_cell(s.focus)
            
        from src.frontend import flags
        if flags.dock_enabled() and not getattr(self, 'is_open', False):
            if from_keyboard:
                ui.run_javascript("if(window.scalarisGlosa) window.scalarisGlosa.open({instant: true, trigger: 'keyboard'});")
            else:
                ui.run_javascript("if(window.scalarisGlosa) window.scalarisGlosa.open();")
                
        if from_keyboard and self.input_field and not s.focus:
            ui.run_javascript("setTimeout(() => { const el = document.querySelector('.glosa-input textarea'); if(el) el.focus(); }, 100);")
            
        self._spawn(self._submit(s.text, cacheable=True, from_keyboard=from_keyboard))

    def ask_followup(self, f, from_keyboard=False):
        if getattr(self, '_is_sending', False):
            ui.notify('Glosa está respondiendo. Espera a que termine.', type='warning')
            return
            
        if from_keyboard and self.input_field:
            ui.run_javascript("setTimeout(() => { const el = document.querySelector('.glosa-input textarea'); if(el) el.focus(); }, 100);")
            
        self._spawn(self._submit(f.question, cacheable=False, simpler=f.simpler, from_keyboard=from_keyboard))

    def trigger_explain_step(self, step_meta):
        if getattr(self, '_is_sending', False):
            ui.notify('Glosa está respondiendo. Espera a que termine.', type='warning')
            return
            
        from src.frontend import flags
        if flags.dock_enabled() and not getattr(self, 'is_open', False):
            ui.run_javascript("if(window.scalarisGlosa) window.scalarisGlosa.open();")
            
        self.set_explain_focus(step_meta)
        
        from src.ai.prompts import build_explain_step_question
        question = build_explain_step_question(
            step_meta.get("kind", "otro"),
            step_meta.get("index", 1),
            step_meta.get("total", 1),
            step_meta.get("op", "")
        )
        
        self._spawn(self._submit(question, cacheable=True, simpler=True))

    async def _submit(self, text, *, cacheable=False, simpler=False, from_keyboard=False, is_retry=False):
        if getattr(self, '_is_sending', False):
            return
            
        now = time.monotonic()
        if now - getattr(self, '_last_send_time', 0) < 1.5:
            ui.notify('Espera un momento antes de enviar otra pregunta.', type='warning')
            return
            
        if not text or not text.strip(): return
        full_text = text.strip()
        
        if self.input_field:
            self.input_field.value = ''
            self.input_field.disable()
            
        if not is_retry:
            msg = {"text": full_text, "sent": True, "cacheable": cacheable, "simpler": simpler}
            self.chat_history.append(msg)
            if len(self.chat_history) > MAX_HISTORY:
                self.chat_history = self.chat_history[-MAX_HISTORY:]
            
        self._is_sending = True
        self._last_send_time = time.monotonic()
        
        self._force_chips_render = True
        self._render_dock_chips()
        
        if hasattr(self, 'followups_container') and self.followups_container:
            try:
                self.followups_container.delete()
                self.followups_container = None
            except Exception: pass
        
        with self.chat_area:
            if not is_retry:
                from src.frontend import flags
                if flags.dock_enabled():
                    self._render_message_dock(self.chat_history[-1], is_last=False)
                else:
                    self._render_message(self.chat_history[-1], idx=len(self.chat_history)-1)
            typing_row = ui.row().classes('w-full justify-start mb-0')
            with typing_row:
                with ui.column().classes('p-3').style('background: var(--bg-panel); color: var(--text-sec); border-radius: 16px 16px 16px 4px; box-shadow: none; max-width: 85%;'):
                    ui.html('<div class="glosa-typing-indicator" role="status" aria-label="Glosa está escribiendo"><span>.</span><span>.</span><span>.</span></div>')
        self._scroll_to_bottom()
        
        ctx_block = self._collect_context()
        history = self.chat_history[:-1]
        
        self._request_counter = getattr(self, '_request_counter', 0) + 1
        current_req = self._request_counter
        
        cancel_event = threading.Event()
        cancel_btn_row = None
        
        async def show_cancel():
            await asyncio.sleep(5)
            if self._request_counter == current_req and getattr(self, '_is_sending', False) and not cancel_event.is_set():
                with self.chat_area:
                    nonlocal cancel_btn_row
                    cancel_btn_row = ui.row().classes('w-full justify-center mt-2')
                    with cancel_btn_row:
                        ui.button('Cancelar', on_click=lambda: cancel_req(current_req)).classes('btn-ghost text-xs text-sec')
                self._scroll_to_bottom()
                        
        def cancel_req(req_id):
            if self._request_counter == req_id and getattr(self, '_is_sending', False):
                cancel_event.set()
                self._request_counter += 1
                self._finish_send(typing_row, cancel_btn_row)
                self._last_send_time = 0.0
                
        with self.chat_area:
            ui.timer(0, show_cancel, once=True)
            
        try:
            result = await run.io_bound(
                self.motor_ia.ask, 
                full_text, 
                history=history, 
                context_block=ctx_block, 
                cancel=cancel_event,
                cacheable=cacheable,
                simpler=simpler
            )
        except Exception:
            logger.exception("Error inesperado en _submit de Glosa")
            result = AIResult(False, "Glosa no pudo responder ahora. Vuelve a intentarlo en un momento.", kind=AIErrorKind.SERVICE)
            
        if self._request_counter == current_req:
            self._finish_send(typing_row, cancel_btn_row)
            
            if result.kind == AIErrorKind.CANCELLED:
                return
                
            if not result.ok:
                msg = {"text": result.text, "sent": False, "error": True, "retry": result.kind not in (AIErrorKind.NO_KEY, AIErrorKind.AUTH)}
                logger.error(f"Error AI: {result.text}")
            else:
                msg = {"text": result.text, "sent": False, "error": False}
                
            self.chat_history.append(msg)
            if len(self.chat_history) > MAX_HISTORY:
                self.chat_history = self.chat_history[-MAX_HISTORY:]
            with self.chat_area:
                from src.frontend import flags
                if flags.dock_enabled():
                    self._render_message_dock(msg, is_last=True)
                else:
                    self._render_message(msg, idx=len(self.chat_history)-1)
            self._scroll_to_bottom()
            
    def _finish_send(self, typing_row, cancel_btn_row):
        try:
            typing_row.delete()
        except: pass
        try:
            if cancel_btn_row: cancel_btn_row.delete()
        except: pass
        self._is_sending = False
        if getattr(self, 'input_field', None):
            self.input_field.enable()
        self._force_chips_render = True
        self._render_dock_chips()
