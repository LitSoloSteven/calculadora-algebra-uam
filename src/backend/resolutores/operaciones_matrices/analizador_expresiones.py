"""Analizador léxico y sintáctico para expresiones matriciales mediante RPN."""

import re


def tokenizar_expresion(expr: str) -> list[str]:
    """Convierte la cadena en tokens e inserta multiplicaciones implícitas."""
    expr_limpia = expr.replace(" ", "").replace("^T", "ᵀ").replace("^t", "ᵀ")
    patron = re.compile(
        r"\d+\.\d+|\d+|[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]*|[A-Za-z][0-9]+|[A-Za-z]|ᵀ|[\+\-\*\(\)]"
    )
    tokens_brutos = patron.findall(expr_limpia)
    if "".join(tokens_brutos) != expr_limpia:
        raise ValueError("La expresión contiene caracteres no soportados (p. ej. '/').")

    tokens = []
    for i, token in enumerate(tokens_brutos):
        if token == "-" and (i == 0 or tokens_brutos[i - 1] in ("(", "+", "-", "*")):
            tokens.append("¬")
            continue
        tokens.append(token)
        if i < len(tokens_brutos) - 1:
            sig = tokens_brutos[i + 1]
            es_act = bool(re.match(r"^[A-Za-z]|\d|\)|ᵀ", token))
            es_sig = bool(re.match(r"^[A-Za-z]|\d|\(", sig))
            if es_act and es_sig:
                tokens.append("*")
    return tokens


def _manejar_cierre_parentesis(pila: list[str], salida: list[str]) -> None:
    """Vacía la pila hasta encontrar el paréntesis de apertura correspondiente."""
    while pila and pila[-1] != "(":
        salida.append(pila.pop())
    if not pila:
        raise ValueError("Error de sintaxis: Paréntesis desbalanceados.")
    pila.pop()


def _manejar_operador(
    t: str, pila: list[str], salida: list[str], precedencia: dict[str, int]
) -> None:
    """Mueve operadores de mayor o igual precedencia a la salida y apila el actual."""
    while pila and pila[-1] != "(":
        prec_tope = precedencia.get(pila[-1], 0)
        prec_act = precedencia[t]
        condicion = prec_tope > prec_act or (prec_tope == prec_act and t != "¬")
        if not condicion:
            break
        salida.append(pila.pop())
    pila.append(t)


def convertir_a_rpn(tokens: list[str]) -> list[str]:
    """Aplica Shunting-Yard para convertir tokens a Notación Polaca Inversa."""
    precedencia = {"+": 1, "-": 1, "*": 2, "ᵀ": 3, "¬": 4}
    salida, pila = [], []
    for t in tokens:
        if re.match(r"^[A-Za-z][A-Za-z0-9_]*$|^\d+(\.\d+)?$", t):
            salida.append(t)
            continue
        if t == "(":
            pila.append(t)
            continue
        if t == ")":
            _manejar_cierre_parentesis(pila, salida)
            continue
        if t in precedencia:
            _manejar_operador(t, pila, salida, precedencia)

    while pila:
        tope = pila.pop()
        if tope in "()":
            raise ValueError("Error de sintaxis: Paréntesis desbalanceados.")
        salida.append(tope)
    return salida
