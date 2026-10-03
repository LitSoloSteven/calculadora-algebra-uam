import html
import re

def render_glosa_text(text: str) -> str:
    """Escapa HTML y procesa bloques de código con triple backtick.
    El texto normal va en <div> con white-space: pre-wrap,
    y los bloques de código en <pre class="glosa-pre"><code>.
    """
    if not text:
        return ""
    
    escaped = html.escape(text)
    
    # Dividir por pares de backticks. Los unclosed quedan en el texto normal.
    parts = re.split(r'```(.*?)```', escaped, flags=re.DOTALL)
    
    html_out = ""
    for i, part in enumerate(parts):
        if i % 2 == 1:
            html_out += f'<pre class="glosa-pre"><code>{part}</code></pre>'
        else:
            if part:
                html_out += f'<div style="white-space: pre-wrap; overflow-wrap: anywhere;">{part}</div>'
                
    return html_out
