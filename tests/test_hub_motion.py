"""Contratos estáticos de movimiento H7 para la matriz del Hub."""
from pathlib import Path
import re

from tests.test_f9_contrast import contrast_ratio, hex_to_rgb, parse_tokens


THEME_CSS_PATH = Path("src/frontend/assets/css/theme.css")
HUB_JS_PATH = Path("src/frontend/assets/js/hub.js")
VIEW_HUB_PATH = Path("src/frontend/views/hub/view_hub.py")


def get_hub_css_block() -> str:
    content = THEME_CSS_PATH.read_text(encoding="utf-8")
    start = content.index("/* === HUB: Matriz de áreas y popovers === */")
    end = content.index("/* === F4: Glosa === */", start)
    return content[start:end]


def matching_brace(css: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(css)):
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    raise AssertionError("Bloque CSS sin cerrar")


def block_for(css: str, selector: str) -> str:
    start = css.index(selector)
    open_index = css.index("{", start)
    return css[open_index + 1:matching_brace(css, open_index)]


def test_hub_motion_transitions_only_use_transform_and_opacity():
    css = get_hub_css_block()
    declarations = re.findall(
        r"\btransition(?:-property)?(?![-\w])\s*:\s*([^;]+);",
        css,
        re.IGNORECASE,
    )
    assert declarations
    forbidden = re.compile(
        r"\b(?:width|height|margin(?:-[a-z-]+)?|padding(?:-[a-z-]+)?|"
        r"left|top|box-shadow)\b",
        re.IGNORECASE,
    )
    for declaration in declarations:
        assert not forbidden.search(declaration), declaration
        for duration in re.findall(r"([\d.]+)ms\b", declaration):
            assert float(duration) <= 250, declaration
    assert not re.search(r"\bease-in\b", css, re.IGNORECASE)


def test_keyboard_and_reduced_motion_disable_new_motion():
    css = get_hub_css_block()
    keyboard_start = css.index('html[data-input="keyboard"] .hub-row,')
    keyboard_open = css.index("{", keyboard_start)
    keyboard = css[keyboard_start:matching_brace(css, keyboard_open) + 1]
    reduced = block_for(css, "@media (prefers-reduced-motion: reduce)")

    assert "transition: none !important" in keyboard
    assert "transition-delay: 0ms !important" in keyboard
    assert ".hub-pop-card" in keyboard
    assert ".hub-tile" in keyboard
    assert "hub-spot-layer" in keyboard
    assert "transition: opacity 120ms linear" in reduced
    assert "transform: none !important" in reduced
    assert "transition-delay: 0ms !important" in reduced
    assert ".hub-row" in reduced
    assert ".hub-pop-card" in reduced
    assert ".hub-tile" in reduced
    assert ".hub-spot-layer" in reduced


def test_hub_rows_and_tiles_have_bounded_stagger_indices():
    view = VIEW_HUB_PATH.read_text(encoding="utf-8")
    css = get_hub_css_block()
    js = HUB_JS_PATH.read_text(encoding="utf-8")

    assert "style=\"--i:{row_index}\"" in view
    assert "style=\"--i:{min(tile_index, 3)}\"" in view
    assert "calc(var(--i, 0) * 45ms)" in css
    assert "calc(var(--i, 0) * 35ms)" in css
    assert "min(tile_index, 3)" in view
    assert "event.detail === 0" in js
    assert "html[data-input=\"keyboard\"]" in css
    assert "pendingDeadline = Date.now() + 3400" in js
    assert "agy-splash-overlay" in js
    assert "new MutationObserver" in js


def test_pointer_halo_is_raf_throttled_and_only_moves_the_spot():
    js = HUB_JS_PATH.read_text(encoding="utf-8")
    start = js.index("  function moveSpot(row, event) {")
    end = js.index("  function clearSpotForPointerOut(event) {", start)
    halo_handler = js[start:end]

    assert "window.requestAnimationFrame" in halo_handler
    assert "spotFrames.has(row)" in halo_handler
    assert "spotPositions.set(row" in halo_handler
    assert "spot.style.transform = 'translate3d('" in halo_handler
    assert ".style." not in halo_handler.replace("spot.style.transform", "")
    assert "data-spot-active" in js
    assert "pointermove" in js
    assert "pointerout" in js
    assert "event.pointerType === 'touch'" in js
    assert "prefers-reduced-motion: reduce" in js


def test_spot_token_is_defined_for_all_themes_and_keeps_text_aa():
    full_css = THEME_CSS_PATH.read_text(encoding="utf-8")
    css = get_hub_css_block()
    tokens = parse_tokens(str(THEME_CSS_PATH))

    assert full_css.count("--hub-spot:") == 4
    assert "color-mix(in srgb, var(--accent) var(--hub-spot), transparent)" in css
    for theme_name in ("papel", "marea", "medianoche"):
        theme = tokens[theme_name]
        percent = float(theme["--hub-spot"].rstrip("%")) / 100
        panel = hex_to_rgb(theme["--bg-panel"])
        accent = hex_to_rgb(theme["--accent"])
        halo_background = tuple(
            percent * accent_channel + (1 - percent) * panel_channel
            for accent_channel, panel_channel in zip(accent, panel)
        )
        for foreground in ("--text-main", "--text-sec"):
            ratio = contrast_ratio(hex_to_rgb(theme[foreground]), halo_background)
            assert ratio >= 4.5, (
                f"Contraste de {foreground} en {theme_name}: {ratio:.2f}:1 < 4.5:1"
            )


def test_popover_motion_waits_for_close_transition_and_has_fallback():
    js = HUB_JS_PATH.read_text(encoding="utf-8")
    css = get_hub_css_block()

    assert "card.style.transformOrigin" in js
    assert "if (instant) card.style.removeProperty('transform-origin')" in js
    assert "cancelCloseWait();" in js
    assert "dialog.removeAttribute('data-open')" in js
    assert "event.propertyName === 'opacity'" in js
    assert "setTimeout(function () { finishClose(dialog); }, 180)" in js
    assert "dialog.close()" in js
    assert "transition: opacity 200ms var(--ease-std)" in css
    assert "transition: opacity 140ms var(--ease-std), transform 140ms var(--ease-std)" in css
    assert "transition-duration: 220ms" in css
    assert "transform: translateY(100%)" in css
    assert "transition-duration: 160ms" in css
