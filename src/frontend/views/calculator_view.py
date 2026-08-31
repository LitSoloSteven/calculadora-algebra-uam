import json
from nicegui import ui
from src.frontend.controllers.controllers_matrix import MatrixController

class CalculatorUI:
    def __init__(self):
        self.entradas_A = []
        self.entradas_b = []
        self.m_input = None
        self.n_input = None
        self.contenedor_matriz = None
        self.contenedor_resultados = None

    def generar_cuadricula(self):
        # 1. Respaldar los valores actuales de la matriz antes de borrar la cuadrícula
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
                    with ui.row().classes('items-center gap-1 mb-2 no-wrap justify-center'):
                        fila_A = []
                        for j in range(columnas):
                            # 2. Recuperar el valor guardado si la coordenada existía previamente
                            val = backup_A[i][j] if i < len(backup_A) and j < len(backup_A[i]) else ''
                            
                            # Usamos data-row y data-col nativos para que Quasar no los sobreescriba
                            celda = ui.input(value=val, placeholder='0').classes('w-16').props(f'data-row="{i}" data-col="{j}"')
                            fila_A.append(celda)
                            
                            texto_var = f'x_{{{j+1}}}'
                            if j < columnas - 1:
                                texto_var += ' +'
                                
                            ui.label(f'${texto_var}$').classes('text-lg mr-2 mt-1')
                            
                        self.entradas_A.append(fila_A)
                        
                        ui.label('=').classes('text-2xl font-bold mx-2 text-gray-500')
                        
                        # Recuperar valor y asignar la columna final al vector de resultados
                        val_b = backup_b[i] if i < len(backup_b) else ''
                        celda_b = ui.input(value=val_b, placeholder='0').classes('w-16 bg-blue-50').props(f'data-row="{i}" data-col="{columnas}"')
                        self.entradas_b.append(celda_b)
                        
        ui.run_javascript('if (window.MathJax) { MathJax.typesetPromise(); }')

    def limpiar_pantalla(self):
        self.contenedor_resultados.clear()
        self.entradas_A.clear()
        self.entradas_b.clear()
        self.m_input.value = 3
        self.n_input.value = 3
        self.generar_cuadricula()

    def resolver_sistema(self):
        self.contenedor_resultados.clear()
        
        matrix_A_vals = [[(celda.value.strip() if celda.value else '0') for celda in fila] for fila in self.entradas_A]
        vector_b_vals = [(celda.value.strip() if celda.value else '0') for celda in self.entradas_b]
        
        payload_dict = {"matrix_A": matrix_A_vals, "vector_b": vector_b_vals}
        json_payload = json.dumps(payload_dict)
        
        respuesta_json_str = MatrixController.process_system(json_payload)
        respuesta = json.loads(respuesta_json_str)
        
        with self.contenedor_resultados:
            if respuesta.get("status") == "error":
                ui.label(respuesta["message"]).classes('text-red-600 font-bold')
                return
                
            ui.label('Clasificación: ' + respuesta["classification"]).classes('text-lg font-bold text-blue-900 mt-4 text-center')
            
            if respuesta.get("solution"):
                with ui.row().classes('gap-4 my-2 justify-center w-full'):
                    for idx, val in enumerate(respuesta["solution"]):
                        ui.label(f'x{idx+1} = {val}').classes('font-mono text-lg p-2 bg-green-50 rounded border')
                        
            if respuesta.get("intermediate_steps_latex"):
                ui.label('Procedimiento:').classes('font-bold mt-4 text-lg w-full text-center')
                for paso in respuesta["intermediate_steps_latex"]:
                    with ui.card().classes('w-full items-center p-4 my-2 bg-gray-50'):
                        ui.label(paso["descripcion"]).classes('text-md font-semibold text-gray-700 mb-1')
                        ui.label(f'$$ {paso["matriz"]} $$').classes('text-xl overflow-x-auto max-w-full')
                        
            if respuesta.get("solution"):
                ui.label('Traducción de matriz final a ecuaciones:').classes('font-bold mt-4 text-lg w-full text-center')
                with ui.card().classes('w-full p-4 bg-yellow-50 mb-4 items-center'):
                    ui.label("A partir de la matriz escalonada, reconstruimos y despejamos el sistema:").classes('mb-2 text-gray-700 text-center')
                    for idx in reversed(range(len(respuesta["solution"]))):
                        ui.label(f'$$ 1x_{{{idx+1}}} = {respuesta["solution"][idx]} $$').classes('text-lg')
                    
            if respuesta.get("verification_steps_latex"):
                ui.label('Comprobación').classes('font-bold mt-4 w-full text-center')
                with ui.card().classes('w-full p-4 bg-purple-50 items-center'):
                    for paso in respuesta["verification_steps_latex"]:
                        ui.label(f'$$ {paso} $$').classes('text-lg my-1')
                        
            ui.run_javascript('if (window.MathJax) { MathJax.typesetPromise(); }')

    def build(self):
        ui.colors(primary='#005596')
        
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
                    // Bloquea salto de celda si el usuario está navegando dentro del texto de la ecuación
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

            // Auto-seleccionar el texto al enfocar una celda (clic o teclado)
            document.addEventListener('focusin', function(e) {
                let active = e.target;
                if (active.tagName === 'INPUT' && active.dataset.row !== undefined) {
                    setTimeout(() => active.select(), 10);
                }
            });
            </script>
            <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" id="MathJax-script" async></script>
        ''')
        
        with ui.column().classes('w-full max-w-5xl mx-auto p-6 items-center'):
            ui.label('Calculadora de Álgebra Lineal').classes('text-3xl font-bold text-primary mb-2 text-center')
            
            with ui.row().classes('gap-6 items-center mb-6 p-4 border rounded bg-gray-50 justify-center w-full max-w-md'):
                self.m_input = ui.number(label='Ecuaciones', value=3, min=1, max=10, format='%.0f', on_change=self.generar_cuadricula).classes('w-32')
                self.n_input = ui.number(label='Variables', value=3, min=1, max=10, format='%.0f', on_change=self.generar_cuadricula).classes('w-32')
                
            self.contenedor_matriz = ui.column().classes('mb-6 w-full overflow-x-auto')
            
            with ui.row().classes('w-full max-w-sm mx-auto mb-8 gap-4 justify-center'):
                ui.button('A/C', on_click=self.limpiar_pantalla, color='red', icon='delete').classes('w-24')
                ui.button('Resolver Sistema', on_click=self.resolver_sistema, icon='calculate').classes('flex-1')
                
            self.contenedor_resultados = ui.column().classes('w-full items-center')
            
            self.generar_cuadricula()