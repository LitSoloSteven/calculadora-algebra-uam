"""Catálogo declarativo puro de sugerencias contextuales y follow-ups."""
from dataclasses import dataclass


@dataclass(frozen=True)
class FollowUp:
    """Opción de profundización posterior en una respuesta de Glosa."""

    id: str
    label: str
    question: str
    simpler: bool = False


FOLLOW_UPS: tuple[FollowUp, ...] = (
    FollowUp("simpler", "Más simple", "Explícalo de forma más simple", True),
    FollowUp("example", "Con un ejemplo numérico", "Dame un ejemplo numérico de eso"),
    FollowUp("why", "¿Por qué funciona?", "¿Por qué funciona?"),
)

CATALOGO_SUGERENCIAS: tuple[tuple[str, str, str, str, str], ...] = (
    # Sistemas
    ("sistemas", "none", "sistemas.none.metodo", "¿Qué método uso, Gauss o Gauss-Jordan?", "state"),
    ("sistemas", "none", "sistemas.none.fracciones", "¿Cómo escribo fracciones y decimales?", "state"),
    ("sistemas", "unique", "sistemas.unica.comprobar", "¿Cómo compruebo la solución?", "state"),
    ("sistemas", "unique", "sistemas.unica.geometria", "¿Qué significa geométricamente?", "state"),
    ("sistemas", "infinite", "sistemas.inf.porque", "¿Por qué tiene infinitas soluciones?", "state"),
    ("sistemas", "infinite", "sistemas.inf.libre", "¿Qué es una variable libre?", "state"),
    ("sistemas", "infinite", "sistemas.inf.parametrica", "¿Cómo leo la solución paramétrica?", "state"),
    ("sistemas", "no_solution", "sistemas.nosol.porque", "¿Por qué no tiene solución?", "state"),
    ("sistemas", "no_solution", "sistemas.nosol.matriz", "¿Cómo se ve una inconsistencia en la matriz?", "state"),
    ("sistemas", "flag_swap", "sistemas.flag.swap", "¿Por qué se intercambiaron filas?", "flag"),
    ("sistemas", "flag_m_gt_n", "sistemas.flag.mgtn", "¿Qué cambia si hay más ecuaciones que incógnitas?", "flag"),
    # Inversa
    ("inversa", "none", "inversa.none.existe", "¿Cuándo existe la inversa?", "state"),
    ("inversa", "success", "inversa.ok.identidad", "¿Por qué la identidad queda a la izquierda?", "state"),
    ("inversa", "success", "inversa.ok.verificar", "¿Cómo verifico A·A⁻¹ = I?", "state"),
    ("inversa", "success", "inversa.ok.sistema", "¿Qué relación tiene con Ax = b?", "state"),
    ("inversa", "singular", "inversa.sing.det", "¿Qué significa que el determinante sea cero?", "state"),
    ("inversa", "singular", "inversa.sing.porque", "¿Por qué una matriz singular no tiene inversa?", "state"),
    # Matrices
    ("matrices", "empty", "matrices.empty.sintaxis", "¿Qué sintaxis acepto, por ejemplo 2A − B(C − Dᵀ)?", "state"),
    ("matrices", "dim_error", "matrices.dim.porque", "¿Por qué no puedo operar estas dimensiones?", "state"),
    ("matrices", "flag_has_product", "matrices.flag.ab", "¿Por qué AB no es igual a BA?", "flag"),
    # Vectores
    ("vectores", "flag_orient_mix", "vectores.flag.orient", "¿Qué pasa si uno es fila y el otro columna?", "flag"),
    ("vectores", "flag_neg_scalar", "vectores.flag.neg", "¿Qué hace geométricamente un escalar negativo?", "flag"),
    ("vectores", "unique", "vectores.lc.unica", "¿Cómo se relaciona con Ax = b?", "state"),
    ("vectores", "infinite", "vectores.lc.inf", "¿Por qué hay infinitas combinaciones?", "state"),
    ("vectores", "infinite", "vectores.lc.dep", "¿Qué es dependencia lineal?", "state"),
    ("vectores", "no_solution", "vectores.lc.span", "¿Qué significa que b no esté en el span?", "state"),
    # Bases
    ("bases", "flag_division", "bases.div", "¿Por qué las divisiones se leen de abajo hacia arriba?", "state"),
    ("bases", "flag_hex", "bases.hex", "¿Por qué hex agrupa bits de 4 en 4?", "state"),
    # Romanos
    ("romanos", "flag_err_sub_zero", "romanos.err.cero", "¿Por qué no existe el cero romano?", "state"),
    ("romanos", "flag_err_sub_neg", "romanos.err.neg", "¿Por qué no hay números negativos en romano?", "state"),
    ("romanos", "flag_err_syntax", "romanos.err.sintaxis", "¿Por qué IIII no es válido?", "state"),
    ("romanos", "flag_op_mult", "romanos.mult", "¿Por qué solo multiplico de un dígito?", "state"),
    # Visualizador
    ("visualizador", "flag_parallel", "visualizador.parallel", "¿Qué significa que las rectas sean paralelas?", "flag"),
    ("visualizador", "result", "visualizador.span", "¿Qué es el span de estos vectores?", "state"),
)
