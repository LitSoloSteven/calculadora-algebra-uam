"""Tests para la fase H5: Estilo visual de tarjetas, contraste AA, foco visual y efectos hover."""
from pathlib import Path
import re
import pytest

from tests.test_f9_contrast import contrast_ratio, hex_to_rgb, parse_tokens

THEME_CSS_PATH = Path("src/frontend/assets/css/theme.css")
HUB_JS_PATH = Path("src/frontend/assets/js/hub.js")


def get_hub_css_block() -> str:
    """Extrae el tramo CSS correspondiente al Hub desde theme.css."""
    content = THEME_CSS_PATH.read_text(encoding="utf-8")
    match = re.search(r'/\* === HUB: Carrusel de Áreas === \*/(.*?)(?=/\* === F4: Glosa === \*/)', content, re.DOTALL)
    assert match is not None, "Bloque CSS de Hub no encontrado en theme.css"
    return match.group(1)


def test_hub_card_active_bg_token_in_four_header_blocks():
    """Verifica que --hub-card-active-bg esté declarado exactamente en los 4 bloques del encabezado."""
    content = THEME_CSS_PATH.read_text(encoding="utf-8")
    head = content.split("/* === BASE ===")[0]

    # Extraer los 4 bloques principales del encabezado
    blocks = re.findall(r"(:root[^{]*)\{([^}]+)\}", head, re.DOTALL)
    assert len(blocks) == 4, f"Se esperaban exactamente 4 bloques en el encabezado, encontrados {len(blocks)}"

    token_pattern = re.compile(
        r'--hub-card-active-bg\s*:\s*color-mix\(\s*in\s+srgb\s*,\s*var\(--accent\)\s+(\d+)%\s*,\s*var\(--bg-elevated\)\s*\)'
    )

    for sel, body in blocks:
        match = token_pattern.search(body)
        assert match is not None, f"--hub-card-active-bg no encontrado o con formato inválido en bloque {sel.strip()}"


def test_hub_card_active_bg_contrast_aa_all_themes():
    """Verifica contraste AA (>= 4.5:1) para --text-main, --text-sec, --accent y --btn-primary-text."""
    content = THEME_CSS_PATH.read_text(encoding="utf-8")
    pct_match = re.search(r'--hub-card-active-bg\s*:\s*color-mix\(\s*in\s+srgb\s*,\s*var\(--accent\)\s+(\d+)%', content)
    assert pct_match is not None
    pct = int(pct_match.group(1))

    themes = parse_tokens(str(THEME_CSS_PATH))

    for t_name in ['papel', 'marea', 'medianoche']:
        t = themes[t_name]
        acc_rgb = hex_to_rgb(t['--accent'])
        elev_rgb = hex_to_rgb(t['--bg-elevated'])
        panel_rgb = hex_to_rgb(t['--bg-panel'])
        main_rgb = hex_to_rgb(t['--text-main'])
        sec_rgb = hex_to_rgb(t['--text-sec'])
        btn_text_rgb = hex_to_rgb(t['--btn-primary-text'])

        # Color mezclado sRGB lineal por canal
        mix_rgb = tuple(
            (pct / 100.0) * a + (1.0 - pct / 100.0) * e
            for a, e in zip(acc_rgb, elev_rgb)
        )

        cr_main = contrast_ratio(main_rgb, mix_rgb)
        cr_sec = contrast_ratio(sec_rgb, mix_rgb)
        cr_acc = contrast_ratio(acc_rgb, mix_rgb)
        cr_acc_panel = contrast_ratio(acc_rgb, panel_rgb)
        cr_btn_text = contrast_ratio(btn_text_rgb, acc_rgb)

        assert cr_main >= 4.5, f"Tema {t_name}: contraste --text-main sobre tarjeta activa es {cr_main:.2f} < 4.5"
        assert cr_sec >= 4.5, f"Tema {t_name}: contraste --text-sec sobre tarjeta activa es {cr_sec:.2f} < 4.5"
        assert cr_acc >= 4.5, f"Tema {t_name}: contraste --accent sobre tarjeta activa es {cr_acc:.2f} < 4.5"
        assert cr_acc_panel >= 4.5, f"Tema {t_name}: contraste --accent sobre panel es {cr_acc_panel:.2f} < 4.5"
        assert cr_btn_text >= 4.5, f"Tema {t_name}: contraste --btn-primary-text sobre --accent es {cr_btn_text:.2f} < 4.5"


def test_hub_hover_media_query_gating_single_rule():
    """Verifica que cada regla :hover del tramo hub esté en su propio @media gateado de una sola regla."""
    hub_css = get_hub_css_block()

    # Buscar todos los bloques @media (hover: hover) and (pointer: fine)
    media_hover_blocks = re.findall(
        r'@media\s*\(hover:\s*hover\)\s*and\s*\(pointer:\s*fine\)\s*\{(.*?)\n\}',
        hub_css,
        re.DOTALL
    )
    assert len(media_hover_blocks) >= 4, (
        f"Se esperaban al menos 4 bloques hover gateados en Hub CSS, encontrados {len(media_hover_blocks)}"
    )

    # Verificar que no exista ningún :hover suelto fuera de los bloques @media
    stripped_css = re.sub(
        r'@media\s*\(hover:\s*hover\)\s*and\s*\(pointer:\s*fine\)\s*\{.*?\}\s*\}?',
        '',
        hub_css,
        flags=re.DOTALL
    )
    assert ":hover" not in stripped_css, f"Regla :hover no gateada encontrada en Hub CSS: {stripped_css}"

    # Verificar presencia de las reglas clave de hover
    full_hover_content = "\n".join(media_hover_blocks)
    assert ".hub-card:hover .hub-card-body::after" in full_hover_content
    assert ".hub-card:not(.is-active):hover .hub-card-body::before" in full_hover_content
    assert ".hub-card:hover .hub-card-icon" in full_hover_content
    assert ".hub-tile:hover::after" in full_hover_content


def test_hub_keyboard_and_reduced_motion_transitions():
    """Verifica que con teclado no haya transiciones y que reduced-motion incluya icono y ::before."""
    hub_css = get_hub_css_block()
    content = THEME_CSS_PATH.read_text(encoding="utf-8")

    # Reglas html[data-input="keyboard"]
    kbd_match = re.search(
        r'html\[data-input="keyboard"\]\s+\.hub-card-body,\s*'
        r'html\[data-input="keyboard"\]\s+\.hub-card-body::before,\s*'
        r'html\[data-input="keyboard"\]\s+\.hub-card-body::after,\s*'
        r'html\[data-input="keyboard"\]\s+\.hub-card-icon\s*\{([^}]+)\}',
        hub_css
    )
    assert kbd_match is not None, "Regla html[data-input='keyboard'] para tarjeta no encontrada en Hub CSS"
    assert "transition: none !important" in kbd_match.group(1)

    # Bloque prefers-reduced-motion en theme.css
    red_match = re.search(
        r'@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{(.*?)(?=\n/\* === F4: Glosa)',
        content,
        re.DOTALL
    )
    assert red_match is not None
    red_body = red_match.group(1)

    assert ".hub-card-icon" in red_body, ".hub-card-icon debe estar incluido en reduced-motion"
    assert ".hub-card-body::before" in red_body, ".hub-card-body::before debe estar incluido en reduced-motion"
    assert "opacity 120ms linear" in red_body


def test_hub_card_body_isolation_and_no_opacity():
    """Verifica isolation: isolate, capas ::before y ::after con elevación mayor y ausencia de opacidad atenuadora."""
    hub_css = get_hub_css_block()

    body_match = re.search(r'(?m)^\.hub-card-body\s*\{([^}]+)\}', hub_css)
    assert body_match is not None
    body_text = body_match.group(1)
    assert "isolation: isolate" in body_text, ".hub-card-body debe declarar isolation: isolate"
    assert "box-shadow: var(--elev-2)" in body_text, ".hub-card-body en reposo debe tener elevación var(--elev-2)"
    assert "opacity" not in body_text, ".hub-card-body no debe definir opacity"

    # ::before con tinte y borde de acento
    before_match = re.search(r'\.hub-card-body::before\s*\{([^}]+)\}', hub_css)
    assert before_match is not None
    before_text = before_match.group(1)
    assert "var(--hub-card-active-bg)" in before_text
    assert "inset 0 3px 0 var(--accent)" in before_text
    assert "opacity: var(--hub-focus)" in before_text
    assert "z-index: -1" in before_text
    assert "transition: opacity 220ms var(--ease-std)" in before_text

    # ::after con elev-3
    after_match = re.search(r'\.hub-card-body::after\s*\{([^}]+)\}', hub_css)
    assert after_match is not None
    after_text = after_match.group(1)
    assert "box-shadow: var(--elev-3)" in after_text
    assert "opacity: var(--hub-focus)" in after_text

    # Icono relleno en activa
    active_icon_match = re.search(r'\.hub-card\.is-active\s+\.hub-card-icon\s*\{([^}]+)\}', hub_css)
    assert active_icon_match is not None
    active_icon_text = active_icon_match.group(1)
    assert "background-color: var(--accent)" in active_icon_text
    assert "color: var(--btn-primary-text)" in active_icon_text

    # Regla base .hub-card-icon con transición de transform
    icon_match = re.search(r'(?m)^\.hub-card-icon\s*\{([^}]+)\}', hub_css)
    assert icon_match is not None
    assert "transition: transform 160ms var(--ease-std)" in icon_match.group(1)
