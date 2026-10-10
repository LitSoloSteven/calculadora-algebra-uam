"""Formateadores seguros de valores y tablas matemáticas de pasos."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from src.backend.constants import DISPLAY_DECIMALS
from src.backend.models.matrix import Matrix
from src.frontend.components.reproductor_pasos.catalogo import STACKED_FRAC_MAX_N


@dataclass(frozen=True)
class _ResaltadosAumentados:
    """Agrupa las opciones de resaltado aplicadas a cada fila."""

    ancho_izquierdo: int
    filas_cambiadas: Sequence[int]
    filas_intercambio: Sequence[int]
    pivote: tuple[int, int] | None
    bloque_resultado: bool
    apilada: bool


def formatear_valor(valor: int | Fraction | float | str, *, apilada: bool = False) -> str:
    """Formatea un número o texto para una celda."""
    if isinstance(valor, int) or (isinstance(valor, Fraction) and valor.denominator == 1):
        return str(valor.numerator if isinstance(valor, Fraction) else valor)
    if isinstance(valor, Fraction):
        signo = "−" if valor < 0 else ""
        numerador, denominador = abs(valor.numerator), valor.denominator
        if apilada:
            return f'{signo}<span class="inv-frac"><span>{numerador}</span><span>{denominador}</span></span>'
        return f"{signo}{numerador}/{denominador}"
    return html.escape(str(valor))


def formatear_decimal(valor: int | Fraction | float | str) -> str:
    """Devuelve una aproximación decimal sin ceros finales redundantes."""
    try:
        numero = float(valor)
        if abs(numero) < 1e-12:
            return "0"
        texto = f"{numero:.{DISPLAY_DECIMALS}f}".rstrip("0").rstrip(".")
        return "0" if texto == "-0" else texto
    except (OverflowError, ValueError):
        return html.escape(str(valor))


def etiqueta_variable_html(nombre: str) -> str:
    """Convierte un subíndice numérico o escapa el nombre recibido."""
    coincidencia = re.fullmatch(r"([A-Za-z]+)_?(\d+)", nombre)
    if coincidencia:
        return f"{coincidencia.group(1)}<sub>{coincidencia.group(2)}</sub>"
    return html.escape(nombre)


def html_tabla_matriz(matriz: Matrix, *, decimales: bool = False) -> str:
    """Genera una tabla de matriz con desplazamiento horizontal propio."""
    compacta = matriz.rows > STACKED_FRAC_MAX_N
    apilada = not compacta and not decimales
    encabezado = "<th class='row-label'></th>" + "".join(
        f"<th>C{columna + 1}</th>" for columna in range(matriz.cols)
    )
    filas = [_fila_matriz(matriz, indice, apilada, decimales) for indice in range(matriz.rows)]
    clase = "inv-table compact" if compacta else "inv-table"
    return _html_tabla(clase, encabezado, filas)


def _fila_matriz(matriz: Matrix, indice: int, apilada: bool, decimales: bool) -> str:
    """Construye una fila de la tabla de matriz con etiquetas y valores."""
    celdas = [f"<th class='row-label'>F{indice + 1}</th>"]
    for columna in range(matriz.cols):
        valor = matriz.get(indice, columna)
        contenido = formatear_decimal(valor) if decimales else formatear_valor(valor, apilada=apilada)
        if decimales:
            celdas.append(f"<td>{contenido}</td>")
            continue
        titulo = _titulo_aproximado(valor)
        celdas.append(f"<td{titulo}>{contenido}</td>")
    return f"<tr>{''.join(celdas)}</tr>"


def _titulo_aproximado(valor: int | Fraction | float) -> str:
    """Crea el atributo de aproximación para celdas no enteras."""
    es_entero = isinstance(valor, int) or isinstance(valor, Fraction) and valor.denominator == 1
    return "" if es_entero else f' title="≈ {formatear_decimal(valor)}"'


def html_tabla_aumentada(
    matriz: Matrix,
    n_izq: int,
    *,
    filas_cambiadas: Sequence[int] = (),
    pivote: tuple[int, int] | None = None,
    filas_intercambio: Sequence[int] = (),
    bloque_resultado: bool = False,
    etiquetas_izq: Sequence[str] | None = None,
    etiquetas_der: Sequence[str] | None = None,
) -> str:
    """Genera una tabla aumentada con resaltados y etiquetas opcionales."""
    if n_izq < 0 or n_izq > matriz.cols:
        raise ValueError("El ancho izquierdo debe caber en la matriz aumentada.")
    ancho_der = matriz.cols - n_izq
    compacta = n_izq > STACKED_FRAC_MAX_N
    encabezado = _encabezados_aumentados(n_izq, ancho_der, etiquetas_izq, etiquetas_der)
    opciones = _ResaltadosAumentados(
        n_izq, filas_cambiadas, filas_intercambio, pivote,
        bloque_resultado, n_izq <= STACKED_FRAC_MAX_N,
    )
    filas = [_fila_aumentada(matriz, indice, opciones) for indice in range(matriz.rows)]
    clases = "inv-table compact" if compacta else "inv-table"
    if bloque_resultado:
        clases += " is-result"
    return _html_tabla(clases, encabezado, filas)


def _encabezados_aumentados(
    n_izq: int,
    ancho_der: int,
    etiquetas_izq: Sequence[str] | None,
    etiquetas_der: Sequence[str] | None,
) -> str:
    """Construye los encabezados de bloques y valida las etiquetas recibidas."""
    izquierda = _validar_etiquetas(etiquetas_izq, n_izq)
    derecha = _validar_etiquetas(etiquetas_der, ancho_der)
    cabecera_izq = "".join(f"<th>{etiqueta}</th>" for etiqueta in izquierda)

    th_der = []
    for indice, etiqueta in enumerate(derecha):
        if indice == 0:
            th_der.append(f"<th class='sep-left'>{etiqueta}</th>")
        else:
            th_der.append(f"<th>{etiqueta}</th>")
    cabecera_der = "".join(th_der)

    return f"<th class='row-label'></th>{cabecera_izq}{cabecera_der}"


def _validar_etiquetas(etiquetas, ancho):
    """Genera las etiquetas numéricas por defecto o valida las explícitas."""
    if etiquetas is None:
        return [str(indice + 1) for indice in range(ancho)]
    if len(etiquetas) != ancho:
        raise ValueError("La cantidad de etiquetas debe coincidir con el ancho del bloque.")
    return [etiqueta_variable_html(etiqueta) for etiqueta in etiquetas]


def _fila_aumentada(matriz, indice, opciones):
    """Construye una fila aumentada y aplica sus clases de resaltado."""
    clase_fila = "row-swap" if indice in opciones.filas_intercambio else "row-changed" if indice in opciones.filas_cambiadas else ""
    atributo_fila = f' class="{clase_fila}"' if clase_fila else ""
    celdas = [f"<th class='row-label'>F{indice + 1}</th>"]
    for columna in range(matriz.cols):
        valor = matriz.get(indice, columna)
        clases = _clases_celda(columna, indice, opciones)
        clase_celda = f' class="{" ".join(clases)}"' if clases else ""
        contenido = formatear_valor(valor, apilada=opciones.apilada)
        celdas.append(f"<td{clase_celda}{_titulo_aproximado(valor)}>{contenido}</td>")
    return f"<tr{atributo_fila}>{''.join(celdas)}</tr>"


def _clases_celda(columna, indice, opciones):
    """Devuelve las clases visuales de una celda aumentada."""
    clases = []
    if columna == opciones.ancho_izquierdo:
        clases.append("sep-left")
    if opciones.pivote is not None and opciones.pivote == (indice, columna):
        clases.append("cell-pivot")
    if opciones.bloque_resultado and columna >= opciones.ancho_izquierdo:
        clases.append("block-result")
    return clases


def _html_tabla(clases, encabezado, filas):
    """Envuelve el encabezado y las filas en la tabla con scroll propia."""
    return (
        f'<div class="inv-scroll"><table class="{clases}">'
        f"<thead><tr>{encabezado}</tr></thead><tbody>{''.join(filas)}</tbody></table></div>"
    )