with open('src/frontend/views/linear_systems/results_mixin.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '<div class="px-4 py-2 panel-card math-label text-main">$$ {latex_var} = {val} $$</div>',
    '<div class="math-scroll-container px-4 py-2 panel-card math-label text-main">$$ {latex_var} = {val} $$</div>'
)

with open('src/frontend/views/linear_systems/results_mixin.py', 'w', encoding='utf-8') as f:
    f.write(content)
