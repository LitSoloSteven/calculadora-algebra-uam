from fractions import Fraction

def to_float(value) -> float:
    """Convierte int/float/Fraction/str ('1/2', '9/7', '-3', '0.25') a float.
    Lanza ValueError si no es convertible (incluye '1/0' y '')."""
    try:
        return float(Fraction(str(value).strip()))
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        raise ValueError(f"Valor no numérico: {value!r}") from e

def format_step_for_mathjax(paso: str) -> str:
    """Prepara un paso para ir entre $$ ... $$.
    Si tiene prefijo de texto ('Ecuación 1: ...') lo envuelve en \\text{}.
    Si ya viene envuelto por el backend (empieza con \\text) no lo toca."""
    s = str(paso).strip()
    if s.startswith('\\text'):
        return s
    head, sep, tail = s.partition(':')
    if sep and head and not any(c in head for c in '\\{}^_='):
        return rf"\text{{{head}:}}\;{tail}"
    return s
