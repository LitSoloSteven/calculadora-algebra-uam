import json
import asyncio
from nicegui import ui
from src.frontend.controllers.linear_systems.controller_gauss import MatrixController
from src.frontend.controllers.linear_systems.controller_gauss_jordan import GaussJordanController
from src.frontend.components.navbar import create_navbar
from src.frontend.components.equation_grid import EquationGrid
from src.frontend.components.calculator import CalculatorPanel
from src.backend.utils.parsers import SystemParser
from src.frontend.app import CHART_PALETTE, CHART_MARKER_LIGHT, CHART_MARKER_BORDER, CHART_GRID_COLOR, CHART_ZERO_COLOR
from src.frontend.components.ai_panel import AIPanel

class LinearSystemsUI:
    def __init__(self, initial_method='gauss'):
        self.grid = EquationGrid()
        self.calculator = CalculatorPanel()
        self.contenedor_resultados = None
        self.mode_tabs = None
        self.method_tabs = None
        self.initial_method = initial_method
        
        # Estado del modo ecuaciones
        self.num_ecuaciones = 3
        self.ecuaciones_inputs = []
        self.contenedor_ecuaciones_lista = None
        
        # Tools Panel
        self.historial = []
        self.preview_task = None
        self.preview_container = None
        self.historial_container = None

    def add_eq(self):
        if self.num_ecuaciones < 10:
            self.num_ecuaciones += 1
            self.render_ecuaciones()

    def remove_eq(self):
        if self.num_ecuaciones > 1:
            self.num_ecuaciones -= 1
            self.render_ecuaciones()

    def render_ecuaciones(self):
        backup_vals = [inp.value for inp in self.ecuaciones_inputs]
        if self.contenedor_ecuaciones_lista:
            self.contenedor_ecuaciones_lista.clear()
            self.ecuaciones_inputs.clear()
            with self.contenedor_ecuaciones_lista:
                for i in range(self.num_ecuaciones):
                    val = backup_vals[i] if i < len(backup_vals) else ''
                    with ui.row().classes('w-full items-center gap-3 no-wrap mb-3'):
                        ui.label(f'{i+1}.').classes('font-bold text-sec w-6 text-right')
                        inp = ui.input(value=val, placeholder=f'Ej. 2x + 3y = {i*2 + 4}', on_change=self.update_sync_buttons).classes('matrix-input flex-1').props(f'borderless autocomplete="new-password" name="eq{i}"')
                        self.ecuaciones_inputs.append(inp)

    def sync_from_matrix(self):
        eqs = self.grid.export_to_equations()
        self.num_ecuaciones = max(len(eqs), 1)
        
        if self.contenedor_ecuaciones_lista:
            self.contenedor_ecuaciones_lista.clear()
            self.ecuaciones_inputs.clear()
            with self.contenedor_ecuaciones_lista:
                for i in range(self.num_ecuaciones):
                    val = eqs[i] if i < len(eqs) else ''
                    with ui.row().classes('w-full items-center gap-3 no-wrap mb-3'):
                        ui.label(f'{i+1}.').classes('font-bold text-sec w-6 text-right')
                        inp = ui.input(value=val, placeholder=f'Ej. 2x + 3y = {i*2 + 4}', on_change=self.update_sync_buttons).classes('matrix-input flex-1').props(f'borderless autocomplete="new-password" name="eq{i}"')
                        self.ecuaciones_inputs.append(inp)
        
        ui.notify('Sincronizado desde Matriz', type='positive', position='top')

    def sync_from_equations(self):
        lineas = [inp.value or "" for inp in self.ecuaciones_inputs]
        raw_text = "\n".join(lineas)
        success, parsed_matrix, variables, msg = SystemParser.parse_system(raw_text)
        
        if not success:
            ui.notify(f'Error al sincronizar: {msg}', type='negative', position='top')
            return
            
        self.grid.import_from_parsed(parsed_matrix, variables)
        ui.notify('Sincronizado desde Ecuaciones', type='positive', position='top')

    def is_matriz_empty(self):
        matrix_A, vector_b = self.grid.get_matrix_data()
        for row in matrix_A:
            for val in row:
                if val and str(val).strip() != '' and str(val).strip() != '0': return False
        for val in vector_b:
            if val and str(val).strip() != '' and str(val).strip() != '0': return False
        return True

    def is_ecuaciones_empty(self):
        for inp in self.ecuaciones_inputs:
            if inp.value and str(inp.value).strip() != '' and str(inp.value).strip() != '0': return False
        return True

    def is_empty(self):
        if self.mode_tabs.value == 'Matriz':
            return self.is_matriz_empty()
        else:
            return self.is_ecuaciones_empty()
            
    def is_strictly_empty(self):
        if self.mode_tabs.value == 'Matriz':
            return self.grid.is_strictly_empty()
        else:
            for inp in self.ecuaciones_inputs:
                if inp.value and str(inp.value).strip() != '': return False
            return True
            
    def update_sync_buttons(self, _=None):
        if hasattr(self, 'sync_btn_from_eq') and self.sync_btn_from_eq:
            self.sync_btn_from_eq.set_visibility(not self.is_ecuaciones_empty())
        if hasattr(self, 'sync_btn_from_matrix') and self.sync_btn_from_matrix:
            self.sync_btn_from_matrix.set_visibility(not self.is_matriz_empty())
            
    def _trigger_live_preview(self):
        if self.preview_task: self.preview_task.cancel()
        self.preview_task = asyncio.create_task(self._update_preview())
        
    async def _update_preview(self):
        await asyncio.sleep(0.3)
        if not self.preview_container: return
        
        self.preview_container.clear()
        with self.preview_container:
            matrix_A, vector_b = self.grid.get_matrix_data()
            if not matrix_A or len(matrix_A) == 0 or len(matrix_A[0]) == 0:
                ui.label('La matriz está vacía.').classes('text-sec italic text-sm mt-4 text-center')
                return
                
            m = len(matrix_A)
            n = len(matrix_A[0])
            
            from src.backend.utils.validators import MatrixValidator
            def sanitize(val):
                if not val: return '0'
                success, _, _ = MatrixValidator.parse_number(val)
                if not success: return r"\color{gray}{?}"
                return val
            
            # Construir LaTeX para matriz aumentada
            latex_lines = []
            for i, row in enumerate(matrix_A):
                row_strs = [sanitize(val) for val in row]
                b_val = sanitize(vector_b[i] if i < len(vector_b) else '0')
                latex_lines.append(" & ".join(row_strs) + f" & {b_val}")
                
            spec = "c" * n + "|c"
            matrix_tex = rf"\left[ \begin{{array}}{{{spec}}} " + r" \\ ".join(latex_lines) + r" \end{array} \right]"
            
            ui.html(f'<div id="preview-matrix" class="math-scroll-container math-label text-lg mb-6 w-full text-center">$$ {matrix_tex} $$</div>')
            
            if m * n > 48:
                ui.label('Sistema demasiado grande para vista previa en ecuaciones.').classes('text-sec italic text-sm mt-4 text-center')
                ui.run_javascript("typesetMathWhenReady(['preview-matrix']);")
                return
            
            # Construir LaTeX para sistema de ecuaciones
            eqs = self.grid.export_to_equations()
            if not eqs:
                ui.label('No hay ecuaciones válidas.').classes('text-sec italic text-sm mt-4 text-center')
                ui.run_javascript("typesetMathWhenReady(['preview-matrix']);")
                return
                
            import re
            eqs_tex = r" \\ ".join(eqs)
            eqs_tex = re.sub(r'\bx(\d+)\b', r'x_{\1}', eqs_tex)
            system_tex = r" \begin{cases} " + eqs_tex + r" \end{cases} "
            
            ui.html(f'<div id="preview-system" class="math-scroll-container math-label text-lg w-full text-center">$$ {system_tex} $$</div>')
            
            ui.run_javascript("typesetMathWhenReady(['preview-matrix', 'preview-system']);")

    def _add_to_history(self, matrix_A, vector_b, m, n, status, method):
        import time
        self.historial.insert(0, {
            'matrix_A': matrix_A,
            'vector_b': vector_b,
            'm': m,
            'n': n,
            'status': status,
            'method': method,
            'time': time.strftime("%H:%M")
        })
        if len(self.historial) > 5:
            self.historial.pop()
        self._render_history()
        
    def _render_history(self):
        if not self.historial_container: return
        self.historial_container.clear()
        
        with self.historial_container:
            if not self.historial:
                ui.label('No hay sistemas resueltos en esta sesión.').classes('text-sec italic text-sm mt-4 text-center')
                return
                
            for h in self.historial:
                with ui.column().classes('panel-card p-4 w-full mb-3 gap-2 border border-[var(--border-input)]'):
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.badge(f"{h['m']}×{h['n']}", color=None).classes('badge-success font-mono')
                        ui.label(h['time']).classes('text-xs text-sec')
                    
                    ui.label(f"Método: {h['method'].replace('-', ' ').title()}").classes('text-sm font-bold text-main')
                    
                    status_class = 'text-[var(--accent)]' if h['status'] == 'UNIQUE_SOLUTION' else ('text-warning' if h['status'] == 'INFINITE_SOLUTIONS' else 'text-[var(--error)]')
                    status_text = 'Solución Única' if h['status'] == 'UNIQUE_SOLUTION' else ('Infinitas Soluciones' if h['status'] == 'INFINITE_SOLUTIONS' else 'Sin Solución' if h['status'] == 'NO_SOLUTION' else 'Error')
                    
                    ui.label(status_text).classes(f'text-xs {status_class} font-bold')
                    
                    ui.button('Restaurar', on_click=lambda e, data=h: self._restore_history(data), color=None).classes('btn-ghost text-xs w-full mt-2').props('ripple=false')

    def _restore_history(self, data):
        self.grid.clear()
        self.grid.m = data['m']
        self.grid.n = data['n']
        
        self.grid._cache_A.clear()
        self.grid._cache_b.clear()
        for i, row in enumerate(data['matrix_A']):
            for j, val in enumerate(row):
                if val != '0': self.grid._cache_A[(i, j)] = val
        for i, val in enumerate(data['vector_b']):
            if val != '0': self.grid._cache_b[i] = val
            
        self.grid.generar_cuadricula()
        self._trigger_live_preview()
        
        ui.notify('Matriz restaurada', type='positive')

    async def confirmar_limpieza(self):
        if self.is_empty():
            ui.notify('El sistema ya está vacío', type='warning', position='top')
            return
            
        with ui.dialog() as dialog, ui.card().classes('panel-card no-shadow p-6 min-w-[300px]'):
            ui.label('¿Vaciar datos?').classes('text-xl font-bold mb-4')
            ui.label('Se animarán y eliminarán los datos.').classes('text-sm text-sec mb-6')
            with ui.row().classes('w-full justify-end gap-3'):
                ui.button('Cancelar', on_click=dialog.close, color=None).classes('btn-ghost px-4').props('ripple=false')
                ui.button('Limpiar', on_click=lambda: self.ejecutar_animacion_limpieza(dialog), color=None).classes('btn-primary px-4').style('background: var(--error); color: white;').props('ripple=false')
        dialog.open()

    async def ejecutar_animacion_limpieza(self, dialog):
        dialog.close()
        ui.run_javascript('animateGarbageCollection()')
        await asyncio.sleep(0.8)
        self.limpiar_todo()

    def limpiar_todo(self):
        self.grid.clear()
        for inp in self.ecuaciones_inputs:
            inp.value = ''
        self.reset_resultados()

    def reset_resultados(self):
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.icon('calculate', size='4rem').classes('text-placeholder mb-4')
            ui.label('Listo para resolver').classes('text-xl font-bold text-main')
            ui.label('Ingresá las ecuaciones o la matriz y presioná Resolver').classes('text-sm text-sec mt-2 text-center')

    async def resolver_sistema(self, sender):
        if self.is_strictly_empty():
            self.reset_resultados()
            with self.contenedor_resultados:
                self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-warning mb-4 w-fit'):
                    ui.icon('warning_amber', size='sm')
                    ui.label('Ingresá al menos un valor antes de resolver').classes('font-bold')
            ui.run_javascript("setTimeout(() => { const el = document.getElementById('resultados-container'); if(el) el.scrollIntoView({behavior: 'smooth', block: 'start'}) }, MOTION.fast);")
            return
            
        btn = sender
        btn.props('loading=true').classes('w-full max-w-[200px]')
        await asyncio.sleep(0.1) 
        
        self.contenedor_resultados.clear()

        # Extraer datos según la pestaña activa
        variables = None
        if self.mode_tabs.value == 'Matriz':
            matrix_A_vals, vector_b_vals = self.grid.get_matrix_data()
            if matrix_A_vals and len(matrix_A_vals) > 0:
                variables = [f"x{j+1}" for j in range(len(matrix_A_vals[0]))]
            else:
                variables = []
        else:
            lineas = [inp.value or "" for inp in self.ecuaciones_inputs]
            raw_text = "\n".join(lineas)
            success, parsed_matrix, variables, msg = SystemParser.parse_system(raw_text)
            
            if not success:
                with self.contenedor_resultados:
                    self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
                    with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                        ui.icon('close', size='sm')
                        ui.label(msg).classes('font-bold')
                btn.props('loading=false')
                return
            
            matrix_A_vals = [[str(val) for val in row[:-1]] for row in parsed_matrix.data]
            vector_b_vals = [str(row[-1]) for row in parsed_matrix.data]

        payload_dict = {"matrix_A": matrix_A_vals, "vector_b": vector_b_vals, "variables": variables}
        
        # Llamar al controller basado en el método seleccionado
        if self.method_tabs.value == 'gauss':
            respuesta_json_str = MatrixController.process_system(json.dumps(payload_dict))
        else:
            respuesta_json_str = GaussJordanController.process_system(json.dumps(payload_dict))
            
        respuesta = json.loads(respuesta_json_str)
        
        # Animación del panel de resultados (Slide Up & Fade In)
        self.contenedor_resultados.classes(add='animate-slide-up')
        
        with self.contenedor_resultados:
            self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
            
            status = respuesta.get("status")
            classification_msg = respuesta.get("classification") or respuesta.get("message", "")
            
            is_error = str(status).upper() == "ERROR"
            
            if is_error:
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                    ui.icon('close', size='sm')
                    ui.label(classification_msg).classes('font-bold')
            elif status == "NO_SOLUTION":
                with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                    ui.icon('close', size='sm')
                    ui.label("Sin solución").classes('font-bold')
            else:
                is_unique = (status == "UNIQUE_SOLUTION")
                badge_class = 'badge-success' if is_unique else 'badge-warning'
                icon_str = 'check' if is_unique else 'warning_amber'
                
                texto_corto = "Solución única" if is_unique else "Infinitas soluciones"
                
                with ui.row().classes('w-full items-center gap-3 mb-4 flex-wrap'):
                    # Bloque de estatus
                    with ui.row().classes(f'items-center gap-2 px-4 py-2 {badge_class}'):
                        ui.icon(icon_str, size='sm')
                        badge_id = f"badge-{id(texto_corto)}"
                        ui.html(f'<b id="{badge_id}"></b>').classes('math-label')
                        ui.timer(0.05, lambda t=texto_corto, bid=badge_id: ui.run_javascript(f'typewriterEffect("{bid}", {json.dumps(t)}, 25)'), once=True)
                    
                    # Bloques individuales por variable
                    if respuesta.get("solution"):
                        for idx, val in enumerate(respuesta["solution"]):
                            var_name = variables[idx] if variables and idx < len(variables) else f"x{idx+1}"
                            
                            import re
                            m = re.match(r'^([a-zA-Z]+)(\d+)$', var_name)
                            if m:
                                html_var = f"<i>{m.group(1)}</i><sub>{m.group(2)}</sub>"
                                latex_var = f"{m.group(1)}_{{{m.group(2)}}}"
                            else:
                                html_var = f"<i>{var_name}</i>"
                                latex_var = f"\\text{{{var_name}}}" if len(var_name) > 1 else var_name
                                
                            if is_unique:
                                ui.html(f'{html_var} = {val}').classes('px-4 py-2 panel-card font-bold math-label text-main')
                            else:
                                ui.html(f'<div class="px-4 py-2 panel-card math-label text-main">$$ {latex_var} = {val} $$</div>')
                            
                if respuesta.get("intermediate_steps_latex"):
                    ui.label('Procedimiento paso a paso').classes('font-bold mt-6 text-xl text-main')
                    with ui.expansion('Ver pasos matriciales', icon='visibility').classes('w-full panel-card mt-2 timeline-expansion').props('header-class="font-bold text-main"'):
                        for paso in respuesta["intermediate_steps_latex"]:
                            with ui.column().classes('w-full p-4 border-l-2 border-l-[var(--accent)] ml-2 mb-2 bg-[var(--bg-panel)] rounded-r-lg'):
                                desc_id = f"desc-{id(paso)}"
                                ui.html(f'<span id="{desc_id}"></span>').classes('text-sm font-semibold mb-2 text-sec block')
                                ui.timer(0.05, lambda text=paso["descripcion"], eid=desc_id: ui.run_javascript(f'typewriterEffect("{eid}", {json.dumps(text)}, 18)'), once=True)
                                ui.html(f'<div class="math-scroll-container math-label text-lg">$$ {paso["matriz"]} $$</div>')
                            
                if respuesta.get("back_substitution_steps") or respuesta.get("verification_steps_latex"):
                    with ui.expansion('Detalles y Comprobación', icon='fact_check').classes('w-full panel-card mt-4').props('header-class="font-bold text-main"'):
                        if respuesta.get("back_substitution_steps"):
                            ui.label('Sustitución:' if self.method_tabs.value == 'gauss' else 'Solución Final:').classes('font-bold text-sm text-sec mt-2')
                            for paso in respuesta["back_substitution_steps"]:
                                if self.method_tabs.value == 'gauss':
                                    ui.html(f'<div class="math-label w-full">$$ {paso} $$</div>')
                                else:
                                    ui.label(paso).classes('text-md font-medium text-main mt-1 w-full')
                                    
                        if respuesta.get("verification_steps_latex"):
                            ui.label('Comprobación Ax = b:').classes('font-bold text-sm text-sec mt-4')
                            for paso in respuesta["verification_steps_latex"]:
                                ui.html(f'<div class="math-scroll-container math-label">$$ {paso} $$</div>')

        if not is_error:
            self._add_to_history(matrix_A_vals, vector_b_vals, len(matrix_A_vals), len(matrix_A_vals[0]) if matrix_A_vals else 0, status, self.method_tabs.value)

        btn.props('loading=false')
        ui.run_javascript('typesetMathWhenReady();')
        
        # Eliminar clase de animación para que se pueda volver a animar
        ui.run_javascript('setTimeout(() => { const res = document.getElementById("' + str(self.contenedor_resultados.id) + '"); if(res) res.classList.remove("animate-slide-up"); }, MOTION.slow);')
        
        with self.contenedor_resultados:
            if not is_error:
                self.render_graphics(matrix_A_vals, vector_b_vals, respuesta)
            
        ui.run_javascript("setTimeout(() => { const el = document.getElementById('resultados-container'); if(el) el.scrollIntoView({behavior: 'smooth', block: 'start'}) }, MOTION.med);")

    def render_graphics(self, matrix_A, vector_b, respuesta):
        m = len(matrix_A)
        n = len(matrix_A[0]) if m > 0 else 0
        
        if n < 2 or n > 3:
            ui.label(f'Visualización gráfica no disponible para {n} dimensiones.').classes('text-sec text-sm italic mt-4')
            return
            
        with ui.expansion('Visualización Gráfica', icon='insights').classes('w-full panel-card mt-4').props('header-class="font-bold text-main" default-opened'):
            try:
                import plotly.graph_objects as go
            except ImportError:
                ui.label('Instalando dependencias gráficas... intente de nuevo en unos segundos.').classes('text-warning')
                return

            def _linspace(start, stop, num):
                if num == 1:
                    return [start]
                step = (stop - start) / (num - 1)
                return [start + i * step for i in range(num)]

            def _meshgrid(x, y):
                X = [[x_val for x_val in x] for _ in y]
                Y = [[y_val for _ in x] for y_val in y]
                return X, Y

            fig = go.Figure()
            colors = CHART_PALETTE
            
            if n == 2:
                x_vals = _linspace(-10, 10, 100)
                for i in range(m):
                    try:
                        a, b, c = float(matrix_A[i][0]), float(matrix_A[i][1]), float(vector_b[i])
                    except:
                        continue
                        
                    if abs(b) > 1e-6:
                        y_vals = [(c - a * x) / b for x in x_vals]
                        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name=f'Eq {i+1}', line=dict(color=colors[i % len(colors)], width=3)))
                    elif abs(a) > 1e-6:
                        x_line = [c/a, c/a]
                        y_line = [-10, 10]
                        fig.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines', name=f'Eq {i+1}', line=dict(color=colors[i % len(colors)], width=3)))
                        
                if respuesta.get("status") == "UNIQUE_SOLUTION" and respuesta.get("solution"):
                    sol = respuesta["solution"]
                    fig.add_trace(go.Scatter(x=[sol[0]], y=[sol[1]], mode='markers', name='Solución',
                                             marker=dict(color=CHART_MARKER_LIGHT, size=12, line=dict(color=CHART_MARKER_BORDER, width=2))))
                                             
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#23262E'),
                    margin=dict(l=20, r=20, t=20, b=20),
                    xaxis=dict(gridcolor=CHART_GRID_COLOR, zerolinecolor=CHART_ZERO_COLOR),
                    yaxis=dict(gridcolor=CHART_GRID_COLOR, zerolinecolor=CHART_ZERO_COLOR)
                )
                
            elif n == 3:
                x = _linspace(-10, 10, 10)
                y = _linspace(-10, 10, 10)
                X, Y = _meshgrid(x, y)
                
                for i in range(m):
                    try:
                        a, b, c_z, d = float(matrix_A[i][0]), float(matrix_A[i][1]), float(matrix_A[i][2]), float(vector_b[i])
                    except:
                        continue
                        
                    if abs(c_z) > 1e-6:
                        Z = [[(d - a * X[r][c] - b * Y[r][c]) / c_z for c in range(len(X[0]))] for r in range(len(X))]
                        fig.add_trace(go.Surface(z=Z, x=X, y=Y, name=f'Eq {i+1}', showscale=False, opacity=0.7, colorscale=[[0, colors[i % len(colors)]], [1, colors[i % len(colors)]]]))
                    elif abs(b) > 1e-6:
                        Z_mesh = _linspace(-10, 10, 10)
                        X_mesh, Z_grid = _meshgrid(x, Z_mesh)
                        Y_grid = [[(d - a * X_mesh[r][c]) / b for c in range(len(X_mesh[0]))] for r in range(len(X_mesh))]
                        fig.add_trace(go.Surface(z=Z_grid, x=X_mesh, y=Y_grid, name=f'Eq {i+1}', showscale=False, opacity=0.7, colorscale=[[0, colors[i % len(colors)]], [1, colors[i % len(colors)]]]))
                    elif abs(a) > 1e-6:
                        Z_mesh = _linspace(-10, 10, 10)
                        Y_mesh, Z_grid = _meshgrid(y, Z_mesh)
                        X_grid = [[(d - b * Y_mesh[r][c]) / a for c in range(len(Y_mesh[0]))] for r in range(len(Y_mesh))]
                        fig.add_trace(go.Surface(z=Z_grid, x=X_grid, y=Y_mesh, name=f'Eq {i+1}', showscale=False, opacity=0.7, colorscale=[[0, colors[i % len(colors)]], [1, colors[i % len(colors)]]]))
                
                if respuesta.get("status") == "UNIQUE_SOLUTION" and respuesta.get("solution"):
                    sol = respuesta["solution"]
                    fig.add_trace(go.Scatter3d(x=[sol[0]], y=[sol[1]], z=[sol[2]], mode='markers', name='Solución',
                                               marker=dict(color=CHART_MARKER_LIGHT, size=8, line=dict(color=CHART_MARKER_BORDER, width=2))))
                
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#23262E'),
                    margin=dict(l=0, r=0, t=0, b=0),
                    scene=dict(
                        xaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor=CHART_GRID_COLOR),
                        yaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor=CHART_GRID_COLOR),
                        zaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor=CHART_GRID_COLOR)
                    )
                )

            ui.plotly(fig).classes('w-full h-[400px]')
            ui.run_javascript("setTimeout(() => { if(window.updatePlotlyTheme) updatePlotlyTheme(document.documentElement.getAttribute('data-theme') || 'claro'); }, 100);")

    def trigger_flip_animation(self):
        ui.run_javascript('''
            const panel = document.querySelector('.main-grid-panel');
            if(panel) {
                panel.classList.remove('animate-slide-bounce');
                void panel.offsetWidth; // trigger reflow
                panel.classList.add('animate-slide-bounce');
            }
        ''')

    def build(self):
        self.ai_panel = AIPanel(self)
        create_navbar(self, active_route='/sistemas-lineales')
        self.grid.inject_scripts()
        self.grid.on_data_change = self._trigger_live_preview
        self.calculator.inject_scripts()
        
        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4'):
            
            # Header con Título y Selector de Método
            with ui.row().classes('w-full justify-between items-center mb-8 gap-4 flex-wrap'):
                # Selector de Método
                with ui.tabs().classes('neo-tabs method-tabs').props('dense no-caps') as self.method_tabs:
                    ui.tab('gauss', label='Gauss')
                    ui.tab('gauss-jordan', label='Gauss-Jordan')
                self.method_tabs.value = self.initial_method
                self.method_tabs.on_value_change(self.trigger_flip_animation)
                
                # Selector de Modo (Matriz/Ecuaciones)
                with ui.tabs().classes('neo-tabs mode-tabs').props('dense no-caps') as self.mode_tabs:
                    ui.tab('Matriz', icon='grid_4x4')
                    ui.tab('Ecuaciones', icon='functions')
            
            with ui.row().classes('w-full flex-col lg:flex-row items-stretch gap-8 mb-8'):
                with ui.column().classes('w-full lg:w-1/2 lg:flex-1'):
                    
                    with ui.tab_panels(self.mode_tabs, value='Matriz').classes('w-full p-0 overflow-hidden panel-card main-grid-panel').props('animated transition-prev="slide-right" transition-next="slide-left"'):
                        
                        # TAB MATRIZ
                        with ui.tab_panel('Matriz').classes('p-6'):
                            with ui.row().classes('w-full justify-end mb-4'):
                                self.sync_btn_from_eq = ui.button('Sincronizar desde Ecuaciones', icon='sync', on_click=self.sync_from_equations, color=None).classes('btn-ghost text-xs py-1 px-3').props('ripple=false')
                            
                            self.grid.build_grid_container()
                            
                        # TAB ECUACIONES
                        with ui.tab_panel('Ecuaciones').classes('p-6'):
                            with ui.row().classes('w-full justify-between items-center mb-6'):
                                ui.label('Sistema de Ecuaciones').classes('text-lg font-bold text-main')
                                self.sync_btn_from_matrix = ui.button('Sincronizar desde Matriz', icon='sync', on_click=self.sync_from_matrix, color=None).classes('btn-ghost text-xs py-1 px-3').props('ripple=false')
                                
                                with ui.row().classes('gap-2 ml-auto'):
                                    ui.button(icon='remove', on_click=self.remove_eq, color=None).classes('btn-neo-icon w-8 h-8 p-0').props('ripple=false')
                                    ui.button(icon='add', on_click=self.add_eq, color=None).classes('btn-neo-icon w-8 h-8 p-0').props('ripple=false')
                            
                            self.contenedor_ecuaciones_lista = ui.column().classes('w-full')
                            self.render_ecuaciones()
                        
                    with ui.row().classes('w-full mt-6 gap-4'):
                        ui.button(icon='delete', on_click=self.confirmar_limpieza, color=None).classes('btn-ghost flex-1 py-3').props('ripple=false id="btn-limpiar-main"').tooltip('Limpiar')
                        ui.button('Resolver', on_click=lambda e: self.resolver_sistema(e.sender), color=None).classes('btn-primary flex-[2] py-3').props('ripple=false')
                
                with ui.column().classes('w-full lg:w-1/2 lg:flex-1 tools-panel'):
                    # Tools Panel con tabs
                    with ui.tabs().classes('neo-tabs w-full').props('dense no-caps') as self.tools_tabs:
                        ui.tab('teclado', label='Teclado')
                        ui.tab('preview', label='Vista previa')
                        ui.tab('history', label='Historial')
                    
                    with ui.tab_panels(self.tools_tabs, value='teclado').classes('w-full p-0 bg-transparent').props('animated'):
                        with ui.tab_panel('teclado').classes('p-0 mt-4'):
                            self.calculator.build(self.mode_tabs)
                            
                        with ui.tab_panel('preview').classes('p-6 panel-card mt-4 min-h-[300px] items-center'):
                            ui.label('Vista Previa en Vivo').classes('font-bold text-main mb-4')
                            self.preview_container = ui.column().classes('w-full items-center justify-center')
                            self._trigger_live_preview()
                            
                        with ui.tab_panel('history').classes('p-6 panel-card mt-4 min-h-[300px]'):
                            ui.label('Últimos 5 sistemas resueltos').classes('font-bold text-main mb-4')
                            self.historial_container = ui.column().classes('w-full')
                            self._render_history()
            
            self.contenedor_resultados = ui.column().classes('w-full panel-card p-6 items-center justify-center min-h-[400px]').props('id="resultados-container"')
            self.reset_resultados()
            
            # Inicializar visibilidad de botones
            self.update_sync_buttons()
            
        self.ai_panel.build()
