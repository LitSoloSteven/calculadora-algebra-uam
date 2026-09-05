from nicegui import ui

class EquationGrid:
    def __init__(self, default_m=3, default_n=3):
        self.entradas_A = []
        self.entradas_b = []
        self.default_m = default_m
        self.default_n = default_n
        self.m_input = None
        self.n_input = None
        self.contenedor_matriz = None

    def inject_scripts(self):
        ui.add_head_html('''
            <script>
            window.MathJax = {
              tex: { inlineMath: [['$', '$'], ['\\\\(', '\\\\)']], displayMath: [['$$', '$$']] }
            };
            document.addEventListener('keydown', function(e) {
                let active = document.activeElement;
                if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
                let r = parseInt(active.dataset.row);
                let c = parseInt(active.dataset.col);
                if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                    if (e.key === 'ArrowLeft' && active.selectionStart > 0 && active.selectionStart === active.selectionEnd) return;
                    if (e.key === 'ArrowRight' && active.selectionEnd < active.value.length && active.selectionStart === active.selectionEnd) return;
                    if (e.key === 'ArrowRight') c++;
                    if (e.key === 'ArrowLeft') c--;
                    if (e.key === 'ArrowDown') r++;
                    if (e.key === 'ArrowUp') r--;
                } else if (e.key === 'Enter') {
                    r++;
                } else {
                    return;
                }
                let nextInput = document.querySelector(`input[data-row="${r}"][data-col="${c}"]`);
                if (nextInput) {
                    nextInput.focus();
                    setTimeout(() => nextInput.select(), 10);
                    e.preventDefault();
                }
            });
            </script>
            <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" id="MathJax-script" async></script>
        ''')

    def build_controls(self):
        with ui.row().classes('gap-8 items-center mb-6 p-6 justify-center w-full max-w-md neu-flat'):
            self.m_input = ui.number(label='Ecuaciones', value=self.default_m, min=1, max=10, format='%.0f', on_change=self.generar_cuadricula).classes('w-32 neu-pressed px-2')
            self.n_input = ui.number(label='Variables', value=self.default_n, min=1, max=10, format='%.0f', on_change=self.generar_cuadricula).classes('w-32 neu-pressed px-2')

    def build_grid_container(self):
        self.contenedor_matriz = ui.column().classes('mb-6 w-full overflow-x-auto neu-flat p-6')
        self.generar_cuadricula()

    def generar_cuadricula(self):
        backup_A = [[c.value for c in fila] for fila in self.entradas_A]
        backup_b = [c.value for c in self.entradas_b]

        self.contenedor_matriz.clear()
        self.entradas_A.clear()
        self.entradas_b.clear()
        
        filas = int(self.m_input.value)
        columnas = int(self.n_input.value)
        
        with self.contenedor_matriz:
            with ui.column().classes('mx-auto'):
                for i in range(filas):
                    with ui.row().classes('items-center gap-2 mb-3 no-wrap justify-center'):
                        fila_A = []
                        for j in range(columnas):
                            val = backup_A[i][j] if i < len(backup_A) and j < len(backup_A[i]) else ''
                            # Colores dependientes del theme
                            celda = ui.input(value=val, placeholder='0').classes('w-16 neu-pressed').props(f'data-row="{i}" data-col="{j}" borderless input-class="text-center font-bold"')
                            fila_A.append(celda)
                            
                            texto_var = f'x_{{{j+1}}}'
                            if j < columnas - 1:
                                texto_var += ' +'
                            ui.label(f'${texto_var}$').classes('text-lg mr-1 mt-1 font-bold')
                            
                        self.entradas_A.append(fila_A)
                        ui.label('=').classes('text-2xl font-bold mx-2')
                        
                        val_b = backup_b[i] if i < len(backup_b) else ''
                        celda_b = ui.input(value=val_b, placeholder='0').classes('w-16 neu-pressed').props(f'data-row="{i}" data-col="{columnas}" borderless input-class="text-center font-bold"')
                        self.entradas_b.append(celda_b)
                        
        ui.run_javascript('if (window.MathJax) { MathJax.typesetPromise(); }')

    def get_matrix_data(self):
        matrix_A_vals = [[(celda.value.strip() if celda.value else '0') for celda in fila] for fila in self.entradas_A]
        vector_b_vals = [(celda.value.strip() if celda.value else '0') for celda in self.entradas_b]
        return matrix_A_vals, vector_b_vals

    def clear(self):
        self.entradas_A.clear()
        self.entradas_b.clear()
        self.m_input.value = self.default_m
        self.n_input.value = self.default_n
        self.generar_cuadricula()