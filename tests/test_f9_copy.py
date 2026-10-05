"""F9 Copy unificado (R15).

Verifica mediante análisis estático de AST que ninguna constante de cadena
(excluyendo docstrings) en src/frontend y src/ai contenga '—', 'Oops' ni
formas de voseo no autorizadas.
Verifica además la presencia de 'Hola, soy Glosa.' y la ausencia de '¡Hola! Soy Glosa.',
así como la alineación de nombres con navigation.py.
"""
import ast
import os
import re
from src.frontend.navigation import TOOLS, PILLARS


def _is_docstring(node: ast.Constant, parent: ast.AST) -> bool:
    """Detecta si un nodo ast.Constant representa el docstring del nodo padre."""
    if isinstance(parent, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if parent.body and isinstance(parent.body[0], ast.Expr) and parent.body[0].value is node:
            return True
    return False


def test_ast_copy_no_emdash_no_oops_no_voseo():
    """Ninguna constante de cadena en src/frontend y src/ai contiene '—', 'Oops' ni voseo."""
    voseo_patterns = [
        r'\bvos\b',
        r'\bpodés\b',
        r'\btenés\b',
        r'\bquerés\b',
        r'\bhacé\b',
        r'\bmirá\b',
        r'\bfijate\b',
        r'\bacá\b',
    ]
    bad_substrings = ['—', 'Oops']

    violations = []

    for root_dir in ['src/frontend', 'src/ai']:
        for root, _, files in os.walk(root_dir):
            for f in files:
                if not f.endswith('.py'):
                    continue
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as fp:
                    try:
                        tree = ast.parse(fp.read(), filename=path)
                    except Exception as e:
                        violations.append(f"Error parseando {path}: {e}")
                        continue

                for parent in ast.walk(tree):
                    for child in ast.iter_child_nodes(parent):
                        if isinstance(child, ast.Constant) and isinstance(child.value, str):
                            if _is_docstring(child, parent):
                                continue

                            val = child.value
                            rel_p = os.path.relpath(path).replace('\\', '/')

                            # Allowlist específica para migración de historial en ai_panel.py
                            if 'ai_panel.py' in rel_p and ('—' in val or 'Tutor IA' in val):
                                continue

                            for b in bad_substrings:
                                if b in val:
                                    violations.append(
                                        f"{rel_p}:{child.lineno} contiene {repr(b)}: {val[:60]}"
                                    )

                            for vp in voseo_patterns:
                                if re.search(vp, val, re.IGNORECASE):
                                    violations.append(
                                        f"{rel_p}:{child.lineno} coincide con patrón voseo {vp}: {val[:60]}"
                                    )

    assert not violations, "Violaciones de copy detectadas:\n" + "\n".join(violations)


def test_glosa_greeting_unified():
    """Verifica que '¡Hola! Soy Glosa.' fue reemplazado por 'Hola, soy Glosa.'."""
    dock_file = os.path.join('src', 'frontend', 'components', 'glosa_dock.py')
    with open(dock_file, 'r', encoding='utf-8') as fp:
        content = fp.read()

    assert "¡Hola! Soy Glosa." not in content, "Aún contiene '¡Hola! Soy Glosa.'"
    assert "Hola, soy Glosa." in content, "No contiene 'Hola, soy Glosa.'"


def test_navigation_names_aligned():
    """Verifica la alineación de nombres con navigation.py."""
    expected_tools = {
        "/algebra-lineal/sistemas": "Sistemas de ecuaciones",
        "/algebra-lineal/inversa": "Matriz inversa",
        "/algebra-lineal/matrices": "Matrices",
        "/algebra-lineal/vectores": "Vectores",
        "/visualizador": "Rectas, planos y vectores",
        "/utilidades/bases": "Conversor de bases",
        "/utilidades/romanos": "Números romanos",
    }

    tool_by_route = {t.route: t.name for t in TOOLS}
    for route, expected_name in expected_tools.items():
        assert route in tool_by_route, f"Ruta {route} no encontrada en TOOLS"
        assert tool_by_route[route] == expected_name, (
            f"Ruta {route} tiene nombre {tool_by_route[route]}, se esperaba {expected_name}"
        )
