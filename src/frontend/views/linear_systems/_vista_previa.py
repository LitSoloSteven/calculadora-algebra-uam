"""Transformaciones puras para los datos de la vista previa de sistemas."""

from dataclasses import dataclass
from fractions import Fraction
import re

from src.backend.models.matrix import Matrix
from src.backend.resolutores.operaciones_vectores.formateadores import (
    matriz_aumentada_gauss_a_latex as augmented_gauss_matrix_to_latex,
    formatear_expresion_lineal as format_linear_expression,
)
from src.backend.utils.formatters import format_variable_for_latex, number_to_latex
from src.backend.utils.parsers import SystemParser
from src.backend.utils.validators import MatrixValidator

MAX_CELDAS_SISTEMA = 48
MAX_ECUACIONES_PREVIA = 10
MAX_VARIABLES_PREVIA = 10
MAX_CARACTERES_ECUACIONES = 2048
_PATRON_LINEA = re.compile(r"^Línea (\d+):(.*)$")


@dataclass(frozen=True)
class ResultadoVistaPrevia:
    """Agrupa el estado inmutable de una matriz o sistema para previsualizar."""

    estado: str
    matriz: tuple[tuple[Fraction | None, ...], ...] | None
    variables: tuple[str, ...]
    mensaje: str


def analizar_ecuaciones(lineas: list[str]) -> ResultadoVistaPrevia:
    """Analiza ecuaciones y conserva el número original de cada línea."""
    longitud = 0
    for linea in lineas:
        longitud += len(linea)
        if longitud > MAX_CARACTERES_ECUACIONES:
            mensaje = f"Reduce el texto a {MAX_CARACTERES_ECUACIONES} caracteres para ver la vista previa."
            return ResultadoVistaPrevia("error", None, (), mensaje)
    escritas = [(indice, linea.strip()) for indice, linea in enumerate(lineas, 1) if linea.strip()]
    if not escritas:
        return ResultadoVistaPrevia("vacio", None, (), "")
    if len(escritas) > MAX_ECUACIONES_PREVIA:
        mensaje = f"La vista previa admite hasta {MAX_ECUACIONES_PREVIA} ecuaciones."
        return ResultadoVistaPrevia("error", None, (), mensaje)
    texto = "\n".join(linea for _, linea in escritas)
    correcto, matriz, variables, mensaje = SystemParser.parse_system(texto)
    if correcto:
        if len(variables) > MAX_VARIABLES_PREVIA:
            mensaje = f"La vista previa admite hasta {MAX_VARIABLES_PREVIA} variables."
            return ResultadoVistaPrevia("error", None, (), mensaje)
        filas = tuple(tuple(fila) for fila in matriz.data)
        return ResultadoVistaPrevia("ok", filas, tuple(variables), "")
    mensaje = mensaje.replace(chr(0x2014), "-")
    coincidencia = _PATRON_LINEA.match(mensaje)
    if coincidencia:
        indice = int(coincidencia.group(1)) - 1
        if 0 <= indice < len(escritas):
            mensaje = f"Ecuación {escritas[indice][0]}:{coincidencia.group(2)}"
    return ResultadoVistaPrevia("error", None, (), mensaje)


def latex_matriz_aumentada(
    matriz: tuple[tuple[Fraction | None, ...], ...], num_vars: int
) -> str:
    """Devuelve la representación LaTeX de una matriz aumentada."""
    if not matriz:
        return ""
    celdas_invalidas = {
        (fila, columna)
        for fila, valores in enumerate(matriz)
        for columna, valor in enumerate(valores)
        if valor is None
    }
    datos = [[valor if valor is not None else 0 for valor in fila] for fila in matriz]
    matriz_backend = Matrix(len(datos), len(datos[0]), datos)
    latex = augmented_gauss_matrix_to_latex(matriz_backend, num_vars)
    filas = latex.split(r" \\ ")
    if len(filas) != len(matriz):
        return latex
    for fila, valores_invalidos in enumerate(_invalidas_por_fila(len(matriz), celdas_invalidas)):
        celdas = filas[fila].split(" & ")
        for columna in valores_invalidos:
            if columna < len(celdas):
                celdas[columna] = r"\color{gray}{?}"
        filas[fila] = " & ".join(celdas)
    return r" \\ ".join(filas)


def latex_sistema(
    matriz: tuple[tuple[Fraction | None, ...], ...], variables: tuple[str, ...]
) -> str:
    """Devuelve las ecuaciones de una matriz aumentada dentro de cases."""
    ecuaciones = []
    variables_latex = [format_variable_for_latex(variable) for variable in variables]
    for fila in matriz:
        coeficientes = [fila[columna] for columna in range(len(variables))]
        expresion = format_linear_expression(coeficientes, variables_latex)
        termino = number_to_latex(fila[len(variables)])
        ecuaciones.append(f"{expresion} = {termino}")
    return r"\begin{cases} " + r" \\ ".join(ecuaciones) + r" \end{cases}"


def matriz_desde_celdas(
    matriz_a: list[list[str]], vector_b: list[str]
) -> ResultadoVistaPrevia:
    """Convierte las celdas editables en una matriz aumentada exacta."""
    if not matriz_a or not matriz_a[0]:
        return ResultadoVistaPrevia("vacio", None, (), "")
    datos: list[tuple[Fraction | None, ...]] = []
    errores = False
    columnas = len(matriz_a[0])
    for indice_fila, fila in enumerate(matriz_a):
        datos_fila: list[Fraction | None] = []
        for valor in fila:
            parseado, numero, _ = MatrixValidator.parse_number_exact(valor or "0")
            datos_fila.append(numero if parseado else None)
            errores = errores or not parseado
        valor_b = vector_b[indice_fila] if indice_fila < len(vector_b) else "0"
        parseado, numero, _ = MatrixValidator.parse_number_exact(valor_b or "0")
        datos_fila.append(numero if parseado else None)
        errores = errores or not parseado
        datos.append(tuple(datos_fila))
    variables = tuple(f"x{indice + 1}" for indice in range(columnas))
    estado = "error" if errores else "ok"
    mensaje = "Corrige los valores inválidos para ver las ecuaciones." if errores else ""
    return ResultadoVistaPrevia(estado, tuple(datos), variables, mensaje)


def _invalidas_por_fila(
    cantidad_filas: int, invalidas: set[tuple[int, int]]
) -> list[set[int]]:
    """Identifica valores de marcado especial en filas de la matriz."""
    filas = [set() for _ in range(cantidad_filas)]
    for fila, columna in invalidas:
        filas[fila].add(columna)
    return filas
