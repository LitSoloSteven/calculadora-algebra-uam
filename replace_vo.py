with open('src/frontend/views/vector_ops/view_vector_ops.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("ui.column().classes('w-full lg:w-1/2 lg:flex-1 p-8 bg-[var(--bg-page)]')", "ui.column().classes('layout-pane p-8 bg-[var(--bg-page)]')")

with open('src/frontend/views/vector_ops/view_vector_ops.py', 'w', encoding='utf-8') as f:
    f.write(content)
