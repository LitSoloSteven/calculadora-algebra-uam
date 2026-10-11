"""Pruebas de cumplimiento estricto de las reglas SCALARIS.

Audita límites duros (líneas, funciones, complejidad, anidamiento, parámetros),
docstrings, comentarios prohibidos, convenciones de idioma, CSS y frontend.
La lista RUTAS_AUDITADAS comienza vacía en la Fase 0 y crece en cada fase.
"""

import ast
from pathlib import Path
import re

RAIZ = Path(__file__).resolve().parent.parent

# Lista de rutas bajo auditoría formal que se amplía en cada fase cerrada
RUTAS_AUDITADAS: list[Path] = [
    RAIZ / "src" / "backend" / "constantes.py",
    RAIZ / "src" / "backend" / "excepciones.py",
    RAIZ / "src" / "backend" / "modelos" / "matriz.py",
    RAIZ / "src" / "backend" / "utilidades" / "analizadores.py",
    RAIZ / "src" / "backend" / "utilidades" / "formateadores.py",
    RAIZ / "src" / "backend" / "utilidades" / "utilidades_matematicas.py",
    RAIZ / "src" / "backend" / "utilidades" / "validadores.py",
    RAIZ / "src" / "backend" / "utilidades" / "verificacion.py",
    RAIZ / "src" / "backend" / "utilidades" / "reglas_dominio.py",
]

PALABRAS_INGLES_PROHIBIDAS = {
    "solver", "solvers", "matrix", "rows", "cols", "solve",
    "step", "steps", "controller", "view", "components", "models",
}

EXCEPCIONES_E4_PERMITIDAS = {
    "app", "main", "ui", "props", "classes", "style", "value",
    "on_click", "on_change", "slot", "row", "column", "card",
    "button", "input", "label", "icon", "dialog", "select",
}

PATRONES_COMENTARIOS_PROHIBIDOS = [
    re.compile(r"^\s*#\s*[-=*#]{3,}", re.MULTILINE),
    re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE),
    re.compile(r"\b(F8[a-z]?|F4|F9[a-z]?|LIT-\d+|Paso\s+\d+)\b", re.IGNORECASE),
    re.compile(r"[\U00010000-\U0010ffff]", re.UNICODE),
    re.compile(r"—"),
]


def _calcular_anidamiento_y_complejidad(nodo: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[int, int]:
    """Calcula el anidamiento máximo de bloques y la complejidad ciclomática aproximada."""
    max_profundidad = 0
    complejidad = 1
    bloques_anidados = (ast.If, ast.For, ast.While, ast.Try, ast.With)

    def _visitar(subnodo: ast.AST, profundidad_actual: int) -> None:
        nonlocal max_profundidad, complejidad
        es_bloque = isinstance(subnodo, bloques_anidados)
        nueva_profundidad = profundidad_actual + (1 if es_bloque else 0)
        if nueva_profundidad > max_profundidad:
            max_profundidad = nueva_profundidad

        if isinstance(subnodo, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
            complejidad += 1
        elif isinstance(subnodo, ast.BoolOp):
            complejidad += len(subnodo.values) - 1

        for hijo in ast.iter_child_nodes(subnodo):
            if not isinstance(hijo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                _visitar(hijo, nueva_profundidad)

    for hijo in ast.iter_child_nodes(nodo):
        _visitar(hijo, 0)

    return max_profundidad, complejidad


def test_sin_marcadores_de_conflicto_global():
    """Verifica que ningún archivo de código contenga marcadores de git."""
    extensiones = {".py", ".js", ".css", ".html"}
    patron = re.compile(r"^(<{7}|={7}|>{7})(?:[ \t\r\n]|$)", re.MULTILINE)
    archivos = [
        p for p in RAIZ.glob("src/**/*") if p.is_file() and p.suffix in extensiones
    ] + [
        p for p in RAIZ.glob("tests/**/*.py") if p.is_file()
    ]
    for ruta in archivos:
        contenido = ruta.read_text(encoding="utf-8", errors="ignore")
        assert not patron.findall(contenido), f"Marcador de conflicto en {ruta.name}"


def test_limites_tamanio_y_complejidad():
    """Audita límites de 300 líneas por archivo, 40 por función y 200 por clase."""
    for ruta in RUTAS_AUDITADAS:
        if not ruta.exists():
            continue
        lineas = ruta.read_text(encoding="utf-8").splitlines()
        assert len(lineas) <= 300, f"{ruta.name} tiene {len(lineas)} líneas (máximo 300)"

        if ruta.suffix != ".py":
            continue
        arbol = ast.parse("\n".join(lineas), filename=str(ruta))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ClassDef):
                alt = (nodo.end_lineno or nodo.lineno) - nodo.lineno + 1
                assert alt <= 200, f"{ruta.name}:{nodo.name} tiene {alt} líneas (máximo 200)"
            elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                alt = (nodo.end_lineno or nodo.lineno) - nodo.lineno + 1
                assert alt <= 40, f"{ruta.name}:{nodo.name} tiene {alt} líneas (máximo 40)"
                params = [a.arg for a in nodo.args.args if a.arg not in ("self", "cls")]
                assert len(params) <= 5, f"{ruta.name}:{nodo.name} tiene {len(params)} parámetros"
                anid, comp = _calcular_anidamiento_y_complejidad(nodo)
                assert anid <= 3, f"{ruta.name}:{nodo.name} anidamiento {anid} (máximo 3)"
                assert comp <= 10, f"{ruta.name}:{nodo.name} complejidad {comp} (máximo 10)"


def test_docstrings_publicos():
    """Verifica que toda clase y función pública posea docstring no vacío."""
    for ruta in RUTAS_AUDITADAS:
        if ruta.suffix != ".py" or not ruta.exists():
            continue
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.iter_child_nodes(arbol):
            if isinstance(nodo, (ast.FunctionDef, ast.ClassDef)) and not nodo.name.startswith("_"):
                doc = ast.get_docstring(nodo)
                assert doc and doc.strip(), f"Sin docstring público en {ruta.name}:{nodo.name}"


def test_identificadores_idioma_y_ascii():
    """Comprueba identificadores en ASCII y ausencia de nombres ingleses prohibidos."""
    for ruta in RUTAS_AUDITADAS:
        if ruta.suffix != ".py" or not ruta.exists():
            continue
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.walk(arbol):
            nombre = getattr(nodo, "id", None) or getattr(nodo, "name", None)
            if not isinstance(nombre, str) or nombre.startswith("__"):
                continue
            assert nombre.isascii(), f"Identificador no ASCII '{nombre}' en {ruta.name}"
            partes = set(re.split(r"[_\d]+", nombre.lower()))
            conflictos = (partes & PALABRAS_INGLES_PROHIBIDAS) - EXCEPCIONES_E4_PERMITIDAS
            assert not conflictos, f"Términos en inglés {conflictos} en {ruta.name}:{nombre}"


def test_comentarios_y_copy_limpios():
    """Valida ausencia de banners, TODO, FIXME, emojis y raya larga."""
    for ruta in RUTAS_AUDITADAS:
        if not ruta.exists():
            continue
        contenido = ruta.read_text(encoding="utf-8")
        for patron in PATRONES_COMENTARIOS_PROHIBIDOS:
            coincidencias = patron.findall(contenido)
            assert not coincidencias, f"Patrón prohibido en {ruta.name}: {coincidencias}"


def test_reglas_css():
    """Valida reglas de movimiento, tokens de color y ausencia de vh en hojas CSS."""
    for ruta in RUTAS_AUDITADAS:
        if ruta.suffix != ".css" or not ruta.exists():
            continue
        css = ruta.read_text(encoding="utf-8")
        assert not re.search(r"\b\d+vh\b", css), f"Uso de 'vh' prohibido en {ruta.name}"
        assert not re.search(r"transition:\s*all\b", css), f"transition: all en {ruta.name}"
        assert not re.search(r"ease-in\b", css), f"ease-in prohibido en {ruta.name}"
        duraciones = [int(m) for m in re.findall(r"(\d+)ms", css)]
        assert all(d <= 250 for d in duraciones), f"Duración > 250ms en {ruta.name}"


def test_reglas_python_frontend():
    """Valida ausencia de estilos en línea y cadenas extensas embebidas en Python."""
    for ruta in RUTAS_AUDITADAS:
        if ruta.suffix != ".py" or not ruta.exists():
            continue
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
                val = nodo.value
                assert 'style="' not in val and "style='" not in val, (
                    f"Estilos en línea detectados en {ruta.name}"
                )
                if any(etiqueta in val for etiqueta in ("<div", "<span", "<table", "<button")):
                    lineas = val.strip().splitlines()
                    assert len(lineas) <= 3, (
                        f"HTML embebido de {len(lineas)} líneas (> 3) en {ruta.name}"
                    )
