from nicegui import ui

class CalculatorPanel:
    def __init__(self):
        # Símbolos para modo Matriz: solo números y operadores básicos para fracciones/negativos
        self.symbols_matrix = [
            '7', '8', '9', '/',
            '4', '5', '6', '-',
            '1', '2', '3', '.',
            '+', '0', '⌫', 'C'
        ]
        
        # Símbolos para modo Ecuaciones: variables y operadores adicionales
        self.symbols_equations = [
            '7', '8', '9', '+', '-',
            '4', '5', '6', '*', '/',
            '1', '2', '3', 'x', 'y',
            '0', '.', '=', 'z', 'C'
        ]

    def inject_scripts(self):
        ui.add_head_html('''
            <script>
            window.lastFocusedInput = null;
            document.addEventListener('focusin', (e) => {
                if (e.target && e.target.tagName === 'INPUT' && e.target.closest('.matrix-input')) {
                    window.lastFocusedInput = e.target;
                }
            });
            
            function insertSymbol(sym) {
                if (!sym) return;
                let active = window.lastFocusedInput || document.activeElement;
                if (active && active.tagName !== 'INPUT') active = window.lastFocusedInput;
                if (active && active.tagName === 'INPUT') {
                    if (sym === 'C') {
                        active.value = '';
                    } else if (sym === '⌫') {
                        const start = active.selectionStart;
                        const end = active.selectionEnd;
                        const currentVal = active.value;
                        if (start === end && start > 0) {
                            active.value = currentVal.substring(0, start - 1) + currentVal.substring(end);
                            active.setSelectionRange(start - 1, start - 1);
                        } else if (start !== end) {
                            active.value = currentVal.substring(0, start) + currentVal.substring(end);
                            active.setSelectionRange(start, start);
                        }
                    } else {
                        const start = active.selectionStart;
                        const end = active.selectionEnd;
                        const currentVal = active.value;
                        active.value = currentVal.substring(0, start) + sym + currentVal.substring(end);
                        active.setSelectionRange(start + sym.length, start + sym.length);
                    }
                    
                    // Disparar eventos para que NiceGUI y Quasar detecten el cambio
                    active.dispatchEvent(new Event('input', { bubbles: true }));
                    active.dispatchEvent(new Event('change', { bubbles: true }));
                    active.focus();
                } else {
                    // Si no hay input activo, intentar buscar el primer input disponible
                    const inputs = document.querySelectorAll('.matrix-input input');
                    if (inputs.length > 0) {
                        inputs[0].focus();
                        insertSymbol(sym);
                    }
                }
            }
            </script>
        ''')

    def build(self, mode_tabs):
        with ui.column().classes('w-full h-full p-6 flex flex-col justify-between panel-card'):
            ui.label('Calculadora').classes('text-main font-bold mb-4 text-center w-full text-lg')
            
            with ui.tab_panels(mode_tabs, value='Matriz').classes('w-full flex-1 bg-transparent p-0 overflow-hidden').props('animated transition-prev="slide-right" transition-next="slide-left"'):
                
                with ui.tab_panel('Matriz').classes('p-0 h-full flex flex-col justify-center'):
                    with ui.grid(columns=4).classes('w-full gap-4'):
                        for sym in self.symbols_matrix:
                            if sym:
                                classes = 'btn-neo-calc w-full h-14 p-0 text-xl font-bold ' + ('text-main' if sym != 'C' else '')
                                btn = ui.button(sym, on_click=lambda s=sym: ui.run_javascript(f"insertSymbol('{s}')"), color=None).classes(classes).props('ripple=false flat')
                                if sym == 'C': btn.style('color: var(--error)')
                            else:
                                ui.label('').classes('w-full h-14') # Espacio en blanco
                                
                with ui.tab_panel('Ecuaciones').classes('p-0 h-full flex flex-col justify-center'):
                    with ui.grid(columns=5).classes('w-full gap-3'):
                        for sym in self.symbols_equations:
                            if sym:
                                classes = 'btn-neo-calc w-full h-12 p-0 text-lg font-bold ' + ('text-main' if sym != 'C' else '')
                                btn = ui.button(sym, on_click=lambda s=sym: ui.run_javascript(f"insertSymbol('{s}')"), color=None).classes(classes).props('ripple=false flat')
                                if sym == 'C': btn.style('color: var(--error)')
                            else:
                                ui.label('').classes('w-full h-12')
