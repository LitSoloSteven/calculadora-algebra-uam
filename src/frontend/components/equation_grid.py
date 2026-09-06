from nicegui import ui

class EquationGrid:
    def __init__(self, default_m=3, default_n=3):
        self.entradas_A = []
        self.entradas_b = []
        self.m = default_m
        self.n = default_n
        self.contenedor_matriz = None
        self.shape_label = None

    def inject_scripts(self):
        ui.add_head_html('''
            <script>
            // Navegación con teclado
            document.addEventListener('keydown', function(e) {
                let active = document.activeElement;
                if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
                let r = parseInt(active.dataset.row), c = parseInt(active.dataset.col);
                if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
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
                let rows = pasteData.trim().split('\\n');
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
            </script>
        ''')

    def adjust_size(self, delta_m=0, delta_n=0):
        if 1 <= self.m + delta_m <= 10: self.m += delta_m
        if 1 <= self.n + delta_n <= 10: self.n += delta_n
        self.generar_cuadricula()

    def build_grid_container(self):
        with ui.row().classes('w-full justify-between items-end mb-4 px-2'):
            self.shape_label = ui.label().classes('text-sm font-semibold tracking-wide').style('color: var(--text-sec);')
        
        with ui.row().classes('w-full items-start no-wrap gap-2'):
            # Contenedor con scroll interno para la matriz
            self.contenedor_matriz = ui.column().classes('overflow-auto panel-card p-4 flex-1').style('max-height: 60vh;')
            
            # Controles inline de filas (Se añade color=None)
            with ui.column().classes('gap-2 mt-12'):
                ui.button(icon='add', on_click=lambda: self.adjust_size(delta_m=1), color=None).classes('btn-ghost w-8 h-8 p-0').props('ripple=false').tooltip('Añadir Ecuación')
                ui.button(icon='remove', on_click=lambda: self.adjust_size(delta_m=-1), color=None).classes('btn-ghost w-8 h-8 p-0').props('ripple=false').tooltip('Eliminar Ecuación')

        # Controles inline de columnas (Se añade color=None)
        with ui.row().classes('w-full justify-center gap-2 mt-2'):
            ui.button(icon='add', on_click=lambda: self.adjust_size(delta_n=1), color=None).classes('btn-ghost w-8 h-8 p-0').props('ripple=false').tooltip('Añadir Variable')
            ui.button(icon='remove', on_click=lambda: self.adjust_size(delta_n=-1), color=None).classes('btn-ghost w-8 h-8 p-0').props('ripple=false').tooltip('Eliminar Variable')
            
        self.generar_cuadricula()

    def generar_cuadricula(self):
        backup_A = [[c.value for c in fila] for fila in self.entradas_A] if self.entradas_A else []
        backup_b = [c.value for c in self.entradas_b] if self.entradas_b else []

        self.contenedor_matriz.clear()
        self.entradas_A.clear()
        self.entradas_b.clear()
        
        # Actualizar indicador de tipo de sistema
        shape_text = "Sistema Cuadrado" if self.m == self.n else "Sistema Rectangular"
        self.shape_label.set_text(f'{shape_text} ({self.m} ecuaciones × {self.n} variables)')
        
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
                    with ui.row().classes('items-center gap-2 mb-2 no-wrap'):
                        fila_A = []
                        for j in range(self.n):
                            val = backup_A[i][j] if i < len(backup_A) and j < len(backup_A[i]) else ''
                            celda = ui.input(value=val, placeholder='0').classes('matrix-input w-20').style('min-width: 80px;').props(f'data-row="{i}" data-col="{j}" borderless')
                            fila_A.append(celda)
                            
                        self.entradas_A.append(fila_A)
                        ui.label('=').classes('w-8 text-center math-label text-xl')
                        
                        val_b = backup_b[i] if i < len(backup_b) else ''
                        celda_b = ui.input(value=val_b, placeholder='0').classes('matrix-input w-20').style('min-width: 80px;').props(f'data-row="{i}" data-col="{self.n}" borderless')
                        self.entradas_b.append(celda_b)

    def get_matrix_data(self):
        matrix_A_vals = [[(celda.value.strip() if celda.value else '0') for celda in fila] for fila in self.entradas_A]
        vector_b_vals = [(celda.value.strip() if celda.value else '0') for celda in self.entradas_b]
        return matrix_A_vals, vector_b_vals

    def clear(self):
        for fila in self.entradas_A:
            for celda in fila: celda.value = ''
        for celda in self.entradas_b: celda.value = ''