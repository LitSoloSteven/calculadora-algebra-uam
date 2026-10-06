"""Pruebas automáticas de contraste WCAG 2.x para los tres temas (Tarea C1).

Verifica cumplimiento de contraste WCAG AA:
- Texto normal: ratio >= 4.5:1
- Elementos gráficos / indicadores / no-texto: ratio >= 3.0:1
"""
import re
from pathlib import Path
import pytest

CSS_PATH = Path(__file__).resolve().parent.parent / "src" / "frontend" / "assets" / "css" / "theme.css"


def parse_theme_tokens(css_path: Path) -> dict[str, dict[str, str]]:
    """Parsea theme.css y extrae tokens para cada uno de los tres temas resolviendo referencias var()."""
    content = css_path.read_text(encoding="utf-8")
    themes = {"papel": {}, "marea": {}, "medianoche": {}}

    blocks = re.findall(r"(:root[^{]*)\{([^}]+)\}", content, re.DOTALL)
    for sel, body in blocks:
        t_name = None
        if 'data-theme="marea"' in sel:
            t_name = "marea"
        elif 'data-theme="medianoche"' in sel:
            t_name = "medianoche"
        elif 'data-theme="papel"' in sel or (sel.strip() == ":root" and not themes["papel"]):
            t_name = "papel"

        if t_name:
            for line in body.split(";"):
                line = line.strip()
                if not line or ":" not in line:
                    continue
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().split("/*")[0].strip()
                if k.startswith("--"):
                    themes[t_name][k] = v

    # Resolución iterativa de var(--token) dentro del mismo tema
    for t in themes.values():
        for _ in range(6):
            for k, v in list(t.items()):
                if v.startswith("var(") and v.endswith(")"):
                    ref = v[4:-1].strip()
                    if ref in t:
                        t[k] = t[ref]

    return themes


def hex_to_rgb(hex_code: str) -> tuple[float, float, float]:
    """Convierte un color hexadecimal '#RRGGBB' a tupla RGB normalizada (0.0 a 1.0)."""
    hex_code = hex_code.lstrip("#").strip()
    return tuple(int(hex_code[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def rel_lum(rgb: tuple[float, float, float]) -> float:
    """Calcula la luminancia relativa según la especificación WCAG 2.x."""
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = [channel(c) for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(rgb1: tuple[float, float, float], rgb2: tuple[float, float, float]) -> float:
    """Calcula el ratio de contraste entre dos colores (>= 1.0)."""
    l1 = rel_lum(rgb1)
    l2 = rel_lum(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


THEMES = ["papel", "marea", "medianoche"]

# Pares de contraste requeridos por la especificación de la Tarea C1 (Paso 3)
CONTRAST_REQUIREMENTS = [
    # text-main sobre bg-page, bg-panel, bg-elevated e input-bg (>= 4.5:1)
    ("text-main", "bg-page", 4.5),
    ("text-main", "bg-panel", 4.5),
    ("text-main", "bg-elevated", 4.5),
    ("text-main", "input-bg", 4.5),
    # text-sec sobre bg-page, bg-panel, bg-elevated e input-bg (>= 4.5:1)
    ("text-sec", "bg-page", 4.5),
    ("text-sec", "bg-panel", 4.5),
    ("text-sec", "bg-elevated", 4.5),
    ("text-sec", "input-bg", 4.5),
    # accent sobre bg-page, bg-panel y bg-elevated (>= 4.5:1)
    ("accent", "bg-page", 4.5),
    ("accent", "bg-panel", 4.5),
    ("accent", "bg-elevated", 4.5),
    # accent sobre accent-soft (>= 4.5:1)
    ("accent", "accent-soft", 4.5),
    # btn-primary-text sobre btn-primary-bg (>= 4.5:1)
    ("btn-primary-text", "btn-primary-bg", 4.5),
    # error sobre bg-panel (>= 4.5:1 para texto de error en .text-err)
    ("error", "bg-panel", 4.5),
    # badge-warn-text sobre bg-panel (>= 4.5:1 para texto en .text-warn)
    ("badge-warn-text", "bg-panel", 4.5),
    # cada par badge (texto/fondo) (>= 4.5:1)
    ("badge-err-text", "badge-err-bg", 4.5),
    ("badge-suc-text", "badge-suc-bg", 4.5),
    ("badge-warn-text", "badge-warn-bg", 4.5),
    # focus-ring vs bg-page (>= 3.0:1 no-texto)
    ("focus-ring", "bg-page", 3.0),
]


@pytest.mark.parametrize("theme_name", THEMES)
@pytest.mark.parametrize("fg,bg,threshold", CONTRAST_REQUIREMENTS)
def test_theme_wcag_contrast(theme_name: str, fg: str, bg: str, threshold: float):
    """Verifica que cada par especificado cumpla con el ratio de contraste WCAG AA exigido."""
    themes = parse_theme_tokens(CSS_PATH)
    t = themes[theme_name]

    fg_hex = t.get(f"--{fg}")
    bg_hex = t.get(f"--{bg}")

    assert fg_hex is not None, f"Token --{fg} no encontrado en tema {theme_name}"
    assert bg_hex is not None, f"Token --{bg} no encontrado en tema {theme_name}"
    assert fg_hex.startswith("#"), f"Token --{fg} en {theme_name} no es un color hex: {fg_hex}"
    assert bg_hex.startswith("#"), f"Token --{bg} en {theme_name} no es un color hex: {bg_hex}"

    rgb_fg = hex_to_rgb(fg_hex)
    rgb_bg = hex_to_rgb(bg_hex)
    ratio = contrast_ratio(rgb_fg, rgb_bg)

    assert ratio >= threshold, (
        f"Contraste insuficiente en {theme_name}: --{fg} ({fg_hex}) sobre --{bg} ({bg_hex}) = "
        f"{ratio:.2f}:1 (requerido >= {threshold:.1f}:1)"
    )
