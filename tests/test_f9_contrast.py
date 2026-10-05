"""Pruebas automáticas de contraste WCAG 2.x para tokens en theme.css (Fase F9)."""
import re
import pytest

CSS_PATH = 'src/frontend/assets/css/theme.css'

def parse_tokens(css_path):
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()

    themes = {'papel': {}, 'marea': {}, 'medianoche': {}}

    # Match :root and theme blocks
    blocks = re.findall(r'(:root[^{]*)\{([^}]+)\}', content, re.DOTALL)
    for sel, body in blocks:
        t_name = None
        if 'data-theme="marea"' in sel:
            t_name = 'marea'
        elif 'data-theme="medianoche"' in sel:
            t_name = 'medianoche'
        elif 'data-theme="papel"' in sel or (sel.strip() == ':root' and not themes['papel']):
            t_name = 'papel'

        if t_name:
            for line in body.split(';'):
                line = line.strip()
                if not line or ':' not in line:
                    continue
                k, v = line.split(':', 1)
                k = k.strip()
                v = v.strip().split('/*')[0].strip()
                if k.startswith('--'):
                    themes[t_name][k] = v

    # Resolve references like var(--accent)
    for t in themes.values():
        for k, v in list(t.items()):
            if v.startswith('var('):
                ref = v[4:-1].strip()
                if ref in t:
                    t[k] = t[ref]

    return themes

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def rel_lum(rgb):
    def channel(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = [channel(c) for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(rgb1, rgb2):
    l1 = rel_lum(rgb1)
    l2 = rel_lum(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

PAIRS = [
    ('text-main', 'bg-page', 4.5),
    ('text-main', 'bg-panel', 4.5),
    ('text-main', 'bg-elevated', 4.5),
    ('text-main', 'input-bg', 4.5),
    ('text-sec', 'bg-page', 4.5),
    ('text-sec', 'bg-panel', 4.5),
    ('text-sec', 'bg-elevated', 4.5),
    ('text-sec', 'input-bg', 4.5),
    ('text-placeholder', 'input-bg', 4.5),
    ('accent', 'bg-page', 4.5),
    ('accent', 'bg-panel', 4.5),
    ('accent', 'bg-elevated', 4.5),
    ('accent', 'accent-soft', 4.5),
    ('btn-primary-text', 'btn-primary-bg', 4.5),
    ('badge-err-text', 'badge-err-bg', 4.5),
    ('badge-suc-text', 'badge-suc-bg', 4.5),
    ('badge-warn-text', 'badge-warn-bg', 4.5),
    ('error', 'bg-panel', 3.0),
    ('success', 'bg-panel', 3.0),
    ('warning', 'bg-panel', 3.0),
    ('focus-ring', 'bg-page', 3.0),
]

THEMES = ['papel', 'marea', 'medianoche']

@pytest.mark.parametrize("theme_name", THEMES)
@pytest.mark.parametrize("fg,bg,threshold", PAIRS)
def test_contrast_ratio_wcag(theme_name, fg, bg, threshold):
    themes = parse_tokens(CSS_PATH)
    t = themes[theme_name]
    fg_hex = t.get(f'--{fg}')
    bg_hex = t.get(f'--{bg}')
    assert fg_hex, f"Token --{fg} no encontrado en tema {theme_name}"
    assert bg_hex, f"Token --{bg} no encontrado en tema {theme_name}"

    rgb_fg = hex_to_rgb(fg_hex)
    rgb_bg = hex_to_rgb(bg_hex)
    cr = contrast_ratio(rgb_fg, rgb_bg)
    assert cr >= threshold, (
        f"Contraste insuficiente en {theme_name}: {fg} ({fg_hex}) sobre {bg} ({bg_hex}) = "
        f"{cr:.2f}:1 (requerido >= {threshold}:1)"
    )
