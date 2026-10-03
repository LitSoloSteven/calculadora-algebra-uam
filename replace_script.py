import os

files_4 = [
    'src/frontend/views/linear_systems/view_linear_systems.py',
    'src/frontend/views/vector_ops/view_vector_ops.py',
    'src/frontend/views/matrix_ops/view_matrix_ops.py',
    'src/frontend/views/inverse_ops/view_inverse_ops.py'
]

for file in files_4:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace("w-full max-w-7xl mx-auto p-6 mt-4'", "w-full max-w-7xl mx-auto p-6 mt-4 view-root'")
    content = content.replace("ui.row().classes('w-full flex-col lg:flex-row items-stretch gap-8 mb-8')", "ui.element('div').classes('layout-split mb-8')")
    content = content.replace("ui.column().classes('w-full lg:w-1/2 lg:flex-1')", "ui.column().classes('layout-pane')")
    content = content.replace("ui.column().classes('w-full lg:w-1/2 lg:flex-1 tools-panel')", "ui.column().classes('layout-pane tools-panel')")
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

conv = 'src/frontend/views/numeric_systems/view_numeric_systems.py'
with open(conv, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace("w-full max-w-4xl mx-auto q-pa-md'", "w-full max-w-4xl mx-auto q-pa-md view-root'")
content = content.replace("ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 gap-4 mt-6')", "ui.element('div').classes('layout-grid-2 mt-6')")
with open(conv, 'w', encoding='utf-8') as f:
    f.write(content)

rom = 'src/frontend/views/numeric_systems/view_roman_calculator.py'
with open(rom, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace("w-full max-w-4xl mx-auto q-pa-md'", "w-full max-w-4xl mx-auto q-pa-md view-root'")
content = content.replace("ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 gap-4')", "ui.element('div').classes('layout-grid-2')")
with open(rom, 'w', encoding='utf-8') as f:
    f.write(content)
