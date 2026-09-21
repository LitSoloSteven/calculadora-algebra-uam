import string
from nicegui import ui
from src.backend.utils.validators import MatrixValidator

class VectorCapturePanel:
    def __init__(self, panel_id: str, *, min_vectors=1, max_vectors=8,
                 allow_orientation_toggle=True,
                 default_orientation='column',
                 first_vector_fixed_label=None):
        self.panel_id = panel_id
        self.min_vectors = min_vectors
        self.max_vectors = max_vectors
        self.allow_orientation_toggle = allow_orientation_toggle
        self.first_vector_fixed_label = first_vector_fixed_label
        
        self.vectors = {} # name -> { 'orientation': 'column', 'cache': {}, 'ui_container': None, ... }
        self.dim = 3 # Shared dimension 'n' for all vectors
        self.container = None
        self.header_container = None
        
        self.default_orientation = default_orientation
        if not allow_orientation_toggle:
            self.default_orientation = 'column' # enforce column if toggle is disabled

    def inject_scripts(self):
        ui.add_head_html('''
            <script>
            if (!window.__vector_listeners_active) {
                window.__vector_listeners_active = true;
                
                // Navegación con teclado
                document.addEventListener('keydown', function(e) {
                    let active = document.activeElement;
                    if (active.tagName !== 'INPUT' || active.dataset.vecIdx === undefined) return;
                    
                    let idx = parseInt(active.dataset.vecIdx);
                    let vId = active.dataset.vecId;
                    let orientation = active.dataset.vecOrientation;
                    
                    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                        if (e.key === 'ArrowLeft' && active.selectionStart !== 0) return;
                        if (e.key === 'ArrowRight' && active.selectionEnd !== active.value.length) return;
                        
                        if (orientation === 'column') {
                            if (e.key === 'ArrowDown') idx++; 
                            if (e.key === 'ArrowUp') idx--;
                        } else {
                            if (e.key === 'ArrowRight') idx++; 
                            if (e.key === 'ArrowLeft') idx--;
                        }
                    } else if (e.key === 'Enter') idx++;
                    else return;
                    
                    let next = document.querySelector(`input[data-vec-id="${vId}"][data-vec-idx="${idx}"]`);
                    if (next) { next.focus(); setTimeout(() => next.select(), 10); e.preventDefault(); }
                });

                // Soporte Paste TSV/CSV simple
                document.addEventListener('paste', function(e) {
                    let active = document.activeElement;
                    if (active.tagName !== 'INPUT' || active.dataset.vecIdx === undefined) return;
                    e.preventDefault();
                    let pasteData = (e.clipboardData || window.clipboardData).getData('text');
                    
                    // Separar por comas, tabs o newlines
                    let vals = pasteData.trim().split(/[\\n\\t,;]+/);
                    let startIdx = parseInt(active.dataset.vecIdx);
                    let vId = active.dataset.vecId;
                    
                    vals.forEach((val, i) => {
                        let input = document.querySelector(`input[data-vec-id="${vId}"][data-vec-idx="${startIdx + i}"]`);
                        if (input) {
                            input.value = val.trim();
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    });
                });
                
                // Cross-highlighting de celdas
                document.addEventListener('focusin', function(e) {
                    let active = e.target;
                    if (active.tagName !== 'INPUT' || active.dataset.vecIdx === undefined) return;
                    let idx = active.dataset.vecIdx;
                    let vId = active.dataset.vecId;
                    
                    document.querySelectorAll(`input[data-vec-id="${vId}"]`).forEach(inp => {
                        let isSame = (inp.dataset.vecIdx === idx);
                        let control = inp.closest('.q-field__control');
                        if(control && isSame) {
                            control.style.background = 'color-mix(in srgb, var(--accent) 15%, var(--input-bg))';
                        }
                    });
                });
                
                document.addEventListener('focusout', function(e) {
                    let active = e.target;
                    if (active.tagName !== 'INPUT' || active.dataset.vecIdx === undefined) return;
                    let vId = active.dataset.vecId;
                    
                    document.querySelectorAll(`input[data-vec-id="${vId}"]`).forEach(inp => {
                        let control = inp.closest('.q-field__control');
                        if(control) control.style.background = '';
                    });
                });
            }
            </script>
        ''')

    def get_next_available_name(self):
        if self.first_vector_fixed_label and self.first_vector_fixed_label not in self.vectors:
            return self.first_vector_fixed_label
            
        if self.max_vectors <= 3:
            for letter in ['u', 'v', 'w']:
                if letter not in self.vectors and letter != self.first_vector_fixed_label:
                    return letter
        
        for i in range(1, 10):
            name = f"v_{i}"
            if name not in self.vectors and name != self.first_vector_fixed_label:
                return name
        return "x"

    def add_vector(self):
        if len(self.vectors) >= self.max_vectors:
            ui.notify(f'Límite de vectores alcanzado ({self.max_vectors})', type='warning')
            return
            
        name = self.get_next_available_name()
        if not name:
            return
            
        self.vectors[name] = {
            'orientation': self.default_orientation,
            'cache': {},
            'ui_container': None,
            'lbl_badge': None,
            'btn_toggle': None
        }
        self.render_all_vectors()

    def remove_vector(self, name):
        if len(self.vectors) <= self.min_vectors:
            ui.notify(f'Se requiere al menos {self.min_vectors} vector(es)', type='warning')
            return
        if name == self.first_vector_fixed_label:
            return
            
        if name in self.vectors:
            del self.vectors[name]
            self.render_all_vectors()

    async def adjust_dimension(self, delta=0):
        new_dim = self.dim + delta
        if not (1 <= new_dim <= 10):
            return
            
        is_remove = (delta < 0)
        is_add = (delta > 0)

        if hasattr(self, 'btn_dim_dec') and self.btn_dim_dec: self.btn_dim_dec.disable()
        if hasattr(self, 'btn_dim_inc') and self.btn_dim_inc: self.btn_dim_inc.disable()

        if is_remove:
            idx_remove = self.dim - 1
            js_salida = f'''
                return new Promise(resolve => {{
                    let cells = document.querySelectorAll(`input[data-vec-idx='{idx_remove}']`);
                    const anims = [];
                    cells.forEach(input => {{
                        let control = input.closest('.q-field__control');
                        if(control) {{
                            anims.push(control.animate(
                                [{{opacity: 1, transform: 'scale(1)', filter: 'blur(0)'}},
                                 {{opacity: 0, transform: 'scale(0.85) translateY(-8px)', filter: 'blur(2px)'}}],
                                {{duration: 240, easing: 'cubic-bezier(0.32,0.72,0,1)', fill: 'forwards'}}
                            ).finished);
                        }}
                    }});
                    if (anims.length > 0) {{
                        Promise.all(anims).then(resolve);
                    }} else {{ resolve(); }}
                }});
            '''
            await ui.run_javascript(js_salida)

        self.dim = new_dim
        
        for v in self.vectors.values():
            v['cache'] = {i: val for i, val in v['cache'].items() if i < self.dim}
            
        if hasattr(self, 'lbl_dim') and self.lbl_dim: 
            self.lbl_dim.set_text(str(self.dim))

        self._update_all_grids()
        
        if hasattr(self, 'btn_dim_dec') and self.btn_dim_dec:
            if self.dim > 1: self.btn_dim_dec.enable()
        if hasattr(self, 'btn_dim_inc') and self.btn_dim_inc:
            if self.dim < 10: self.btn_dim_inc.enable()

        if is_add:
            idx_add = self.dim - 1
            import asyncio
            await asyncio.sleep(0.05)
            js_entrada = f'''
                return new Promise(resolve => {{
                    let cells = document.querySelectorAll(`input[data-vec-idx='{idx_add}']`);
                    const anims = [];
                    cells.forEach(input => {{
                        let control = input.closest('.q-field__control');
                        if(control) {{
                            anims.push(control.animate(
                                [{{opacity: 0, transform: 'scale(0.85) translateY(8px)', filter: 'blur(2px)'}},
                                 {{opacity: 1, transform: 'scale(1)', filter: 'blur(0)'}}],
                                {{duration: 240, easing: 'cubic-bezier(0.32,0.72,0,1)', fill: 'forwards'}}
                            ).finished);
                        }}
                    }});
                    if (anims.length > 0) {{
                        Promise.all(anims).then(resolve);
                    }} else {{ resolve(); }}
                }});
            '''
            await ui.run_javascript(js_entrada)

    def toggle_orientation(self, name):
        if name not in self.vectors or not self.allow_orientation_toggle:
            return
        
        v = self.vectors[name]
        v['orientation'] = 'row' if v['orientation'] == 'column' else 'column'
        
        self.render_vector_grid(name)
        
        if v['lbl_badge']:
            name_html = name
            if "_" in name:
                parts = name.split("_")
                name_html = f"<i>{parts[0]}</i><sub>{parts[1]}</sub>"
            else:
                name_html = f"<i>{name}</i>"
            badge_text = "n &times; 1" if v["orientation"] == "column" else "1 &times; n"
            v['lbl_badge'].content = f'{name_html} <span style="color: var(--accent)">·</span> {badge_text}'
            
        if v['btn_toggle']:
            v['btn_toggle'].props(f'icon={"swap_vert" if v["orientation"] == "column" else "swap_horiz"}')

    def render_vector_grid(self, name):
        v = self.vectors[name]
        if not v['ui_container']: return
        
        v['ui_container'].clear()
        
        with v['ui_container']:
            container_classes = 'items-center gap-2 overflow-x-auto overflow-y-hidden max-w-full pb-2' if v['orientation'] == 'row' else 'items-center gap-2 overflow-y-auto max-h-[300px]'
            layout = ui.row() if v['orientation'] == 'row' else ui.column()
            
            with layout.classes(container_classes).style('flex-wrap: nowrap;' if v['orientation'] == 'row' else ''):
                for i in range(self.dim):
                    val = v['cache'].get(i, '')
                    
                    def update_cache(e, idx=i, vec_name=name):
                        self.vectors[vec_name]['cache'][idx] = e.value
                        
                    ui.input(value=val, placeholder='', on_change=update_cache).classes('matrix-input w-20').style('min-width: 80px; flex-shrink: 0;').props(f'data-vec-id="{self.panel_id}_{name}" data-vec-idx="{i}" data-vec-orientation="{v["orientation"]}" borderless autocomplete="new-password" name="{self.panel_id}_{name}_idx{i}"')

    def _update_all_grids(self):
        for name in self.vectors:
            self.render_vector_grid(name)

    def render_all_vectors(self):
        if not self.container: return
        self.container.clear()
        
        if self.header_container:
            self.header_container.clear()
            with self.header_container:
                with ui.row().classes('w-full justify-between items-center mb-4 panel-card p-3 border border-[var(--border-input)]'):
                    ui.label('Dimensión de los vectores (n)').classes('text-sm font-bold text-main')
                    
                    from functools import partial
                    with ui.row().classes('gap-2 items-center'):
                        self.btn_dim_dec = ui.button(icon='remove', on_click=partial(self.adjust_dimension, delta=-1), color=None).classes('btn-neo-icon w-6 h-6 p-0 min-h-0 text-xs').props('ripple=false')
                        if self.dim <= 1: self.btn_dim_dec.disable()
                        
                        self.lbl_dim = ui.label(str(self.dim)).classes('font-bold w-4 text-center')
                        
                        self.btn_dim_inc = ui.button(icon='add', on_click=partial(self.adjust_dimension, delta=1), color=None).classes('btn-neo-icon w-6 h-6 p-0 min-h-0 text-xs').props('ripple=false')
                        if self.dim >= 10: self.btn_dim_inc.disable()
                        
                    if len(self.vectors) < self.max_vectors:
                        ui.button('+ Añadir Vector', icon='add', on_click=self.add_vector, color=None).classes('btn-ghost py-1 px-3 text-xs ml-auto').props('ripple=false')
        
        with self.container:
            for name in self.vectors.keys():
                v = self.vectors[name]
                with ui.column().classes('w-full panel-card p-4 mb-4'):
                    with ui.row().classes('w-full justify-between items-center mb-4'):
                        with ui.row().classes('items-center gap-2'):
                            name_html = name
                            if "_" in name:
                                parts = name.split("_")
                                name_html = f"<i>{parts[0]}</i><sub>{parts[1]}</sub>"
                            else:
                                name_html = f"<i>{name}</i>"
                                
                            ui.html(f'<span class="text-lg font-bold text-main math-label">{name_html}</span>')
                            
                            badge_text = "n &times; 1" if v["orientation"] == "column" else "1 &times; n"
                            v['lbl_badge'] = ui.html(f'{name_html} <span style="color: var(--accent)">·</span> {badge_text}').classes('fs-small text-sec uppercase').style('letter-spacing: 0.08em; font-variant-numeric: tabular-nums; margin-bottom: -2px;')
                        
                        from functools import partial
                        with ui.row().classes('gap-2 items-center flex-wrap'):
                            if self.allow_orientation_toggle:
                                icon = "swap_vert" if v["orientation"] == "column" else "swap_horiz"
                                tooltip = "Fila/Columna"
                                v['btn_toggle'] = ui.button(icon=icon, on_click=partial(self.toggle_orientation, name), color=None).classes('btn-ghost w-8 h-8 p-0 text-sec').props('ripple=false').tooltip(tooltip)

                            if len(self.vectors) > self.min_vectors and name != self.first_vector_fixed_label:
                                ui.button(icon='delete', on_click=partial(self.remove_vector, name), color=None).classes('btn-ghost w-8 h-8 p-0 ml-2').style('color: var(--error)').props('ripple=false').tooltip('Eliminar Vector')

                    v['ui_container'] = ui.column().classes('w-full')
                    self.render_vector_grid(name)

    def build_container(self):
        self.header_container = ui.column().classes('w-full')
        self.container = ui.column().classes('w-full')
        
        if not self.vectors:
            for _ in range(self.min_vectors):
                name = self.get_next_available_name()
                if name:
                    self.vectors[name] = {'orientation': self.default_orientation, 'cache': {}, 'ui_container': None, 'lbl_badge': None, 'btn_toggle': None}
            
        self.render_all_vectors()

    def get_vectors_dict(self):
        result = {}
        for name, v in self.vectors.items():
            parsed_data = []
            for i in range(self.dim):
                val_str = str(v['cache'].get(i, '0')).strip()
                if not val_str:
                    val_str = '0'
                
                success, _, msg = MatrixValidator.parse_number_exact(val_str)
                if not success:
                    raise ValueError(f"Error en Vector {name}, componente {i+1}: {msg}")
                parsed_data.append(val_str)
                
            result[name] = {
                "orientation": v["orientation"],
                "data": parsed_data
            }
        return result

    def clear(self):
        for v in self.vectors.values():
            v['cache'].clear()
        self._update_all_grids()
