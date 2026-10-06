import re

with open("src/frontend/views/numeric_systems/view_roman_calculator.py", "r", encoding="utf-8") as f:
    text = f.read()

# Replace: background: var(--elev-2); ... box-shadow: var(--elev-1); -> background: var(--bg-panel); ... box-shadow: var(--elev-2);
text = re.sub(r'background:\s*var\(--elev-2\);\s*border-color:\s*var\(--border-input\);\s*box-shadow:\s*var\(--elev-1\);',
              r'background: var(--bg-panel); border-color: var(--border-input); box-shadow: var(--elev-2);', text)

# Replace: background: var(--elev-2); border-color: var(--border-input); (without box-shadow) -> background: var(--bg-panel); border-color: var(--border-input); box-shadow: var(--elev-2);
text = re.sub(r'background:\s*var\(--elev-2\);\s*border-color:\s*var\(--border-input\);(?!.*?box-shadow)',
              r'background: var(--bg-panel); border-color: var(--border-input); box-shadow: var(--elev-2);', text)

# Replace background: var(--elev-inset); with background: var(--bg-elevated); box-shadow: var(--elev-inset);
# Sometimes it has other properties
text = re.sub(r'background:\s*var\(--elev-inset\);',
              r'background: var(--bg-elevated); box-shadow: var(--elev-inset);', text)

with open("src/frontend/views/numeric_systems/view_roman_calculator.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Romanos fixed.")
