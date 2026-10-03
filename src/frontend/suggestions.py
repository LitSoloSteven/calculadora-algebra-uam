from dataclasses import dataclass, field
from typing import Protocol

from src.frontend import flags

@dataclass(frozen=True)
class InvalidCell:
    label: str
    focus: tuple[int, int] | None = None

@dataclass(frozen=True)
class Signals:
    tool: str
    state: str
    flags: frozenset[str] = field(default_factory=frozenset)
    invalid: InvalidCell | None = None

@dataclass(frozen=True)
class Suggestion:
    id: str
    text: str
    role: str
    focus: tuple[int, int] | None = None

@dataclass(frozen=True)
class FollowUp:
    id: str
    label: str
    question: str
    simpler: bool = False

FOLLOW_UPS = (
    FollowUp("simpler", "Más simple", "Explícalo de forma más simple", True),
    FollowUp("example", "Con un ejemplo numérico", "Dame un ejemplo numérico de eso"),
    FollowUp("why", "¿Por qué funciona?", "¿Por qué funciona?"),
)

_CATALOG = [
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
]

import os

def glosa_configured() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY", "").strip())

def first_invalid_cell(items) -> InvalidCell | None:
    from src.backend.utils.validators import MatrixValidator
    for item in items:
        label = item[0]
        valor = item[1]
        focus = item[2] if len(item) > 2 else None
        
        val_str = str(valor).strip() if valor is not None else ""
        if not val_str or val_str in ('0', '0.0'):
            continue
        ok, _, _ = MatrixValidator.parse_number_exact(val_str)
        if not ok:
            return InvalidCell(label=label, focus=focus)
    return None

def chips_active() -> bool:
    return flags.dock_enabled() and flags.proactive_enabled()

def candidates(signals: Signals | None) -> list[Suggestion]:
    if not signals:
        return []
    
    cands = []
    
    if signals.state == "none" and signals.invalid:
        label = signals.invalid.label
        if len(label) > 24:
            label = label[:23] + "…"
        cands.append(Suggestion(
            id=f"{signals.tool}.invalid",
            text=f"¿Por qué {label} no es válido?",
            role="specific",
            focus=signals.invalid.focus
        ))
        
    for tool, trigger, id_, text, role in _CATALOG:
        if tool != signals.tool:
            continue
            
        match = False
        if trigger == signals.state:
            match = True
        elif trigger.startswith("flag_") and trigger[5:] in signals.flags:
            flag_name = trigger[5:]
            if tool == "matrices" and flag_name == "has_product" and signals.state != "ok":
                match = False
            elif tool == "bases" and signals.state != "result":
                match = False
            elif tool == "romanos" and signals.state not in ("ok", "error"):
                match = False
            else:
                match = True
                
        if match:
            cands.append(Suggestion(id=id_, text=text, role=role))
            
    return cands

def select_chips(cands: list[Suggestion], limit: int) -> list[Suggestion]:
    specifics = [c for c in cands if c.role == "specific"]
    states = [c for c in cands if c.role == "state"]
    flags_list = [c for c in cands if c.role == "flag"]
    
    selected = []
    selected.extend(specifics)
    
    for s in states[:2]:
        if s not in selected:
            selected.append(s)
            
    if flags_list:
        if flags_list[0] not in selected:
            selected.append(flags_list[0])
            
    for s in states[2:]:
        if s not in selected:
            selected.append(s)
            
    for f in flags_list[1:]:
        if f not in selected:
            selected.append(f)
            
    return selected[:limit]

def suggest(signals: Signals | None, *, limit: int = 3, include_specific: bool = True) -> list[Suggestion]:
    cands = candidates(signals)
    if not include_specific:
        cands = [c for c in cands if c.role != "specific"]
    return select_chips(cands, limit)

class SuggestionProvider(Protocol):
    def get_ai_signals(self) -> Signals | None:
        ...
