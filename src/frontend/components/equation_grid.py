from nicegui import ui

class EquationGrid:
    def __init__(self, default_m=3, default_n=3):
        self.entradas_A = []
        self.entradas_b = []
        self.m = default_m
        self.n = default_n
        self.contenedor_matriz = None
        self.shape_label = None
        self._cache_A = {}  # Guardar (row, col) -> value
        self._cache_b = {}  # Guardar row -> value
        self.on_data_change = None
        self.btn_m_dec = None
        self.btn_m_inc = None
        self.btn_n_dec = None
        self.btn_n_inc = None

    def inject_scripts(self):
        ui.add_head_html('''
            <script>
            if (!window.__matrix_listeners_active) {
                window.__matrix_listeners_active = true;
                // Navegación con teclado
                document.addEventListener('keydown', function(e) {
                    let active = document.activeElement;
                if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
                let r = parseInt(active.dataset.row), c = parseInt(active.dataset.col);
                if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                    if (e.key === 'ArrowLeft' && active.selectionStart !== 0) return;
                    if (e.key === 'ArrowRight' && active.selectionEnd !== active.value.length) return;
                    if (e.key === 'ArrowRight') c++; if (e.key === 'ArrowLeft') c--;
                    if (e.key === 'ArrowDown') r++; if (e.key === 'ArrowUp') r--;
                } else if (e.key === 'Enter') r++;
                else return;
                
                let next = document.querySelector(`input[data-row="${r}"][data-col="${c}"]`);
                if (next) { next.focus(); setTimeout(() => next.select(), 10); e.preventDefault(); }
            });

            // Soporte Paste TSV (Excel/Portapapeles)
            document.addEventListener('paste', function(e) {
                let active = document.activeElement;
                if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
                e.preventDefault();
                let pasteData = (e.clipboardData || window.clipboardData).getData('text');
                let rows = pasteData.replace(/\\s+$/, '').split('\\n');
                let startR = parseInt(active.dataset.row), startC = parseInt(active.dataset.col);
                
                rows.forEach((rowStr, rIdx) => {
                    let cols = rowStr.split('\\t');
                    cols.forEach((val, cIdx) => {
                        let input = document.querySelector(`input[data-row="${startR + rIdx}"][data-col="${startC + cIdx}"]`);
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
                if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
                let r = active.dataset.row;
                let c = active.dataset.col;
                
                let container = active.closest('.panel-card');
                if(!container) return;
                
                container.querySelectorAll('input[data-row]').forEach(inp => {
                    let isSame = (inp.dataset.row === r || inp.dataset.col === c);
                    let control = inp.closest('.q-field__control');
                    if(control && isSame) {
                        control.style.background = 'color-mix(in srgb, var(--accent) 15%, var(--input-bg))';
                    }
                });
            });
            
            document.addEventListener('focusout', function(e) {
                let active = e.target;
                if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
                
                let container = active.closest('.panel-card');
                if(!container) return;
                
                container.querySelectorAll('input[data-row]').forEach(inp => {
                    let control = inp.closest('.q-field__control');
                    if(control) control.style.background = '';
                });
            });
            }
            </script>
        ''')

    async def adjust_size(self, delta_m=0, delta_n=0):
        if delta_m > 0 and self.m >= 10:
            return
        if delta_m < 0 and self.m <= 1:
            return
        if delta_n > 0 and self.n >= 10:
            return
        if delta_n < 0 and self.n <= 1:
            return
            
        is_remove = (delta_m < 0 or delta_n < 0)
        is_add = (delta_m > 0 or delta_n > 0)
        
        if self.btn_m_dec: self.btn_m_dec.disable()
        if self.btn_m_inc: self.btn_m_inc.disable()
        if self.btn_n_dec: self.btn_n_dec.disable()
        if self.btn_n_inc: self.btn_n_inc.disable()

        if is_remove:
            target = f"[data-row='{self.m - 1}']" if delta_m < 0 else f"[data-col='{self.n - 1}']"
            idx_row = self.m - 1
            is_m = 'true' if delta_m < 0 else 'false'
            
            js_salida = f'''
                return new Promise(resolve => {{
                    let cells = document.querySelectorAll(`input{target}`);
                    const anims = [];
                    cells.forEach((input, i) => {{
                        let ctrl = input.closest('.q-field__control');
                        if (ctrl) {{
                            anims.push(ctrl.animate(
                                [{{opacity: 1, transform: 'scale(1)', filter: 'blur(0)'}},
                                 {{opacity: 0, transform: 'scale(0.85) translateY(-8px)', filter: 'blur(2px)'}}],
                                {{duration: 240, delay: i * 25, easing: 'cubic-bezier(0.32,0.72,0,1)', fill: 'forwards'}}
                            ).finished);
                        }}
                    }});
                    if ({is_m}) {{
                        let rowContainer = document.querySelector(`[data-grid-row="{idx_row}"]`);
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
            
        self.m += delta_m
        self.n += delta_n
        
        # Purgar caché fuera de rango
        self._cache_A = {(r, c): v for (r, c), v in self._cache_A.items() if r < self.m and c < self.n}
        self._cache_b = {r: v for r, v in self._cache_b.items() if r < self.m}
        
        self.entradas_A.clear()
        self.entradas_b.clear()
        self.generar_cuadricula()
        if self.on_data_change: self.on_data_change()
        
        if is_add:
            target = f"[data-row='{self.m - 1}']" if delta_m > 0 else f"[data-col='{self.n - 1}']"
            
            import asyncio
            await asyncio.sleep(0.05)
            
            js_entrada = f'''
                return new Promise(resolve => {{
                    let cells = document.querySelectorAll(`input{target}`);
                    const anims = [];
                    cells.forEach((input, i) => {{
                        let ctrl = input.closest('.q-field__control');
                        if (ctrl) {{
                            anims.push(ctrl.animate(
                                [{{opacity: 0, transform: 'scale(0.85) translateY(8px)', filter: 'blur(2px)'}},
                                 {{opacity: 1, transform: 'scale(1)', filter: 'blur(0)'}}],
                                {{duration: 240, delay: i * 25, easing: 'cubic-bezier(0.32,0.72,0,1)', fill: 'forwards'}}
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

    def build_grid_container(self):
        with ui.row().classes('w-full justify-between items-end mb-4 px-2'):
            self.shape_label = ui.html().classes('fs-small text-sec uppercase').style('letter-spacing: 0.08em; font-variant-numeric: tabular-nums; margin-bottom: -2px;')
        
        with ui.row().classes('w-full items-start no-wrap gap-2'):
            # Contenedor con scroll interno para la matriz
            self.contenedor_matriz = ui.column().classes('overflow-auto panel-card p-4 flex-1').style('max-height: 60vh;')
            
            # Controles inline de filas (Se añade color=None)
            from functools import partial
            with ui.column().classes('gap-2 mt-12 items-center justify-center mr-2'):
                self.btn_m_inc = ui.button(icon='add', on_click=partial(self.adjust_size, delta_m=1), color=None).classes('btn-neo-icon w-8 h-8 p-0').props('ripple=false').tooltip('Añadir Ecuación')
                self.btn_m_dec = ui.button(icon='remove', on_click=partial(self.adjust_size, delta_m=-1), color=None).classes('btn-neo-icon w-8 h-8 p-0').props('ripple=false').tooltip('Quitar Ecuación')

        # Controles inline de columnas (Se añade color=None)
        with ui.row().classes('w-full justify-center gap-2 mt-4'):
            self.btn_n_inc = ui.button(icon='add', on_click=partial(self.adjust_size, delta_n=1), color=None).classes('btn-neo-icon w-8 h-8 p-0').props('ripple=false').tooltip('Añadir Variable')
            self.btn_n_dec = ui.button(icon='remove', on_click=partial(self.adjust_size, delta_n=-1), color=None).classes('btn-neo-icon w-8 h-8 p-0').props('ripple=false').tooltip('Quitar Variable')
            
        self.generar_cuadricula()

    def generar_cuadricula(self):
        # Actualizar caché antes de destruir
        for i, fila in enumerate(self.entradas_A):
            for j, celda in enumerate(fila):
                if celda.value: self._cache_A[(i, j)] = celda.value
        for i, celda in enumerate(self.entradas_b):
            if celda.value: self._cache_b[i] = celda.value

        self.contenedor_matriz.clear()
        self.entradas_A.clear()
        self.entradas_b.clear()
        
        # Actualizar indicador de tipo de sistema
        shape_text = "Sistema Cuadrado" if self.m == self.n else "Sistema Rectangular"
        self.shape_label.content = f'{shape_text} <span style="color: var(--accent)">·</span> {self.m} &times; {self.n}'
        
        if self.btn_m_dec: 
            if self.m <= 1: self.btn_m_dec.disable()
            else: self.btn_m_dec.enable()
        if self.btn_m_inc: 
            if self.m >= 10: self.btn_m_inc.disable()
            else: self.btn_m_inc.enable()
        if self.btn_n_dec: 
            if self.n <= 1: self.btn_n_dec.disable()
            else: self.btn_n_dec.enable()
        if self.btn_n_inc: 
            if self.n >= 10: self.btn_n_inc.disable()
            else: self.btn_n_inc.enable()
        
        with self.contenedor_matriz:
            # Cabeceras Sticky (x₁, x₂, etc)
            with ui.row().classes('items-center gap-2 mb-2 no-wrap w-full z-10 bg-[var(--bg-panel)]').style('position: sticky; top: 0; min-width: max-content;'):
                for j in range(self.n):
                    # CORRECCIÓN: Se reemplaza ui.label() por ui.html() para permitir etiquetas <sub>
                    ui.html(f'x<sub>{j+1}</sub>').classes('w-20 text-center math-label').style('min-width: 80px;')
                ui.label('=').classes('w-8 text-center text-transparent') # Espaciador
                ui.label('b').classes('w-20 text-center math-label').style('min-width: 80px;')

            with ui.column().style('min-width: max-content;'):
                for i in range(self.m):
                    with ui.row().classes('items-center gap-2 mb-2 no-wrap').props(f'data-grid-row="{i}"'):
                        fila_A = []
                        for j in range(self.n):
                            val = self._cache_A.get((i, j), '')
                            
                            def update_cache_A(e, r=i, c=j):
                                self._cache_A[(r, c)] = e.value
                                if self.on_data_change: self.on_data_change()
                                
                            celda = ui.input(value=val, placeholder='0', on_change=update_cache_A).classes('matrix-input w-20').style('min-width: 80px;').props(f'data-row="{i}" data-col="{j}" borderless autocomplete="new-password" name="r{i}c{j}"')
                            fila_A.append(celda)
                            
                        self.entradas_A.append(fila_A)
                        ui.label('=').classes('w-8 text-center math-label text-xl')
                        
                        val_b = self._cache_b.get(i, '')
                        
                        def update_cache_b(e, r=i):
                            self._cache_b[r] = e.value
                            if self.on_data_change: self.on_data_change()
                            
                        celda_b = ui.input(value=val_b, placeholder='0', on_change=update_cache_b).classes('matrix-input w-20').style('min-width: 80px;').props(f'data-row="{i}" data-col="{self.n}" borderless autocomplete="new-password" name="r{i}cb"')
                        self.entradas_b.append(celda_b)

    def get_matrix_data(self):
        matrix_A_vals = [[(celda.value.strip() if celda.value else '0') for celda in fila] for fila in self.entradas_A]
        vector_b_vals = [(celda.value.strip() if celda.value else '0') for celda in self.entradas_b]
        return matrix_A_vals, vector_b_vals

    def is_strictly_empty(self):
        for fila in self.entradas_A:
            for celda in fila:
                if celda.value and str(celda.value).strip() != '': return False
        for celda in self.entradas_b:
            if celda.value and str(celda.value).strip() != '': return False
        return True

    def clear(self):
        self._cache_A.clear()
        self._cache_b.clear()
        for fila in self.entradas_A:
            for celda in fila: celda.value = ''
        for celda in self.entradas_b: celda.value = ''
        if self.on_data_change: self.on_data_change()

    def export_to_equations(self, preserve_shape: bool = False):
        """Genera una lista de strings de ecuaciones desde la matriz actual."""
        ecuaciones = []
        matrix_A, vector_b = self.get_matrix_data()
        
        from src.backend.utils.validators import MatrixValidator
        for i, row in enumerate(matrix_A):
            terms = []
            for j, val in enumerate(row):
                if val and val != '0':
                    success, num, _ = MatrixValidator.parse_number_exact(val)
                    if not success:
                        continue
                    
                    sign = "-" if val.startswith("-") else "+"
                    val_abs = val.lstrip("+-").strip()
                    
                    if val_abs == "1" or val_abs == "":
                        term = f"x{j+1}"
                    else:
                        term = f"{val_abs}x{j+1}"
                        
                    if not terms and sign == "+":
                        terms.append(term)
                    elif not terms and sign == "-":
                        terms.append(f"-{term}")
                    else:
                        terms.append(f"{sign} {term}")
                        
            if not terms:
                if vector_b[i] and vector_b[i] != '0':
                    ecuaciones.append(f"0x1 = {vector_b[i]}" if preserve_shape else f"0 = {vector_b[i]}")
                elif preserve_shape:
                    ecuaciones.append("0x1 = 0")
            else:
                eq_str = " ".join(terms) + f" = {vector_b[i]}"
                ecuaciones.append(eq_str)
                
        if preserve_shape and ecuaciones:
            import re
            used_vars = set()
            for eq in ecuaciones:
                for match in re.finditer(r'x(\d+)', eq):
                    used_vars.add(int(match.group(1)))
                    
            first_eq_parts = ecuaciones[0].split(' = ')
            if len(first_eq_parts) == 2:
                first_eq, b_part = first_eq_parts
                for j in range(self.n):
                    if (j + 1) not in used_vars:
                        if first_eq == "0":
                            first_eq = f"0x{j+1}"
                        elif first_eq == "":
                            first_eq = f"0x{j+1}"
                        else:
                            first_eq += f" + 0x{j+1}"
                ecuaciones[0] = f"{first_eq} = {b_part}"
                
        return ecuaciones

    def import_from_parsed(self, parsed_matrix):
        """Reconstruye la cuadrícula desde una matriz parseada."""
        if parsed_matrix.rows > 10 or (parsed_matrix.cols - 1) > 10:
            ui.notify("El sistema excede el límite de visualización (10x10).", type='warning')
            return
            
        self.m = parsed_matrix.rows
        self.n = parsed_matrix.cols - 1
        
        # Llenar el caché primero para que generar_cuadricula lo use
        self._cache_A.clear()
        self._cache_b.clear()
        
        for i in range(self.m):
            for j in range(self.n):
                s = str(parsed_matrix.data[i][j])
                if s != "0":
                    self._cache_A[(i, j)] = s
                
            s = str(parsed_matrix.data[i][-1])
            if s != "0":
                self._cache_b[i] = s
            
        # Descartar los widgets viejos: generar_cuadricula() copia sus valores
        # al caché antes de reconstruir y pisaría lo recién importado.
        self.entradas_A.clear()
        self.entradas_b.clear()
        self.generar_cuadricula()
        if self.on_data_change:
            self.on_data_change()