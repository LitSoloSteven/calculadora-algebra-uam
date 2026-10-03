"""Tests F8c — Verificación de copy unificado a tuteo y sin formas voseo en frontend y ai."""
import re
from pathlib import Path
import pytest

VOSEO_REGEX = re.compile(
    r"\b(ingresá|añadí|escribí|presioná|pegá|preguntá|contactá|instalá|elegí|seleccioná|usá|probá|revisá)\b",
    re.IGNORECASE
)


def _gather_files():
    roots = [Path("src/frontend"), Path("src/ai")]
    files = []
    for root in roots:
        for p in root.rglob("*"):
            if p.is_file() and p.suffix in (".py", ".js"):
                files.append(p)
    return files


def test_no_voseo_in_frontend_and_ai():
    """Verifica que ningún archivo en src/frontend o src/ai contenga formas voseo prohibidas."""
    files = _gather_files()
    assert len(files) > 0, "No se encontraron archivos en src/frontend o src/ai"

    violations = []
    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        matches = VOSEO_REGEX.findall(text)
        if matches:
            violations.append(f"{file_path}: {matches}")

    assert not violations, f"Se encontraron formas voseo en los siguientes archivos:\n" + "\n".join(violations)


def test_square_matrix_panel_max_n_dynamic_copy():
    """Verifica que el panel de matriz cuadrada use el límite dinámico en el texto de ayuda."""
    panel_file = Path("src/frontend/components/square_matrix_panel.py")
    assert panel_file.exists()
    content = panel_file.read_text(encoding="utf-8")
    assert "Máx. 50×50" not in content, "square_matrix_panel.py todavía contiene 'Máx. 50×50' hardcodeado"
    assert "MAX_N" in content
    assert "Pega desde Excel" in content
