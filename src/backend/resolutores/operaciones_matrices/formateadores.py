"""Formateadores especificos de LaTeX para operaciones con matrices."""

from src.backend.constantes import TOLERANCIA_COINCIDENCIA_FRACCION
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import numero_a_latex


def matriz_a_latex(matriz: Matriz, eps: float = TOLERANCIA_COINCIDENCIA_FRACCION) -> str:
    """Renderiza una matriz en formato LaTeX bmatrix."""
    filas_str = []
    for r in range(matriz.filas):
        valores = [numero_a_latex(matriz.obtener(r, c)) for c in range(matriz.columnas)]
        filas_str.append(" & ".join(valores))
    cuerpo = " \\\\\n".join(filas_str)
    return f"\\begin{{bmatrix}}\n{cuerpo}\n\\end{{bmatrix}}"


def sumar_restar_matriz_a_latex(
    matriz_a: Matriz,
    matriz_b: Matriz,
    operador: str = "+",
) -> str:
    """Renderiza la suma o resta elemento a elemento en formato LaTeX."""
    filas_str = []
    for r in range(matriz_a.filas):
        valores = []
        for c in range(matriz_a.columnas):
            a_str = numero_a_latex(matriz_a.obtener(r, c))
            b_str = numero_a_latex(matriz_b.obtener(r, c))
            a_fmt = f"({a_str})" if a_str.startswith("-") else a_str
            b_fmt = f"({b_str})" if b_str.startswith("-") else b_str
            valores.append(f"{a_fmt} {operador} {b_fmt}")
        filas_str.append(" & ".join(valores))
    cuerpo = " \\\\\n".join(filas_str)
    return f"\\begin{{bmatrix}}\n{cuerpo}\n\\end{{bmatrix}}"


def multiplicar_matriz_a_latex(matriz_a: Matriz, matriz_b: Matriz) -> str:
    """Renderiza el producto matricial fila por columna en formato LaTeX."""
    m, n, q = matriz_a.filas, matriz_a.columnas, matriz_b.columnas
    filas_str = []
    for r in range(m):
        valores = []
        for c in range(q):
            terminos = []
            for k in range(n):
                a_str = numero_a_latex(matriz_a.obtener(r, k))
                b_str = numero_a_latex(matriz_b.obtener(k, c))
                terminos.append(f"({a_str})({b_str})")
            valores.append(" + ".join(terminos))
        filas_str.append(" & ".join(valores))
    cuerpo = " \\\\\n".join(filas_str)
    return f"\\begin{{bmatrix}}\n{cuerpo}\n\\end{{bmatrix}}"


def matriz_particionada_a_latex(matriz: Matriz, num_columnas_izq: int) -> str:
    """Renderiza una matriz aumentada particionada con linea vertical divisoria."""
    total = matriz.columnas
    derecha = total - num_columnas_izq
    if num_columnas_izq < 1 or derecha < 1:
        return matriz_a_latex(matriz)

    especificacion = ("c" * num_columnas_izq) + "|" + ("c" * derecha)
    filas = []
    for i in range(matriz.filas):
        valores = [numero_a_latex(matriz.obtener(i, j)) for j in range(total)]
        filas.append(" & ".join(valores))
    cuerpo = " \\\\ ".join(filas)
    return rf"\left[ \begin{{array}}{{{especificacion}}} {cuerpo} \end{{array}} \right]"
