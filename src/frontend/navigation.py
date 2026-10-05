"""Registro central de taxonomía, navegación y redirecciones de Scalaris.

Módulo puro de Python (solo stdlib) que actúa como única fuente de verdad
para la jerarquía de pilares, herramientas, metadatos de rutas y redirecciones legacy.
"""
from __future__ import annotations

import urllib.parse
from dataclasses import dataclass


@dataclass(frozen=True)
class Pillar:
    """Representa una categoría superior o pilar conceptual en Scalaris."""
    id: str
    name: str
    icon: str = ""
    short_name: str = ""
    prefix: str = ""


@dataclass(frozen=True)
class Tool:
    """Representa una herramienta interactiva dentro de la suite."""
    id: str
    name: str
    descriptor: str
    route: str
    pillar_id: str
    icon: str
    page_title: str
    example_latex: str
    enabled: bool = True


@dataclass(frozen=True)
class LegacyRedirect:
    """Define una regla de redirección desde una URL previa hacia la nueva taxonomía."""
    path: str
    target_route: str
    fixed_query: tuple[tuple[str, str], ...] = ()
    permanent: bool = True


@dataclass(frozen=True)
class NavItem:
    """Elemento interactivo de navegación contextual para pilares y escenas."""
    key: str
    label: str
    short_label: str
    descriptor: str
    icon: str
    route: str
    query: tuple[tuple[str, str], ...]
    tool_id: str


VISUALIZER_SCENES: tuple[tuple[str, str, str, str, str], ...] = (
    ("rectas-planos", "Rectas y planos", "Rectas", "Sistemas de 2 y 3 variables", "escena_rectas_planos"),
    ("vectores", "Vectores", "Vectores", "Suma y escalamiento de u y v", "vectores"),
    ("combinacion", "Combinación lineal", "Combinación", "Cómo se forma b con tus vectores", "escena_combinacion"),
)

_SHORT_LABELS: dict[str, str] = {
    "sistemas": "Sistemas",
    "vectores": "Vectores",
    "matrices": "Matrices",
    "inversa": "Inversa",
    "bases": "Bases",
    "romanos": "Romanos",
}


# --- Constantes y Taxonomía Base ---

HUB_ENABLED: bool = True
HUB_ROUTE: str = "/"
HUB_PAGE_TITLE: str = "Inicio | Scalaris"

PILLARS: tuple[Pillar, ...] = (
    Pillar(id="algebra", name="Álgebra lineal", icon="algebra_lineal", short_name="Álgebra lineal", prefix="/algebra-lineal"),
    Pillar(id="visualizador", name="Visualizador geométrico", icon="geometria", short_name="Visualizador", prefix="/visualizador"),
    Pillar(id="utilidades", name="Utilidades numéricas", icon="utilidades", short_name="Utilidades", prefix="/utilidades"),
)

_PILLARS_BY_ID: dict[str, Pillar] = {p.id: p for p in PILLARS}

TOOLS: tuple[Tool, ...] = (
    Tool(
        id="sistemas",
        name="Sistemas de ecuaciones",
        descriptor="SEL: Gauss y Gauss-Jordan",
        route="/algebra-lineal/sistemas",
        pillar_id="algebra",
        icon="sistemas_lineales",
        page_title="Sistemas de ecuaciones lineales (SEL) | Scalaris",
        example_latex=r"A\mathbf{x} = \mathbf{b}",
        enabled=True,
    ),
    Tool(
        id="vectores",
        name="Vectores",
        descriptor="Operaciones y combinación lineal",
        route="/algebra-lineal/vectores",
        pillar_id="algebra",
        icon="vectores",
        page_title="Vectores | Scalaris",
        example_latex=r"c_1\mathbf{v}_1 + c_2\mathbf{v}_2 = \mathbf{b}",
        enabled=True,
    ),
    Tool(
        id="matrices",
        name="Matrices",
        descriptor="Expresiones, transpuesta y producto",
        route="/algebra-lineal/matrices",
        pillar_id="algebra",
        icon="operaciones_matrices",
        page_title="Matrices | Scalaris",
        example_latex=r"2A - B(C - D^{T})",
        enabled=True,
    ),
    Tool(
        id="inversa",
        name="Matriz inversa",
        descriptor="Gauss-Jordan sobre [A | I]",
        route="/algebra-lineal/inversa",
        pillar_id="algebra",
        icon="matriz_inversa",
        page_title="Matriz inversa | Scalaris",
        example_latex=r"A^{-1}",
        enabled=True,
    ),
    Tool(
        id="visualizador",
        name="Rectas, planos y vectores",
        descriptor="Escenas interactivas en R² y R³",
        route="/visualizador",
        pillar_id="visualizador",
        icon="geometria",
        page_title="Visualizador geométrico | Scalaris",
        example_latex=r"\mathbf{x} = \mathbf{p} + t\,\mathbf{d}",
        enabled=True,
    ),
    Tool(
        id="bases",
        name="Conversor de bases",
        descriptor="Decimal, binario, octal y hexadecimal",
        route="/utilidades/bases",
        pillar_id="utilidades",
        icon="conversor_bases",
        page_title="Conversor de bases | Scalaris",
        example_latex=r"1010_2 = 10_{10}",
        enabled=True,
    ),
    Tool(
        id="romanos",
        name="Números romanos",
        descriptor="Suma, resta y multiplicación",
        route="/utilidades/romanos",
        pillar_id="utilidades",
        icon="romanos",
        page_title="Números romanos | Scalaris",
        example_latex=r"\text{XIV} + \text{IX} = \text{XXIII}",
        enabled=True,
    ),
)

_TOOLS_BY_ID: dict[str, Tool] = {t.id: t for t in TOOLS}

# Orden plano para la barra de navegación en Fase 1 (se eliminará en Fase 2)
NAV_FLAT_ORDER: tuple[str, ...] = (
    "sistemas",
    "matrices",
    "inversa",
    "vectores",
    "visualizador",
    "bases",
    "romanos",
)


# --- API Pública de Navegación ---

def tool_by_id(tool_id: str) -> Tool:
    """Devuelve la Tool correspondiente al id dado.

    Raises:
        KeyError: si el id no existe en el registro.
    """
    if tool_id not in _TOOLS_BY_ID:
        raise KeyError(f"Herramienta no encontrada en el registro: '{tool_id}'")
    return _TOOLS_BY_ID[tool_id]


def route_of(tool_id: str) -> str:
    """Devuelve la ruta canónica asociada a la herramienta."""
    return tool_by_id(tool_id).route


def tool_by_route(path: str) -> Tool | None:
    """Busca y devuelve la Tool activa asociada a la ruta dada.

    Ignora cadenas de consulta (?query) y barras finales.
    Devuelve None si no coincide con ninguna ruta actual.
    """
    clean_path = path.split("?")[0].rstrip("/")
    if not clean_path:
        clean_path = "/"
    for tool in TOOLS:
        if tool.route.rstrip("/") == clean_path:
            return tool
    return None


def pillar_of(tool_id: str) -> Pillar:
    """Devuelve el Pillar al que pertenece la herramienta."""
    tool = tool_by_id(tool_id)
    return _PILLARS_BY_ID[tool.pillar_id]


def visible_tools(pillar_id: str | None = None) -> tuple[Tool, ...]:
    """Devuelve las herramientas habilitadas (enabled=True) en orden de taxonomía."""
    if pillar_id is None:
        return tuple(t for t in TOOLS if t.enabled)
    return tuple(t for t in TOOLS if t.enabled and t.pillar_id == pillar_id)


def nav_groups() -> tuple[tuple[Pillar, tuple[Tool, ...]], ...]:
    """Devuelve en el orden de PILLARS cada pilar con al menos una herramienta."""
    groups = []
    for p in PILLARS:
        tools = visible_tools(p.id)
        if tools:
            groups.append((p, tools))
    return tuple(groups)


def pillar_for_route(path: str) -> Pillar | None:
    """Encuentra el pilar al que pertenece una ruta base."""
    clean_path = path.split("?")[0].rstrip("/")
    if not clean_path:
        clean_path = "/"
    for p in PILLARS:
        if clean_path == p.prefix or clean_path.startswith(p.prefix + "/"):
            return p
    return None


def breadcrumb(route: str) -> tuple[tuple[str, str | None], ...]:
    """Genera la estructura de migas de pan para una ruta dada.

    Ejemplo: (("Álgebra lineal", None), ("Matriz inversa", "/algebra-lineal/inversa"))
    Devuelve tupla vacía si la ruta no existe en el registro.
    """
    tool = tool_by_route(route)
    if tool is None:
        return ()
    pillar = _PILLARS_BY_ID[tool.pillar_id]
    return ((pillar.name, None), (tool.name, tool.route))


def legacy_redirects() -> tuple[LegacyRedirect, ...]:
    """Devuelve la tupla de redirecciones legacy activas según el estado de HUB_ENABLED."""
    # Lectura dinámica en tiempo de llamada para permitir monkeypatching en tests
    import src.frontend.navigation as nav_mod
    hub_active = getattr(nav_mod, "HUB_ENABLED", False)

    redirects: list[LegacyRedirect] = []

    if not hub_active:
        redirects.append(LegacyRedirect(path="/", target_route="/algebra-lineal/sistemas", permanent=False))
        redirects.append(LegacyRedirect(path="/ia", target_route="/algebra-lineal/sistemas", permanent=False))
    else:
        # En F2 con Hub activado: '/' es la página Hub y '/ia' va a '/?glosa=1'
        redirects.append(LegacyRedirect(path="/ia", target_route="/", fixed_query=(("glosa", "1"),), permanent=True))

    redirects.extend([
        LegacyRedirect(path="/sistemas-lineales", target_route="/algebra-lineal/sistemas"),
        LegacyRedirect(path="/gauss", target_route="/algebra-lineal/sistemas", fixed_query=(("method", "gauss"),)),
        LegacyRedirect(path="/gauss-jordan", target_route="/algebra-lineal/sistemas", fixed_query=(("method", "gauss-jordan"),)),
        LegacyRedirect(path="/operaciones-matrices", target_route="/algebra-lineal/matrices"),
        LegacyRedirect(path="/matriz-inversa", target_route="/algebra-lineal/inversa"),
        LegacyRedirect(path="/vectores", target_route="/algebra-lineal/vectores"),
        LegacyRedirect(path="/conversor", target_route="/utilidades/bases"),
        LegacyRedirect(path="/romanos", target_route="/utilidades/romanos"),
    ])

    return tuple(redirects)


def redirect_location(redirect: LegacyRedirect, incoming_items: list[tuple[str, str]]) -> str:
    """Calcula la URL de destino final para una redirección legacy.

    Reglas de precedencia:
      1. Empieza por los pares de la query fija.
      2. Añade los pares entrantes cuya clave no esté entre las fijas.
      3. Conserva duplicados y valores vacíos.
      4. Codifica con urlencode; si no hay pares no añade '?'.
    """
    fixed_pairs: list[tuple[str, str]] = list(redirect.fixed_query)
    fixed_keys = {k for k, _ in fixed_pairs}

    for k, v in incoming_items:
        if k not in fixed_keys:
            fixed_pairs.append((k, v))

    if fixed_pairs:
        encoded_query = urllib.parse.urlencode(fixed_pairs)
        return f"{redirect.target_route}?{encoded_query}"
    return redirect.target_route


def nav_items(pillar_id: str) -> tuple[NavItem, ...]:
    """Devuelve los items de navegacion contextual asociados a un pilar."""
    if pillar_id in ("algebra", "algebra-lineal"):
        order = ("sistemas", "vectores", "matrices", "inversa")
        items = []
        for tid in order:
            t = tool_by_id(tid)
            items.append(
                NavItem(
                    key=t.id,
                    label=t.name,
                    short_label=_SHORT_LABELS[t.id],
                    descriptor=t.descriptor,
                    icon=t.icon,
                    route=t.route,
                    query=(),
                    tool_id=t.id,
                )
            )
        return tuple(items)

    if pillar_id in ("visualizador", "geometria"):
        items = []
        for escena, label, short_label, descriptor, icon in VISUALIZER_SCENES:
            items.append(
                NavItem(
                    key=f"vis:{escena}",
                    label=label,
                    short_label=short_label,
                    descriptor=descriptor,
                    icon=icon,
                    route="/visualizador",
                    query=(("escena", escena),),
                    tool_id="visualizador",
                )
            )
        return tuple(items)

    if pillar_id in ("utilidades", "utilidades-numericas"):
        order = ("bases", "romanos")
        items = []
        for tid in order:
            t = tool_by_id(tid)
            items.append(
                NavItem(
                    key=t.id,
                    label=t.name,
                    short_label=_SHORT_LABELS[t.id],
                    descriptor=t.descriptor,
                    icon=t.icon,
                    route=t.route,
                    query=(),
                    tool_id=t.id,
                )
            )
        return tuple(items)

    return ()


def nav_item_href(item: NavItem) -> str:
    """Calcula la URL de destino del item con query string codificada si existe."""
    if item.query:
        return f"{item.route}?{urllib.parse.urlencode(item.query)}"
    return item.route


def default_item_key(route: str) -> str | None:
    """Obtiene la clave del item de navegacion predeterminado para una ruta."""
    tool = tool_by_route(route)
    if tool is None:
        return None
    if tool.id == "visualizador":
        return "vis:rectas-planos"
    return tool.id
