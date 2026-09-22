from typing import List

def mcd(a: int, b: int) -> int:
    """Calcula el Máximo Común Divisor (Algoritmo de Euclides)."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a

def mcm(a: int, b: int) -> int:
    """Calcula el Mínimo Común Múltiplo de dos enteros."""
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // mcd(a, b)

def mcd_lista(numeros: List[int]) -> int:
    """Calcula el MCD de una lista de enteros."""
    numeros_no_cero = [abs(x) for x in numeros if x != 0]
    if not numeros_no_cero:
        return 1
    res = numeros_no_cero[0]
    for num in numeros_no_cero[1:]:
        res = mcd(res, num)
    return res

def simplificar_fila(fila: List[int]) -> List[int]:
    """Reduce los coeficientes de una fila dividiéndolos entre su MCD."""
    factor = mcd_lista(fila)
    if factor <= 1:
        return fila
    return [elem // factor for elem in fila]