"""Pruebas de cumplimiento continuo de las reglas SCALARIS.

Valida de forma estricta los límites duros, la ausencia de marcadores de
conflicto, higiene de archivos, ausencia de comentarios prohibidos y
docstrings en español para los archivos bajo alcance de cada fase.
"""

import ast
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Archivos formalmente auditados por fases cerradas
ARCHIVOS_AUDITADOS = [
    RAIZ / "src" / "frontend" / "controllers" / "linear_systems" / "_shared.py",
    RAIZ / "src" / "frontend" / "views" / "vector_ops" / "results_mixin.py",
]

PATRONES_PROHIBIDOS = [
    re.compile(r"^\s*#\s*[-=*#]{3,}", re.MULTILINE),
    re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE),
    re.compile(r"\b(F8[a-z]?|F4|F9[a-z]?|LIT-\d+|Paso\s+\d+)\b", re.IGNORECASE),
    re.compile(r"[\U00010000-\U0010ffff]", re.UNICODE),
]


def test_higiene_sin_scripts_residuales():
    """Verifica que no existan scripts de parcheo ni carpetas de regresion en raiz."""
    archivos_residuales = [
        "check_dry_refactor.py",
        "replace_ls.py",
        "replace_romanos.py",
        "replace_script.py",
        "replace_vo.py",
    ]
    for nombre in archivos_residuales:
        ruta = RAIZ / nombre
        assert not ruta.exists(), f"Archivo residual encontrado en raiz: {nombre}"

    assert not (RAIZ / "regression_output").exists(), "Directorio regression_output presente."


def test_sin_marcadores_de_conflicto():
    """Verifica que ningun archivo de codigo contenga marcadores de git."""
    extensiones = {".py", ".js", ".css", ".html"}
    patron_conflicto = re.compile(r"^(<{7}|={7}|>{7})(?:[ \t\r\n]|$)", re.MULTILINE)
    archivos_codigo = [
        p for p in RAIZ.glob("src/**/*") if p.is_file() and p.suffix in extensiones
    ] + [
        p for p in RAIZ.glob("tests/**/*.py") if p.is_file()
    ]

    for ruta in archivos_codigo:
        contenido = ruta.read_text(encoding="utf-8", errors="ignore")
        coincidencias = patron_conflicto.findall(contenido)
        assert not coincidencias, f"Marcador de conflicto detectado en {ruta.relative_to(RAIZ)}"


def test_limite_lineas_archivos_auditados():
    """Comprueba que ningun archivo auditado supere las 300 lineas."""
    for ruta in ARCHIVOS_AUDITADOS:
        lineas = ruta.read_text(encoding="utf-8").splitlines()
        total = len(lineas)
        assert total <= 300, f"{ruta.name} tiene {total} lineas (limite 300)."


def test_limite_lineas_funciones_auditadas():
    """Comprueba que ninguna funcion en los archivos auditados supere las 40 lineas."""
    for ruta in ARCHIVOS_AUDITADOS:
        if ruta.suffix != ".py":
            continue
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lineas = (nodo.end_lineno or nodo.lineno) - nodo.lineno + 1
                assert lineas <= 40, f"{ruta.name}:{nodo.name} tiene {lineas} lineas (max 40)."


def test_sin_comentarios_prohibidos():
    """Comprueba que los archivos auditados no contengan comentarios prohibidos."""
    for ruta in ARCHIVOS_AUDITADOS:
        contenido = ruta.read_text(encoding="utf-8")
        for patron in PATRONES_PROHIBIDOS:
            coincidencias = patron.findall(contenido)
            assert not coincidencias, f"Patron prohibido en {ruta.name}: {coincidencias}"


def test_docstrings_publicos():
    """Comprueba que clases y funciones publicas posean docstring explicativo."""
    for ruta in ARCHIVOS_AUDITADOS:
        if ruta.suffix != ".py":
            continue
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.iter_child_nodes(arbol):
            if isinstance(nodo, (ast.FunctionDef, ast.ClassDef)) and not nodo.name.startswith("_"):
                doc = ast.get_docstring(nodo)
                assert doc and doc.strip(), f"Sin docstring publico en {ruta.name}:{nodo.name}"


def test_cero_alias_en_archivos_auditados():
    """Comprueba la ausencia de alias de compatibilidad en archivos auditados."""
    nombres_alias_prohibidos = {"parsear_payload", "validar_y_construir_aumentada", "renderizar_estado_vacio"}
    for ruta in ARCHIVOS_AUDITADOS:
        if ruta.suffix != ".py":
            continue
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Assign):
                for target in nodo.targets:
                    if isinstance(target, ast.Name):
                        assert target.id not in nombres_alias_prohibidos, (
                            f"Alias prohibido '{target.id}' detectado en {ruta.name}"
                        )
