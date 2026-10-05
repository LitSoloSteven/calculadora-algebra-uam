"""Barridos estáticos de calidad y accesibilidad (Fase F9)."""
import os
import re
import ast
import pytest

FRONTEND_DIR = 'src/frontend'
THEME_CSS_PATH = 'src/frontend/assets/css/theme.css'


def test_no_100vh_in_frontend():
    """F3(i): Ningún archivo de src/frontend contiene '100vh'."""
    violations = []
    for root, _, files in os.walk(FRONTEND_DIR):
        for f in files:
            if not (f.endswith('.py') or f.endswith('.js') or f.endswith('.css')):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                for i, line in enumerate(fp, 1):
                    if '100vh' in line:
                        violations.append(f"{path}:{i} -> {line.strip()}")
    assert not violations, f"Se encontraron referencias a 100vh:\n" + "\n".join(violations)


def test_no_backdrop_filter_or_blur_in_frontend():
    """F3(ii): Ningún archivo en src/frontend contiene 'backdrop-filter' ni 'blur(' salvo splash.js."""
    violations = []
    for root, _, files in os.walk(FRONTEND_DIR):
        for f in files:
            if f == 'splash.js':
                continue
            if not (f.endswith('.py') or f.endswith('.js') or f.endswith('.css')):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                for i, line in enumerate(fp, 1):
                    if 'backdrop-filter' in line or 'blur(' in line:
                        violations.append(f"{path}:{i} -> {line.strip()}")
    assert not violations, f"Se encontraron 'backdrop-filter' o 'blur(' fuera de splash.js:\n" + "\n".join(violations)


def test_no_literal_colors_in_theme_css_after_f2():
    """F3(iii): Ningún color literal (#hex, rgb(, rgba() en theme.css desde '/* === F2:'."""
    with open(THEME_CSS_PATH, 'r', encoding='utf-8') as fp:
        css_content = fp.read()

    f2_pos = css_content.find('/* === F2:')
    assert f2_pos != -1, "Marcador '/* === F2:' no encontrado en theme.css"

    css_tail = css_content[f2_pos:]
    color_re = re.compile(r'(#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\))')
    violations = []
    for i, line in enumerate(css_tail.splitlines(), 1):
        clean = line.split('/*')[0].strip()
        m = color_re.findall(clean)
        if m:
            violations.append(f"Línea {i}: {clean} (colores: {m})")

    assert not violations, f"Colores literales encontrados tras F2:\n" + "\n".join(violations)


def test_no_unapproved_numeric_zindex_in_frontend():
    """F3(iv): Sin z-index numérico fuera de tokens salvo splash (99999) y stacking local <= 10."""
    violations = []
    z_re = re.compile(r'z-index\s*:\s*([0-9]+)', re.IGNORECASE)
    for root, _, files in os.walk(FRONTEND_DIR):
        for f in files:
            if f == 'splash.js':
                continue
            if not (f.endswith('.py') or f.endswith('.js') or f.endswith('.css')):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                for i, line in enumerate(fp, 1):
                    m = z_re.search(line)
                    if m:
                        val = int(m.group(1))
                        # Valores menores o iguales a 10 se permiten solo para stacking contexts locales
                        if val > 10:
                            violations.append(f"{path}:{i} -> z-index: {val}")

    # Verificar que animateGarbageCollection en app.js no usa 9999
    app_js_path = os.path.join(FRONTEND_DIR, 'assets', 'js', 'app.js')
    with open(app_js_path, 'r', encoding='utf-8') as fp:
        app_js = fp.read()
    assert "9999" not in app_js, "app.js aún contiene z-index 9999"
    assert "var(--z-modal)" in app_js, "app.js debe usar var(--z-modal)"

    assert not violations, f"z-index numéricos elevados no permitidos:\n" + "\n".join(violations)


def test_math_scroll_container_wraps_all_mathjax():
    """F3(v): Toda cadena con '$$' en views y components está contenida dentro de .math-scroll-container."""
    target = chr(36) + chr(36)
    violations = []
    for root, _, files in os.walk(FRONTEND_DIR):
        if 'views' not in root and 'components' not in root:
            continue
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                content = fp.read()
            if target not in content:
                continue

            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                if target in line:
                    window = '\n'.join(lines[max(0, i - 10):min(len(lines), i + 10)])
                    if 'math-scroll-container' not in window:
                        violations.append(f"{path}:{i} -> {line.strip()}")

    assert not violations, f"Fórmulas $$ fuera de math-scroll-container:\n" + "\n".join(violations)


def test_icon_buttons_have_aria_label():
    """D2(c): Todo ui.button(...) con icon= y sin texto accesible tiene aria-label."""
    violations = []
    for root, _, files in os.walk(FRONTEND_DIR):
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                src = fp.read()
            try:
                tree = ast.parse(src, filename=path)
            except Exception:
                continue

            lines = src.splitlines()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    is_btn = False
                    if isinstance(node.func, ast.Attribute) and node.func.attr == 'button':
                        is_btn = True
                    if is_btn:
                        has_text = False
                        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str) and node.args[0].value.strip() != '':
                            has_text = True
                        has_icon = any(k.arg == 'icon' for k in node.keywords)
                        if not has_text and has_icon:
                            chunk = '\n'.join(lines[node.lineno - 1:node.end_lineno + 3])
                            if 'aria-label' not in chunk:
                                violations.append(f"{path}:{node.lineno} -> {chunk[:100]}")

    assert not violations, f"Botones de solo icono sin aria-label:\n" + "\n".join(violations)
