"""Auditoría estática AST de accesibilidad (a11y) para src/frontend.

Verifica:
1. ui.button con keyword `icon=` y sin texto posicional debe incluir 'aria-label' en sus .props(...).
2. ui.switch sin texto posicional debe incluir 'aria-label' (en props o keywords).
"""
from __future__ import annotations

import ast
from pathlib import Path


def _extract_props_strings(call_node: ast.Call) -> list[str]:
    """Extrae literales de cadena (estáticos o f-strings) de los argumentos de .props(...)."""
    res = []
    for a in call_node.args:
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            res.append(a.value)
        elif isinstance(a, ast.JoinedStr):
            parts = []
            for val in a.values:
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    parts.append(val.value)
                else:
                    parts.append("")
            res.append("".join(parts))
    return res


def _collect_chained_props(node: ast.AST, parent_map: dict[ast.AST, ast.AST]) -> list[str]:
    """Sube por la cadena de llamadas (.classes(...).props(...).style(...)) recopilando strings de props."""
    curr = node
    props_str = []
    while curr in parent_map:
        parent = parent_map[curr]
        if isinstance(parent, ast.Attribute) and parent.value == curr and parent.attr == "props":
            call_parent = parent_map.get(parent)
            if isinstance(call_parent, ast.Call):
                props_str.extend(_extract_props_strings(call_parent))
        curr = parent
    return props_str


def find_a11y_violations(tree: ast.AST, file_path_str: str) -> list[tuple[str, str, int, str]]:
    """Encuentra violaciones de accesibilidad en ui.button y ui.switch."""
    parent_map = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parent_map[child] = parent

    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        # Detección de ui.button
        is_ui_btn = (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "button"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "ui"
        )
        if is_ui_btn:
            has_icon_kw = any(k.arg == "icon" for k in node.keywords)
            has_pos_text = (
                len(node.args) > 0
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            )
            if has_icon_kw and not has_pos_text:
                props_list = _collect_chained_props(node, parent_map)
                full_props = " ".join(props_list)
                if "aria-label" not in full_props:
                    violations.append(("BUTTON", file_path_str, node.lineno, full_props))

        # Detección de ui.switch
        is_ui_switch = (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "switch"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "ui"
        )
        if is_ui_switch:
            has_pos_text = (
                len(node.args) > 0
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            )
            kw_aria = any(k.arg in ("aria_label", "aria-label") for k in node.keywords)
            props_list = _collect_chained_props(node, parent_map)
            full_props = " ".join(props_list)
            if not has_pos_text and not kw_aria and "aria-label" not in full_props:
                violations.append(("SWITCH", file_path_str, node.lineno, full_props))

    return violations


def test_frontend_a11y_buttons_and_switches():
    """Audita todos los archivos en src/frontend para que no existan ui.button ni ui.switch sin accesibilidad."""
    frontend_dir = Path(__file__).resolve().parent.parent / "src" / "frontend"
    all_violations = []

    for py_file in frontend_dir.rglob("*.py"):
        code = py_file.read_text(encoding="utf-8")
        tree = ast.parse(code, filename=str(py_file))
        violations = find_a11y_violations(tree, py_file.as_posix())
        all_violations.extend(violations)

    if all_violations:
        lines = [
            f"[{kind}] {p}:{line} (props: '{props}')"
            for kind, p, line, props in all_violations
        ]
        report = "\n".join(lines)
        raise AssertionError(
            f"Se encontraron {len(all_violations)} elementos UI sin aria-label ni texto:\n{report}"
        )


def test_a11y_detector_catches_missing_labels_synthetic():
    """Verifica que el auditor detecte llamadas inválidas sintéticas."""
    bad_code = '''
def build():
    btn = ui.button(icon="send").props("ripple=false")
    sw = ui.switch(value=True).props("dense size=sm")
'''
    tree = ast.parse(bad_code)
    violations = find_a11y_violations(tree, "synthetic.py")

    kinds = [v[0] for v in violations]
    assert "BUTTON" in kinds
    assert "SWITCH" in kinds
