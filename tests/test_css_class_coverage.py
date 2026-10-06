"""Test de cobertura estatica de clases CSS semanticas (nav-*, hub-*, glosa-*).
Verifica que toda clase usada en components/ y views/ tenga regla en theme.css (Paso 1e y 2.8)."""
from pathlib import Path
import re
import pytest

CSS_PATH = Path("src/frontend/assets/css/theme.css")


def get_used_semantic_classes() -> set[str]:
    classes_used = set()
    directories = [Path("src/frontend/components"), Path("src/frontend/views")]

    for directory in directories:
        for file_path in directory.rglob("*.py"):
            text = file_path.read_text(encoding="utf-8")
            # Extraer clases dentro de .classes(...) o class="..."
            for match in re.findall(r'''(?:classes\(|class=)[fF]?['"]([^'"]+)['"]''', text):
                for word in match.split():
                    clean = re.sub(r'[^a-zA-Z0-9_-]', '', word)
                    if any(clean.startswith(prefix) for prefix in ['nav-', 'hub-', 'glosa-']):
                        classes_used.add(clean)

            # Extraer clases en fragmentos HTML class="..."
            for match in re.findall(r'''class=['"]([^'"]+)['"]''', text):
                for word in match.split():
                    clean = re.sub(r'[^a-zA-Z0-9_-]', '', word)
                    if any(clean.startswith(prefix) for prefix in ['nav-', 'hub-', 'glosa-']):
                        classes_used.add(clean)

    return classes_used


def get_css_defined_classes() -> set[str]:
    content = CSS_PATH.read_text(encoding="utf-8")
    # Buscar todas las clases declaradas en selectores CSS: .clase
    return set(re.findall(r'\.([a-zA-Z0-9_-]+)', content))


def test_no_orphan_semantic_classes():
    """Verifica que ninguna clase nav-*, hub-* o glosa-* usada en Python quede sin regla en theme.css."""
    used_classes = get_used_semantic_classes()
    assert len(used_classes) > 0, "No se encontraron clases semanticas usadas"

    defined_classes = get_css_defined_classes()
    orphans = sorted([cls for cls in used_classes if cls not in defined_classes])

    assert orphans == [], f"Clases semanticas huerfanas (sin regla en theme.css): {orphans}"
