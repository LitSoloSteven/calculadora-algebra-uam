"""Pruebas automáticas de contraste WCAG AA, relieve y swatches para Marea #CFE3F0 (Fase C2).

Verifica en Python puro sin dependencias de navegador ni NiceGUI:
- Contraste WCAG 2.x AA en Marea (>= 4.5:1 texto, >= 3.0:1 no-texto/foco).
- Heurística de relieve neumórfico (diferencias de luminancia entre superficies).
- Presencia exacta de las 4 declaraciones --swatch-marea: #D8FFFF;.
- Inmutabilidad de los bloques de Papel y Medianoche.
"""
import re
from pathlib import Path
import pytest

CSS_PATH = Path(__file__).resolve().parent.parent / "src" / "frontend" / "assets" / "css" / "theme.css"


def parse_tokens(css_path: Path) -> dict[str, dict[str, str]]:
    """Parsea theme.css y extrae tokens por tema resolviendo var() del mismo bloque."""
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

    # Resolver referencias var()
    for t in themes.values():
        for _ in range(6):
            for k, v in list(t.items()):
                if v.startswith("var(") and v.endswith(")"):
                    ref = v[4:-1].strip()
                    if ref in t:
                        t[k] = t[ref]

    return themes


def hex_to_rgb(hex_code: str) -> tuple[float, float, float]:
    """Convierte hex '#RRGGBB' a tupla RGB normalizada (0.0..1.0)."""
    hex_code = hex_code.lstrip("#").strip()
    return tuple(int(hex_code[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def rel_lum(rgb: tuple[float, float, float]) -> float:
    """Calcula luminancia relativa según WCAG 2.x."""
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = [channel(c) for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(rgb1: tuple[float, float, float], rgb2: tuple[float, float, float]) -> float:
    """Calcula el ratio de contraste entre dos colores (>= 1.0)."""
    l1 = rel_lum(rgb1)
    l2 = rel_lum(rgb2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


MAREA_TEXT_SURFACES = [
    # text-main y text-sec sobre bg-page, bg-panel, bg-elevated, bg-calc-btn, input-bg
    ("text-main", "bg-page", 4.5),
    ("text-main", "bg-panel", 4.5),
    ("text-main", "bg-elevated", 4.5),
    ("text-main", "bg-calc-btn", 4.5),
    ("text-main", "input-bg", 4.5),
    ("text-sec", "bg-page", 4.5),
    ("text-sec", "bg-panel", 4.5),
    ("text-sec", "bg-elevated", 4.5),
    ("text-sec", "bg-calc-btn", 4.5),
    ("text-sec", "input-bg", 4.5),
]

MAREA_ACCENT_PAIRS = [
    # accent sobre bg-page, bg-panel, bg-elevated y accent-soft
    ("accent", "bg-page", 4.5),
    ("accent", "bg-panel", 4.5),
    ("accent", "bg-elevated", 4.5),
    ("accent", "accent-soft", 4.5),
    ("btn-primary-text", "btn-primary-bg", 4.5),
]

MAREA_STATUS_PAIRS = [
    # error, success, warning sobre bg-page y bg-panel (>= 4.5)
    ("error", "bg-page", 4.5),
    ("error", "bg-panel", 4.5),
    ("success", "bg-page", 4.5),
    ("success", "bg-panel", 4.5),
    ("warning", "bg-page", 4.5),
    ("warning", "bg-panel", 4.5),
]

MAREA_BADGE_PAIRS = [
    ("badge-err-text", "badge-err-bg", 4.5),
    ("badge-suc-text", "badge-suc-bg", 4.5),
    ("badge-warn-text", "badge-warn-bg", 4.5),
]

MAREA_FOCUS_PAIRS = [
    ("focus-ring", "bg-page", 3.0),
    ("focus-ring", "bg-panel", 3.0),
]


@pytest.mark.parametrize("fg,bg,threshold", MAREA_TEXT_SURFACES + MAREA_ACCENT_PAIRS + MAREA_STATUS_PAIRS + MAREA_BADGE_PAIRS + MAREA_FOCUS_PAIRS)
def test_marea_wcag_contrast(fg: str, bg: str, threshold: float):
    """Verifica contraste WCAG AA exigido en Marea para cada par especificado en C2."""
    themes = parse_tokens(CSS_PATH)
    marea = themes["marea"]

    fg_hex = marea.get(f"--{fg}")
    bg_hex = marea.get(f"--{bg}")
    assert fg_hex is not None, f"Token --{fg} no encontrado en Marea"
    assert bg_hex is not None, f"Token --{bg} no encontrado en Marea"

    cr = contrast_ratio(hex_to_rgb(fg_hex), hex_to_rgb(bg_hex))
    assert cr >= threshold, (
        f"Contraste insuficiente en Marea: --{fg} ({fg_hex}) sobre --{bg} ({bg_hex}) = "
        f"{cr:.2f}:1 (requerido >= {threshold:.1f}:1)"
    )


def test_marea_neumorphic_relief_heuristics():
    """Verifica que el relieve neumórfico posea diferencias mínimas de luminancia relativa."""
    themes = parse_tokens(CSS_PATH)
    marea = themes["marea"]

    lum_page = rel_lum(hex_to_rgb(marea["--bg-page"]))
    lum_panel = rel_lum(hex_to_rgb(marea["--bg-panel"]))
    lum_elevated = rel_lum(hex_to_rgb(marea["--bg-elevated"]))
    lum_input = rel_lum(hex_to_rgb(marea["--input-bg"]))

    # Heurística 1: El panel debe ser notablemente más oscuro que la página (ΔL >= 0.08)
    diff_panel = lum_page - lum_panel
    assert diff_panel >= 0.08, (
        f"Relieve insuficiente entre --bg-page ({lum_page:.4f}) y --bg-panel ({lum_panel:.4f}): ΔL = {diff_panel:.4f} < 0.08"
    )

    # Heurística 2: El input debe ser claramente hundido respecto a la página (ΔL >= 0.15)
    diff_input = lum_page - lum_input
    assert diff_input >= 0.15, (
        f"Relieve insuficiente de hundimiento para --input-bg: ΔL = {diff_input:.4f} < 0.15"
    )

    # Heurística 3: El input debe ser más oscuro que el panel (ΔL >= 0.05)
    diff_panel_input = lum_panel - lum_input
    assert diff_panel_input >= 0.05, (
        f"El input debe ser más oscuro que el panel: ΔL = {diff_panel_input:.4f} < 0.05"
    )

    # Heurística 4: La superficie elevated debe ser más clara que la página (L_elevated > L_page)
    assert lum_elevated > lum_page, (
        f"La superficie --bg-elevated ({lum_elevated:.4f}) debe ser más clara que --bg-page ({lum_page:.4f})"
    )


def test_swatches_marea_four_declarations():
    """Verifica que las cuatro declaraciones de --swatch-marea sean exactamente #CFE3F0."""
    content = CSS_PATH.read_text(encoding="utf-8")
    assert content.count("--swatch-marea: #CFE3F0;") >= 4, (
        f"Se esperaban al menos 4 declaraciones exactas de '--swatch-marea: #CFE3F0;', "
        f"se encontraron {content.count('--swatch-marea: #CFE3F0;')}"
    )


def test_papel_and_medianoche_unaltered():
    """Verifica que los tokens de Papel y Medianoche permanezcan idénticos a su estado canónico."""
    themes = parse_tokens(CSS_PATH)
    papel = themes["papel"]
    medianoche = themes["medianoche"]

    expected_papel = {
        "--bg-page": "#F2F0EB",
        "--bg-panel": "#EDEAE3",
        "--bg-elevated": "#F7F5F1",
        "--bg-calc-btn": "#F6F4EF",
        "--input-bg": "#E5E1D8",
        "--text-main": "#23262E",
        "--text-sec": "#5A6070",
        "--accent": "#1F6B64",
        "--accent-soft": "#D8E8E5",
        "--btn-primary-text": "#F7F5F1",
        "--focus-ring": "#1F6B64",
        "--error": "#B23A31",
        "--success": "#1F7A4D",
        "--warning": "#A6710B",
    }
    for k, v in expected_papel.items():
        assert papel.get(k) == v, f"Token Papel {k} alterado: {papel.get(k)} != {v}"

    expected_medianoche = {
        "--bg-page": "#082338",
        "--bg-panel": "#0A2B45",
        "--bg-elevated": "#0D3554",
        "--bg-calc-btn": "#0D3554",
        "--input-bg": "#061D2E",
        "--text-main": "#EAF6FF",
        "--text-sec": "#B1D4F0",
        "--accent": "#BFE6E1",
        "--accent-soft": "#14403C",
        "--btn-primary-text": "#082338",
        "--focus-ring": "#BFE6E1",
        "--error": "#E8897D",
        "--success": "#8FCBA6",
        "--warning": "#E3B27E",
    }
    for k, v in expected_medianoche.items():
        assert medianoche.get(k) == v, f"Token Medianoche {k} alterado: {medianoche.get(k)} != {v}"
