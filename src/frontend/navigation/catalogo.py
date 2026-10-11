"""Catálogo declarativo de pilares, herramientas y escenas de Scalaris."""
from src.frontend.navigation.modelo import Pillar, Tool

HUB_ENABLED: bool = True
HUB_ROUTE: str = "/"
HUB_PAGE_TITLE: str = "Inicio | Scalaris"

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
    "leontief": "Leontief",
    "transformaciones": "Transformaciones",
}

PILLARS: tuple[Pillar, ...] = (
    Pillar(
        id="algebra",
        name="Álgebra lineal",
        icon="algebra_lineal",
        short_name="Álgebra lineal",
        prefix="/algebra-lineal",
    ),
    Pillar(
        id="visualizador",
        name="Visualizador geométrico",
        icon="geometria",
        short_name="Visualizador",
        prefix="/visualizador",
    ),
    Pillar(
        id="utilidades",
        name="Utilidades numéricas",
        icon="utilidades",
        short_name="Utilidades",
        prefix="/utilidades",
    ),
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
    Tool(
        id="leontief",
        name="Modelo de Leontief",
        descriptor="Insumo-producto: x = (I - C)^(-1) d",
        route="/algebra-lineal/leontief",
        pillar_id="algebra",
        icon="matriz_inversa",
        page_title="Modelo de Leontief | Scalaris",
        example_latex=r"x = (I - C)^{-1}\,d",
        enabled=True,
    ),
    Tool(
        id="transformaciones",
        name="Transformaciones Lineales",
        descriptor="ker(T), Im(T), rango y nulidad",
        route="/algebra-lineal/transformaciones",
        pillar_id="algebra",
        icon="operaciones_matrices",
        page_title="Transformaciones Lineales | Scalaris",
        example_latex=r"T: \mathbb{R}^n \to \mathbb{R}^m",
        enabled=True,
    ),
)

_TOOLS_BY_ID: dict[str, Tool] = {t.id: t for t in TOOLS}

NAV_FLAT_ORDER: tuple[str, ...] = (
    "sistemas",
    "matrices",
    "inversa",
    "vectores",
    "leontief",
    "transformaciones",
    "visualizador",
    "bases",
    "romanos",
)
