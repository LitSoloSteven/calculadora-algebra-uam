import re
from typing import TypedDict, Optional

# Expresiones regulares para clasificar pasos elementales de Gauss-Jordan
RE_INICIAL = r"^Matriz inicial"
RE_INTERCAMBIO = r"^Intercambio: Fila (\d+) ↔ Fila (\d+)"
RE_PIVOTE = r"^Pivote seleccionado en Fila (\d+), Columna (\d+)"
RE_ELIMINACION = r"^Fila (\d+) = Fila \1 − \((.+)\) · Fila (\d+)$"
RE_NORMALIZA = r"^Normalizar pivote(?: a 1)?: Fila (\d+) = Fila \1 / (.+)$"

class ParsedParams(TypedDict):
    kind: str
    row1: Optional[int]
    row2: Optional[int]
    col: Optional[int]
    val_str: Optional[str]

def classify_step(desc: str) -> ParsedParams:
    res: ParsedParams = {
        "kind": "otro",
        "row1": None,
        "row2": None,
        "col": None,
        "val_str": None
    }
    
    if re.match(RE_INICIAL, desc):
        res["kind"] = "inicial"
        return res
        
    m_swap = re.match(RE_INTERCAMBIO, desc)
    if m_swap:
        res["kind"] = "intercambio"
        res["row1"] = int(m_swap.group(1)) - 1
        res["row2"] = int(m_swap.group(2)) - 1
        return res
        
    m_piv = re.match(RE_PIVOTE, desc)
    if m_piv:
        res["kind"] = "pivote"
        res["row1"] = int(m_piv.group(1)) - 1
        res["col"] = int(m_piv.group(2)) - 1
        return res
        
    m_elim = re.match(RE_ELIMINACION, desc)
    if m_elim:
        res["kind"] = "eliminacion"
        res["row1"] = int(m_elim.group(1)) - 1
        res["row2"] = int(m_elim.group(3)) - 1
        res["val_str"] = m_elim.group(2)
        return res
        
    m_norm = re.match(RE_NORMALIZA, desc)
    if m_norm:
        res["kind"] = "normalizacion"
        res["row1"] = int(m_norm.group(1)) - 1
        res["val_str"] = m_norm.group(2)
        return res
        
    return res
