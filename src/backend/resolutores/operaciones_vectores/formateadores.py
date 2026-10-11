"""Formateadores LaTeX específicos para el dominio vectorial."""

from fractions import Fraction
import re

from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import numero_a_latex


def vector_a_latex(v: Matriz) -> str:
    """Renderiza un vector como matriz LaTeX bmatrix."""
    if v.filas == 1 and v.columnas > 1:
        columnas = [numero_a_latex(v.obtener(0, j)) for j in range(v.columnas)]
        return r"\begin{bmatrix} " + r" & ".join(columnas) + r" \end{bmatrix}"
    filas = [numero_a_latex(v.obtener(i, 0)) for i in range(v.filas)]
    return r"\begin{bmatrix} " + r" \\ ".join(filas) + r" \end{bmatrix}"


def vector_columna_a_latex(v: Matriz) -> str:
    """Renderiza un vector columna como matriz LaTeX bmatrix."""
    return vector_a_latex(v)


def matriz_aumentada_gauss_a_latex(m: Matriz, num_vars: int | None = None) -> str:
    """Renderiza una matriz aumentada con barra divisoria vertical."""
    conteo_vars = (m.columnas - 1) if num_vars is None else num_vars
    espec_columnas = ("c" * conteo_vars) + "|c"
    filas = []
    for i in range(m.filas):
        vals_fila = [numero_a_latex(m.obtener(i, j)) for j in range(m.columnas)]
        filas.append(" & ".join(vals_fila))
    cuerpo = " \\\\ ".join(filas)
    return rf"\left[ \begin{{array}}{{{espec_columnas}}} {cuerpo} \end{{array}} \right]"


def formatear_variable_latex(nombre_var: str) -> str:
    """Normaliza el nombre de una variable a modo matemático LaTeX."""
    if nombre_var.startswith("\\"):
        return nombre_var
    m = re.match(r"^([a-zA-Z]+)_?(\d+)$", nombre_var)
    if m:
        letras, digitos = m.groups()
        return f"{letras}_{{{digitos}}}"
    return nombre_var


def formatear_vector_latex(nombre_vec: str) -> str:
    """Formatea el símbolo de un vector en negrita canónica LaTeX."""
    if nombre_vec.startswith(r"\mathbf{"):
        return nombre_vec
    m = re.match(r"^([a-zA-Z]+)_?(\d+)$", nombre_vec)
    if m:
        letras, digitos = m.groups()
        if len(digitos) == 1:
            return rf"\mathbf{{{letras}}}_{digitos}"
        return rf"\mathbf{{{letras}}}_{{{digitos}}}"
    return rf"\mathbf{{{nombre_vec}}}"


def formatear_componente_escalar(val: Fraction | int | float, var: str) -> str:
    """Formatea la multiplicación de un escalar por una variable."""
    f = Fraction(val)
    if f == 0:
        return "0"
    if f == 1:
        return var
    if f == -1:
        return f"-{var}"
    if f.denominator == 1:
        return f"{f.numerator} {var}"
    return f"{numero_a_latex(f)} {var}"


def formatear_expresion_lineal(coefs: list[Fraction | int | float], variables: list[str]) -> str:
    """Combina los términos de una fila en una expresión lineal respetando signos."""
    partes = []
    for c_bruto, var in zip(coefs, variables):
        c = Fraction(c_bruto)
        if c == 0:
            continue
        c_abs = abs(c)
        if c_abs == 1:
            termino = var
        elif c_abs.denominator == 1:
            termino = f"{c_abs.numerator} {var}"
        else:
            termino = f"{numero_a_latex(c_abs)} {var}"

        if not partes:
            partes.append(f"-{termino}" if c < 0 else termino)
        else:
            signo = "-" if c < 0 else "+"
            partes.append(f"{signo} {termino}")
    return " ".join(partes) if partes else "0"


def matriz_aumentada_a_latex(vectores: list[Matriz], b: Matriz) -> str:
    """Renderiza la matriz aumentada [A | b] con línea divisoria."""
    k = len(vectores)
    n = b.filas
    espec_columnas = ("c" * k) + "|c"
    filas = []
    for i in range(n):
        vals_fila = [numero_a_latex(vectores[j].obtener(i, 0)) for j in range(k)]
        vals_fila.append(numero_a_latex(b.obtener(i, 0)))
        filas.append(" & ".join(vals_fila))
    cuerpo = " \\\\ ".join(filas)
    return rf"\left[ \begin{{array}}{{{espec_columnas}}} {cuerpo} \end{{array}} \right]"


def formatear_combinacion_lineal_vector(
    coefs: list[Fraction | int | float], nombres_vec: list[str]
) -> str:
    """Formatea la combinación escalar-vector para la comprobación formal."""
    partes = []
    for c_bruto, v_nombre in zip(coefs, nombres_vec):
        c = Fraction(c_bruto)
        v_tex = formatear_vector_latex(v_nombre)
        if c == 0:
            continue
        c_abs = abs(c)
        if c_abs == 1:
            termino = v_tex
        elif c_abs.denominator == 1:
            termino = f"{c_abs.numerator}{v_tex}"
        else:
            termino = f"{numero_a_latex(c_abs)}{v_tex}"

        if not partes:
            partes.append(f"-{termino}" if c < 0 else termino)
        else:
            signo = "-" if c < 0 else "+"
            partes.append(f"{signo} {termino}")
    return " ".join(partes) if partes else "0"
