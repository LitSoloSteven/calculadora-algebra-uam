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
            'ui_container': None
        }
        self.render_all_matrices()

    def remove_matrix(self, name):
        if name in self.matrices:
            del self.matrices[name]
            self.render_all_matrices()

    def adjust_size(self, name, delta_m=0, delta_n=0):
        if name not in self.matrices: return
        mat = self.matrices[name]
        
        for r, fila in enumerate(mat['entradas']):
            for c, celda in enumerate(fila):
                if celda.value: mat['cache'][(r, c)] = celda.value

        if 1 <= mat['m'] + delta_m <= 10: mat['m'] += delta_m
        if 1 <= mat['n'] + delta_n <= 10: mat['n'] += delta_n
        
        self.render_matrix_grid(name)

    def render_matrix_grid(self, name):
        mat = self.matrices[name]
        if not mat['ui_container']: return
        
        mat['ui_container'].clear()
        mat['entradas'].clear()
        
        with mat['ui_container']:
            with ui.column().style('min-width: max-content;'):
                for i in range(mat['m']):
                    with ui.row().classes('items-center gap-2 mb-2 no-wrap'):
                        fila_UI = []
                        for j in range(mat['n']):
                            val = mat['cache'].get((i, j), '')
                            
                            def update_cache(e, r=i, c=j, matrix_name=name):
                                self.matrices[matrix_name]['cache'][(r, c)] = e.value
                                
                            celda = ui.input(value=val, placeholder='0', on_change=update_cache).classes('matrix-input w-20').style('min-width: 80px;').props(f'data-matrix-id="{name}" data-matrix-row="{i}" data-matrix-col="{j}" borderless autocomplete="new-password" name="{name}_r{i}c{j}"')
                            fila_UI.append(celda)
                        mat['entradas'].append(fila_UI)

    def render_all_matrices(self):
        if not self.container: return
        self.container.clear()
        
        with self.container:
            for name in sorted(self.matrices.keys()):
                mat = self.matrices[name]
                with ui.column().classes('w-full panel-card p-4 mb-6'):
                    with ui.row().classes('w-full justify-between items-center mb-4'):
                        ui.label(f'Matriz {name}').classes('text-lg font-bold text-main')
                        
                        # Controles de dimensiones
                        with ui.row().classes('gap-4 items-center flex-wrap'):
                            with ui.row().classes('gap-1 items-center'):
                                ui.label('Filas:').classes('text-sm text-sec mr-1')
                                ui.button(icon='remove', on_click=lambda e, n=name: self.adjust_size(n, delta_m=-1), color=None).classes('btn-neo-icon w-6 h-6 p-0 min-h-0 text-xs').props('ripple=false')
                                ui.label(str(mat['m'])).classes('font-bold w-4 text-center')
                                ui.button(icon='add', on_click=lambda e, n=name: self.adjust_size(n, delta_m=1), color=None).classes('btn-neo-icon w-6 h-6 p-0 min-h-0 text-xs').props('ripple=false')
                            
                            with ui.row().classes('gap-1 items-center'):
                                ui.label('Cols:').classes('text-sm text-sec mr-1')
                                ui.button(icon='remove', on_click=lambda e, n=name: self.adjust_size(n, delta_n=-1), color=None).classes('btn-neo-icon w-6 h-6 p-0 min-h-0 text-xs').props('ripple=false')
                                ui.label(str(mat['n'])).classes('font-bold w-4 text-center')
                                ui.button(icon='add', on_click=lambda e, n=name: self.adjust_size(n, delta_n=1), color=None).classes('btn-neo-icon w-6 h-6 p-0 min-h-0 text-xs').props('ripple=false')

                            ui.button(icon='delete', on_click=lambda e, n=name: self.remove_matrix(n), color=None).classes('btn-ghost w-8 h-8 p-0 text-red-500 ml-2').props('ripple=false').tooltip('Eliminar Matriz')

                    mat['ui_container'] = ui.column().classes('overflow-auto w-full max-h-[300px]')
                    self.render_matrix_grid(name)

    def build_container(self):
        with ui.row().classes('w-full justify-end mb-4'):
            ui.button('+ Añadir Matriz', icon='add', on_click=self.add_matrix, color=None).classes('btn-ghost py-1 px-4 text-sm').props('ripple=false')
            
        self.container = ui.column().classes('w-full')
        
        # Valores iniciales si está vacío
        if not self.matrices:
            self.matrices['A'] = {'m': 3, 'n': 3, 'entradas': [], 'cache': {}, 'ui_container': None}
            self.matrices['B'] = {'m': 3, 'n': 3, 'entradas': [], 'cache': {}, 'ui_container': None}
            
        self.render_all_matrices()

    def get_matrices_dict(self):
        """Devuelve un diccionario de dicts con raw_data, de forma que el controller las convierta a Matrix"""
        result = {}
        for name, mat in self.matrices.items():
            parsed_data = []
            for r in range(mat['m']):
                row_vals = []
                for c in range(mat['n']):
                    val_str = mat['cache'].get((r, c), '0')
                    if not str(val_str).strip():
                        val_str = '0'
                    
                    success, num, msg = MatrixValidator.parse_number(val_str)
                    if not success:
                        raise ValueError(f"Error en Matriz {name}, celda [{r+1},{c+1}]: {msg}")
                    row_vals.append(num)
                parsed_data.append(row_vals)
                
            result[name] = {
                "rows": mat['m'],
                "cols": mat['n'],
                "data": parsed_data
            }
        return result
