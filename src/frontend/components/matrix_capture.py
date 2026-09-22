import string
from nicegui import ui
from src.backend.models.matrix import Matrix
from src.backend.utils.validators import MatrixValidator

class MatrixCapturePanel:
    def __init__(self):
        self.matrices = {} # Dict de nombre -> { 'm': 3, 'n': 3, 'entradas': [], 'cache': {}, 'ui_container': None }
        self.container = None
        
    def inject_scripts(self):
        ui.add_head_html('''
            <script>
            if (!window.__matrix_ops_listeners_active) {
                window.__matrix_ops_listeners_active = true;
                
                // Navegación con teclado
                document.addEventListener('keydown', function(e) {
                    let active = document.activeElement;
                    if (active.tagName !== 'INPUT' || active.dataset.matrixRow === undefined) return;
                    let r = parseInt(active.dataset.matrixRow), c = parseInt(active.dataset.matrixCol);
                    let mId = active.dataset.matrixId;
                    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                        if (e.key === 'ArrowLeft' && active.selectionStart !== 0) return;
                        if (e.key === 'ArrowRight' && active.selectionEnd !== active.value.length) return;
                        if (e.key === 'ArrowRight') c++; if (e.key === 'ArrowLeft') c--;
                        if (e.key === 'ArrowDown') r++; if (e.key === 'ArrowUp') r--;
                    } else if (e.key === 'Enter') r++;
                    else return;
                    
                    let next = document.querySelector(`input[data-matrix-id="${mId}"][data-matrix-row="${r}"][data-matrix-col="${c}"]`);
                    if (next) { next.focus(); setTimeout(() => next.select(), 10); e.preventDefault(); }
                });

                // Soporte Paste TSV
                document.addEventListener('paste', function(e) {
                    let active = document.activeElement;
                    if (active.tagName !== 'INPUT' || active.dataset.matrixRow === undefined) return;
                    e.preventDefault();
                    let pasteData = (e.clipboardData || window.clipboardData).getData('text');
                    let rows = pasteData.trim().split('\\n');
                    let startR = parseInt(active.dataset.matrixRow), startC = parseInt(active.dataset.matrixCol);
                    let mId = active.dataset.matrixId;
                    
                    rows.forEach((rowStr, rIdx) => {
                        let cols = rowStr.split('\\t');
                        cols.forEach((val, cIdx) => {
                            let input = document.querySelector(`input[data-matrix-id="${mId}"][data-matrix-row="${startR + rIdx}"][data-matrix-col="${startC + cIdx}"]`);
                            if (input) {
                                input.value = val.trim();
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                            }
                        });
                    });
                });
                // Cross-highlighting de celdas
                document.addEventListener('focusin', function(e) {
                    let active = e.target;
                    if (active.tagName !== 'INPUT' || active.dataset.matrixRow === undefined) return;
                    let r = active.dataset.matrixRow;
                    let c = active.dataset.matrixCol;
                    let mId = active.dataset.matrixId;
                    
                    document.querySelectorAll(`input[data-matrix-id="${mId}"]`).forEach(inp => {
                        let isSame = (inp.dataset.matrixRow === r || inp.dataset.matrixCol === c);
                        let control = inp.closest('.q-field__control');
                        if(control && isSame) {
                            control.style.background = 'color-mix(in srgb, var(--accent) 15%, var(--input-bg))';
                        }
                    });
                });
                
                document.addEventListener('focusout', function(e) {
                    let active = e.target;
                    if (active.tagName !== 'INPUT' || active.dataset.matrixRow === undefined) return;
                    let mId = active.dataset.matrixId;
                    
                    document.querySelectorAll(`input[data-matrix-id="${mId}"]`).forEach(inp => {
                        let control = inp.closest('.q-field__control');
                        if(control) control.style.background = '';
                    });
                });
            }
            </script>
        ''')

    def get_next_available_name(self):
        for letter in string.ascii_uppercase:
            if letter not in self.matrices:
                return letter
        return None

    def add_matrix(self):
        name = self.get_next_available_name()
        if not name:
            ui.notify('Límite de matrices alcanzado (Z)', type='warning')
            return
            
        self.matrices[name] = {
            'm': 3,
            'n': 3,
            'entradas': [],
            'cache': {},
            'ui_container': None,
            'lbl_m': None, 'lbl_n': None, 'lbl_badge': None,
            'btn_m_dec': None, 'btn_m_inc': None, 'btn_n_dec': None, 'btn_n_inc': None
        }
        self.render_all_matrices()

    def remove_matrix(self, name):
        if name in self.matrices:
            del self.matrices[name]
            self.render_all_matrices()

    async def adjust_size(self, name, delta_m=0, delta_n=0):
        if name not in self.matrices: return
        mat = self.matrices[name]
        
        for r, fila in enumerate(mat['entradas']):
            for c, celda in enumerate(fila):
                if celda.value: mat['cache'][(r, c)] = celda.value

        if delta_m and not (1 <= mat['m'] + delta_m <= 10):
            return
        if delta_n and not (1 <= mat['n'] + delta_n <= 10):
            return

        is_remove = (delta_m < 0 or delta_n < 0)
        is_add = (delta_m > 0 or delta_n > 0)
        
        if mat['btn_m_dec']: mat['btn_m_dec'].disable()
        if mat['btn_m_inc']: mat['btn_m_inc'].disable()
        if mat['btn_n_dec']: mat['btn_n_dec'].disable()
        if mat['btn_n_inc']: mat['btn_n_inc'].disable()

        if is_remove:
            target_attr = f"[data-matrix-row='{mat['m'] - 1}']" if delta_m < 0 else f"[data-matrix-col='{mat['n'] - 1}']"
            idx_row = mat['m'] - 1
            is_m = 'true' if delta_m < 0 else 'false'
            
            js_salida = f'''
                return new Promise(resolve => {{
                    let cells = document.querySelectorAll(`input[data-matrix-id='{name}']{target_attr}`);
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
                    if ({is_m}) {{
                        let rowContainer = document.querySelector(`[data-grid-row="{name}_{idx_row}"]`);
                        if (rowContainer) {{
                            rowContainer.style.overflow = 'hidden';
                            anims.push(rowContainer.animate(
                                [{{height: rowContainer.offsetHeight + 'px', opacity: 1, marginTop: '0px', marginBottom: '8px'}},
                                 {{height: '0px', opacity: 0, marginTop: '0px', marginBottom: '0px'}}],
                                {{duration: 240, easing: 'cubic-bezier(0.32,0.72,0,1)', fill: 'forwards'}}
                            ).finished);
                        }}
                    }}
                    Promise.all(anims).then(resolve);
                }});
            '''
            await ui.run_javascript(js_salida)

        if 1 <= mat['m'] + delta_m <= 10: mat['m'] += delta_m
        if 1 <= mat['n'] + delta_n <= 10: mat['n'] += delta_n
        
        # Purgar caché de celdas fuera de rango
        mat['cache'] = {(r, c): v for (r, c), v in mat['cache'].items() if r < mat['m'] and c < mat['n']}

        if mat['lbl_m']: mat['lbl_m'].set_text(str(mat['m']))
        if mat['lbl_n']: mat['lbl_n'].set_text(str(mat['n']))
        if mat['lbl_badge']: mat['lbl_badge'].content = f'{name} <span style="color: var(--accent)">·</span> {mat["m"]} &times; {mat["n"]}'
        
        self.render_matrix_grid(name)
        
        if is_add:
            target_attr = f"[data-matrix-row='{mat['m'] - 1}']" if delta_m > 0 else f"[data-matrix-col='{mat['n'] - 1}']"
            import asyncio
            await asyncio.sleep(0.05)
            
            js_entrada = f'''
                return new Promise(resolve => {{
                    let cells = document.querySelectorAll(`input[data-matrix-id='{name}']{target_attr}`);
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
                    }} else {{
                        resolve();
                    }}
                }});
            '''
            await ui.run_javascript(js_entrada)

    def render_matrix_grid(self, name):
        mat = self.matrices[name]
        if not mat['ui_container']: return
        
        mat['ui_container'].clear()
        mat['entradas'].clear()
        
        with mat['ui_container']:
            with ui.column().style('min-width: max-content;'):
                for i in range(mat['m']):
                    with ui.row().classes('items-center gap-2 mb-2 no-wrap').props(f'data-grid-row="{name}_{i}"'):
                        fila_UI = []
                        for j in range(mat['n']):
                            val = mat['cache'].get((i, j), '')
                            
                            def update_cache(e, r=i, c=j, matrix_name=name):
                                self.matrices[matrix_name]['cache'][(r, c)] = e.value
                                
                            celda = ui.input(value=val, placeholder='', on_change=update_cache).classes('matrix-input w-20').style('min-width: 80px;').props(f'data-matrix-id="{name}" data-matrix-row="{i}" data-matrix-col="{j}" borderless autocomplete="new-password" name="{name}_r{i}c{j}"')
                            fila_UI.append(celda)
                        mat['entradas'].append(fila_UI)
                        
        if mat['btn_m_dec']: 
            if mat['m'] <= 1: mat['btn_m_dec'].disable()
            else: mat['btn_m_dec'].enable()
        if mat['btn_m_inc']: 
            if mat['m'] >= 10: mat['btn_m_inc'].disable()
            else: mat['btn_m_inc'].enable()
        if mat['btn_n_dec']: 
            if mat['n'] <= 1: mat['btn_n_dec'].disable()
            else: mat['btn_n_dec'].enable()
        if mat['btn_n_inc']: 
            if mat['n'] >= 10: mat['btn_n_inc'].disable()
            else: mat['btn_n_inc'].enable()

    def render_all_matrices(self):
        if not self.container: return
        self.container.clear()
        
        with self.container:
            for name in sorted(self.matrices.keys()):
                mat = self.matrices[name]
                with ui.column().classes('w-full panel-card p-4 mb-6'):
                    with ui.row().classes('w-full justify-between items-center mb-4'):
                        with ui.row().classes('items-center gap-2'):
                            ui.label(f'Matriz {name}').classes('text-lg font-bold text-main')
                            mat['lbl_badge'] = ui.html(f'{name} <span style="color: var(--accent)">·</span> {mat["m"]} &times; {mat["n"]}').classes('fs-small text-sec uppercase').style('letter-spacing: 0.08em; font-variant-numeric: tabular-nums; margin-bottom: -2px;')
                        
                        # Controles de dimensiones
                        from functools import partial
                        with ui.row().classes('gap-4 items-center flex-wrap'):
                            with ui.row().classes('gap-1 items-center'):
                                ui.label('Filas:').classes('text-sm text-sec mr-1')
                                mat['btn_m_dec'] = ui.button(icon='remove', on_click=partial(self.adjust_size, name, delta_m=-1), color=None).classes('btn-neo-icon w-6 h-6 p-0 min-h-0 text-xs').props('ripple=false')
                                mat['lbl_m'] = ui.label(str(mat['m'])).classes('font-bold w-4 text-center')
                                mat['btn_m_inc'] = ui.button(icon='add', on_click=partial(self.adjust_size, name, delta_m=1), color=None).classes('btn-neo-icon w-6 h-6 p-0 min-h-0 text-xs').props('ripple=false')
                            
                            with ui.row().classes('gap-1 items-center'):
                                ui.label('Cols:').classes('text-sm text-sec mr-1')
                                mat['btn_n_dec'] = ui.button(icon='remove', on_click=partial(self.adjust_size, name, delta_n=-1), color=None).classes('btn-neo-icon w-6 h-6 p-0 min-h-0 text-xs').props('ripple=false')
                                mat['lbl_n'] = ui.label(str(mat['n'])).classes('font-bold w-4 text-center')
                                mat['btn_n_inc'] = ui.button(icon='add', on_click=partial(self.adjust_size, name, delta_n=1), color=None).classes('btn-neo-icon w-6 h-6 p-0 min-h-0 text-xs').props('ripple=false')

                            ui.button(icon='delete', on_click=partial(self.remove_matrix, name), color=None).classes('btn-ghost w-8 h-8 p-0 ml-2').style('color: var(--error)').props('ripple=false').tooltip('Eliminar Matriz')

                    # Configurar estado inicial deshabilitado si corresponde
                    if mat['m'] <= 1: mat['btn_m_dec'].disable()
                    if mat['m'] >= 10: mat['btn_m_inc'].disable()
                    if mat['n'] <= 1: mat['btn_n_dec'].disable()
                    if mat['n'] >= 10: mat['btn_n_inc'].disable()

                    mat['ui_container'] = ui.column().classes('overflow-auto w-full max-h-[300px]')
                    self.render_matrix_grid(name)

    def build_container(self):
        with ui.row().classes('w-full justify-end mb-4'):
            ui.button('+ Añadir Matriz', icon='add', on_click=self.add_matrix, color=None).classes('btn-ghost py-1 px-4 text-sm').props('ripple=false')
            
        self.container = ui.column().classes('w-full')
        
        # Valores iniciales si está vacío
        if not self.matrices:
            self.matrices['A'] = {'m': 3, 'n': 3, 'entradas': [], 'cache': {}, 'ui_container': None, 'lbl_m': None, 'lbl_n': None, 'lbl_badge': None, 'btn_m_dec': None, 'btn_m_inc': None, 'btn_n_dec': None, 'btn_n_inc': None}
            self.matrices['B'] = {'m': 3, 'n': 3, 'entradas': [], 'cache': {}, 'ui_container': None, 'lbl_m': None, 'lbl_n': None, 'lbl_badge': None, 'btn_m_dec': None, 'btn_m_inc': None, 'btn_n_dec': None, 'btn_n_inc': None}
            
        self.render_all_matrices()

    def get_matrices_dict(self):
        """Devuelve un diccionario de dicts con raw_data (strings), para que
        el controller las parsee con parse_number_exact y preserve fracciones
        exactas sin importar el tamaño del denominador."""
        result = {}
        for name, mat in self.matrices.items():
            parsed_data = []
            for r in range(mat['m']):
                row_vals = []
                for c in range(mat['n']):
                    val_str = str(mat['cache'].get((r, c), '0')).strip()
                    if not val_str:
                        val_str = '0'
                    
                    # Se conserva la validación para dar feedback inmediato en la UI,
                    # pero ahora se envía el string original al backend para no
                    # perder precisión en fracciones con denominador > 1000.
                    success, _, msg = MatrixValidator.parse_number_exact(val_str)
                    if not success:
                        raise ValueError(f"Error en Matriz {name}, celda [{r+1},{c+1}]: {msg}")
                    row_vals.append(val_str)
                parsed_data.append(row_vals)
                
            result[name] = {
                "rows": mat['m'],
                "cols": mat['n'],
                "data": parsed_data
            }
        return result
