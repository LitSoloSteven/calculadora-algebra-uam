from fractions import Fraction

def to_float(value) -> float:
    """Convierte int/float/Fraction/str ('1/2', '9/7', '-3', '0.25') a float.
    Lanza ValueError si no es convertible (incluye '1/0' y '')."""
    try:
        return float(Fraction(str(value).strip()))
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        raise ValueError(f"Valor no numérico: {value!r}") from e
