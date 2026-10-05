"""Pruebas de verificacion de tokens de swatches tematicos (Fase P2a)."""
import re
from pathlib import Path
import pytest

from tests.test_f9_contrast import parse_tokens

CSS_PATH = Path("src/frontend/assets/css/theme.css")

EXPECTED_SWATCHES = {
    "--swatch-papel": "#F2F0EB",
    "--swatch-marea": "#DEF7FF",
    "--swatch-medianoche": "#082338",
}


def test_swatches_match_bg_page_of_each_theme():
    """Cada swatch debe coincidir exactamente con el color de fondo (--bg-page) de su tema."""
    themes = parse_tokens(str(CSS_PATH))

    assert themes["papel"]["--swatch-papel"] == themes["papel"]["--bg-page"]
    assert themes["marea"]["--swatch-marea"] == themes["marea"]["--bg-page"]
    assert themes["medianoche"]["--swatch-medianoche"] == themes["medianoche"]["--bg-page"]


def test_swatches_defined_in_root_and_all_theme_blocks():
    """Verifica que los tres swatches esten declarados en :root y en cada uno de los bloques de tema."""
    content = CSS_PATH.read_text(encoding="utf-8")

    # Cada token swatch aparece declarado al menos 4 veces (:root y los 3 temas)
    for swatch, val in EXPECTED_SWATCHES.items():
        assert content.count(f"{swatch}: {val};") >= 4

    # Verificar presencia explícita en los 4 bloques temáticos principales del inicio
    head = content.split("/* === BASE ===")[0]
    blocks = re.findall(r"(:root[^{]*)\{([^}]+)\}", head, re.DOTALL)
    assert len(blocks) == 4, f"Se esperaban 4 bloques principales en el encabezado, se encontraron {len(blocks)}"

    for sel, body in blocks:
        for swatch, val in EXPECTED_SWATCHES.items():
            assert f"{swatch}: {val};" in body, (
                f"Token {swatch} con valor {val} no encontrado en bloque {sel.strip()}"
            )
