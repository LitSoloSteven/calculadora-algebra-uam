"""Contrato estatico del bucle de pilares de la barra (separadores)."""
import ast
from pathlib import Path

NAVBAR_PATH = Path("src/frontend/components/navbar.py")


def _loop_over_nav_groups(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Call):
            call = node.iter
            if isinstance(call.func, ast.Name) and call.func.id == "enumerate":
                inner = call.args[0] if call.args else None
                if isinstance(inner, ast.Call) and getattr(inner.func, "id", "") == "nav_groups":
                    return node
    return None


def _contains_nav_sep(node):
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and sub.value == "nav-sep":
            return True
    return False


def test_pillar_loop_uses_enumerate_over_nav_groups():
    tree = ast.parse(NAVBAR_PATH.read_text(encoding="utf-8"))
    assert _loop_over_nav_groups(tree) is not None


def test_pillar_separator_is_conditional_and_comes_first():
    tree = ast.parse(NAVBAR_PATH.read_text(encoding="utf-8"))
    loop = _loop_over_nav_groups(tree)
    assert loop is not None
    unconditional = [
        stmt for stmt in loop.body
        if not isinstance(stmt, ast.If) and _contains_nav_sep(stmt)
    ]
    assert unconditional == [], "nav-sep no debe emitirse incondicionalmente dentro del bucle"
    first = loop.body[0]
    assert isinstance(first, ast.If) and _contains_nav_sep(first), (
        "El separador condicional (index > 0) debe ser la primera sentencia del bucle"
    )
