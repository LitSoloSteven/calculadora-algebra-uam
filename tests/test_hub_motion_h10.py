"""Guardrails estáticos para la temporización de popovers del Hub (H10)."""
from pathlib import Path
import re


THEME_CSS_PATH = Path("src/frontend/assets/css/theme.css")
HUB_JS_PATH = Path("src/frontend/assets/js/hub.js")


def hub_css_block() -> str:
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


def duration_ms(block: str, property_name: str) -> int:
    match = re.search(rf"\b{re.escape(property_name)}\s*:\s*([^;]+)", block)
    assert match is not None, f"Falta {property_name} en el bloque"
    duration = re.search(r"(\d+)ms\b", match.group(1))
    assert duration is not None, f"Falta duración en {property_name}"
    return int(duration.group(1))


def test_hub_popover_motion_timing_and_accessibility_contract():
    css = hub_css_block()
    js = HUB_JS_PATH.read_text(encoding="utf-8")

    transition_declarations = re.findall(
        r"\btransition(?:-duration)?\s*:\s*([^;]+);",
        css,
        flags=re.IGNORECASE,
    )
    durations = [
        int(value)
        for declaration in transition_declarations
        for value in re.findall(r"(?<![\w.])(\d+)ms\b", declaration)
    ]
    assert durations
    assert max(durations) <= 340
    assert not re.search(r"(?<![\w-])ease-in(?![\w-])", css, re.IGNORECASE)

    card_exit = block_for(css, ".hub-pop-card")
    card_entry = block_for(css, ".hub-pop[open][data-open] .hub-pop-card")
    assert "opacity: 0" in card_exit
    assert duration_ms(card_exit, "transition") == 220
    assert duration_ms(card_entry, "transition-duration") == 320
    assert duration_ms(card_entry, "transition-duration") > duration_ms(card_exit, "transition")

    mobile = block_for(css, "@media (max-width: 639px)")
    mobile_exit = block_for(mobile, ".hub-pop-card")
    mobile_entry = block_for(mobile, ".hub-pop[open][data-open] .hub-pop-card")
    assert duration_ms(mobile_exit, "transition-duration") == 240
    assert duration_ms(mobile_entry, "transition-duration") == 340
    assert duration_ms(mobile_entry, "transition-duration") > duration_ms(mobile_exit, "transition-duration")

    backdrop_entry = block_for(css, ".hub-pop[open][data-open]::backdrop")
    assert duration_ms(backdrop_entry, "transition-duration") == 320
    tile_entry = block_for(css, ".hub-pop[data-open] .hub-tile")
    assert duration_ms(tile_entry, "transition-duration") == 280
    assert "calc(var(--i, 0) * 50ms)" in tile_entry

    fallback = re.search(
        r"setTimeout\(function \(\) \{ finishClose\(dialog\); \}, (\d+)\)",
        js,
    )
    assert fallback is not None
    assert int(fallback.group(1)) > 240
    assert "card.addEventListener('transitionend', closeTransitionHandler);" in js
    assert "event.target === card && event.propertyName === 'opacity'" in js
    assert "cancelCloseWait();" in js
    assert "if (closeTimer && closingDialog === dialog) return;" in js
    assert js.count("closeTimer = setTimeout(") == 1

    keyboard = block_for(css, 'html[data-input="keyboard"] .hub-row,')
    reduced = block_for(css, "@media (prefers-reduced-motion: reduce)")
    assert "transition: none !important" in keyboard
    assert "transition: opacity 120ms linear" in reduced
