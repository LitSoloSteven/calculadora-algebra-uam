"""Test estructural para verificar que ningún archivo en src/frontend y src/ai

utiliza nombres globales no definidos ni importados.
"""
from __future__ import annotations

import ast
import builtins
from pathlib import Path


BUILTIN_NAMES = set(dir(builtins)) | {
    "__file__",
    "__name__",
    "__doc__",
    "__package__",
    "__path__",
    "__builtins__",
    "__annotations__",
}


def collect_bound_names(tree: ast.AST) -> set[str]:
    """Reúne todos los nombres enlazados en cualquier parte del árbol sintáctico."""
    bound = set(BUILTIN_NAMES)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
            if hasattr(node, "args"):
                args_obj = node.args
                for a in getattr(args_obj, "posonlyargs", []) + args_obj.args + args_obj.kwonlyargs:
                    bound.add(a.arg)
                if args_obj.vararg:
                    bound.add(args_obj.vararg.arg)
                if args_obj.kwarg:
                    bound.add(args_obj.kwarg.arg)

        elif isinstance(node, ast.Lambda):
            for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
                bound.add(a.arg)
            if node.args.vararg:
                bound.add(node.args.vararg.arg)
            if node.args.kwarg:
                bound.add(node.args.kwarg.arg)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound.add(alias.asname or alias.name)

        elif isinstance(node, ast.ExceptHandler):
            if node.name:
                bound.add(node.name)

        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            for name in node.names:
                bound.add(name)

        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bound.add(node.id)

    return bound


def find_unbound_names_in_file(file_path: Path) -> list[tuple[str, int, str]]:
    """Encuentra nombres en contexto Load que no estén enlazados en el archivo ni en builtins."""
    content = file_path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(file_path))
    bound = collect_bound_names(tree)

    unbound = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in bound:
                unbound.append((file_path.as_posix(), node.lineno, node.id))

    return unbound


def test_no_unbound_global_names_in_frontend_and_ai():
    """Recorre todos los módulos de src/frontend y src/ai asegurando que todo nombre esté enlazado."""
    project_root = Path(__file__).resolve().parent.parent
    target_dirs = [project_root / "src" / "frontend", project_root / "src" / "ai"]

    all_unbound = []
    scanned_count = 0

    for target_dir in target_dirs:
        for py_path in target_dir.rglob("*.py"):
            scanned_count += 1
            unbound = find_unbound_names_in_file(py_path)
            all_unbound.extend(unbound)

    assert scanned_count > 0, "No se encontraron archivos .py para escanear"

    if all_unbound:
        lines = [f"{p}:{lineno} -> '{name}'" for p, lineno, name in all_unbound]
        report = "\n".join(lines)
        raise AssertionError(
            f"Se encontraron {len(all_unbound)} nombres no definidos/importados:\n{report}"
        )


def test_detector_catches_missing_imports_mental_verification():
    """Verifica que el algoritmo detecta exactamente la omisión de imports

    como la que ocurrió en ai_panel.py antes de F9b (asyncio, json, html).
    """
    sample_code = '''
def schedule_context_refresh():
    async def _debounced():
        await asyncio.sleep(0.25)
    _debounced()

def _render_message(text):
    s = json.dumps(text)
    return html.escape(s)
'''
    tree = ast.parse(sample_code)
    bound = collect_bound_names(tree)
    missing = [
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node.id not in bound
    ]

    assert "asyncio" in missing
    assert "json" in missing
    assert "html" in missing
