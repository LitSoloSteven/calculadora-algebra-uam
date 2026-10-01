"""Funciones puras de renderizado HTML para tablas neumórficas, fracciones y chips de la matriz inversa."""
from __future__ import annotations

import html
from fractions import Fraction
from typing import Sequence

from src.backend.constants import DISPLAY_DECIMALS
from src.backend.models.matrix import Matrix
from src.frontend.views.inverse_ops._config import STACKED_FRAC_MAX_N

KIND_META = {
    "inicial": {"label": "Inicio", "icon": "grid_on"},
    "intercambio": {"label": "Intercambio", "icon": "swap_vert"},
    "pivote": {"label": "Pivote", "icon": "gps_fixed"},
    "eliminacion": {"label": "Eliminación", "icon": "exposure"},
    "normalizacion": {"label": "Normalización", "icon": "looks_one"},
    "otro": {"label": "Operación", "icon": "tune"},
    "final": {"label": "Resultado", "icon": "check_circle"},
}


def fmt_value(val: int | Fraction | float | str, *, stacked: bool = False) -> str:
    """Formatea un valor matemático como entero o fracción estilizada."""
    if isinstance(val, int) or (isinstance(val, Fraction) and val.denominator == 1):
        num = val.numerator if isinstance(val, Fraction) else val
        return str(num)

    if isinstance(val, Fraction):
        sign = "−" if val < 0 else ""
        num = abs(val.numerator)
        den = val.denominator
        if stacked:
            return f'{sign}<span class="inv-frac"><span>{num}</span><span>{den}</span></span>'
        return f"{sign}{num}/{den}"

    return html.escape(str(val))


def fmt_decimal(val: int | Fraction | float | str) -> str:
    """Convierte un valor exacto a decimal con DISPLAY_DECIMALS y sin ceros redundantes."""
    try:
        flt = float(val)
        if abs(flt) < 1e-12:
            return "0"
        formatted = f"{flt:.{DISPLAY_DECIMALS}f}".rstrip("0").rstrip(".")
        if formatted == "-0":
            formatted = "0"
        return formatted
    except (OverflowError, ValueError):
        return html.escape(str(val))


def matrix_table_html(matrix: Matrix, *, decimals: bool = False) -> str:
    """Genera el HTML de una tabla con scroll propio (.inv-table) para una matriz dada."""
    n = matrix.rows
    compact = n > STACKED_FRAC_MAX_N
    is_stacked = (not compact) and (not decimals)

    th_cols = "".join(f"<th>C{j + 1}</th>" for j in range(matrix.cols))
    thead = f"<thead><tr><th class='row-label'></th>{th_cols}</tr></thead>"

    tbody_rows = []
    for i in range(matrix.rows):
        tds = [f"<th class='row-label'>F{i + 1}</th>"]
        for j in range(matrix.cols):
            val = matrix.get(i, j)
            dec_str = fmt_decimal(val)
            if decimals:
                content = dec_str
                tds.append(f"<td>{content}</td>")
            else:
                content = fmt_value(val, stacked=is_stacked)
                is_int = (
                    isinstance(val, int)
                    or (isinstance(val, Fraction) and val.denominator == 1)
                )
                title_attr = "" if is_int else f' title="≈ {dec_str}"'
                tds.append(f"<td{title_attr}>{content}</td>")
        tbody_rows.append(f"<tr>{''.join(tds)}</tr>")

    table_class = "inv-table compact" if compact else "inv-table"
    return (
        f'<div class="inv-scroll"><table class="{table_class}">'
        f'{thead}<tbody>{"".join(tbody_rows)}</tbody></table></div>'
    )


def augmented_table_html(
    matrix: Matrix,
    n: int,
    *,
    changed_rows: Sequence[int] = (),
    pivot: tuple[int, int] | None = None,
    swap_rows: Sequence[int] = (),
    is_final: bool = False,
) -> str:
    """Genera el HTML de la matriz aumentada [A | I] con resaltado de operaciones elementales."""
    compact = n > STACKED_FRAC_MAX_N
    is_stacked = not compact

    # thead: Columnas 1..n bloque izquierdo y 1..n bloque derecho
    left_ths = "".join(f"<th>{j + 1}</th>" for j in range(n))
    right_ths = []
    for j in range(n):
        cls = " class='sep-left'" if j == 0 else ""
        right_ths.append(f"<th{cls}>{j + 1}</th>")
    thead = f"<thead><tr><th class='row-label'></th>{left_ths}{''.join(right_ths)}</tr></thead>"

    tbody_rows = []
    for i in range(matrix.rows):
        tr_class = ""
        if i in swap_rows:
            tr_class = "row-swap"
        elif i in changed_rows:
            tr_class = "row-changed"
        tr_attr = f' class="{tr_class}"' if tr_class else ""

        tds = [f"<th class='row-label'>F{i + 1}</th>"]
        for col in range(matrix.cols):
            val = matrix.get(i, col)
            dec_str = fmt_decimal(val)
            is_int = (
                isinstance(val, int)
                or (isinstance(val, Fraction) and val.denominator == 1)
            )
            title_attr = "" if is_int else f' title="≈ {dec_str}"'
            content = fmt_value(val, stacked=is_stacked)

            td_classes = []
            if col == n:
                td_classes.append("sep-left")
            if pivot is not None and pivot[0] == i and pivot[1] == col:
                td_classes.append("cell-pivot")
            if is_final and col >= n:
                td_classes.append("block-result")

            cls_str = f' class="{" ".join(td_classes)}"' if td_classes else ""
            tds.append(f"<td{cls_str}{title_attr}>{content}</td>")

        tbody_rows.append(f"<tr{tr_attr}>{''.join(tds)}</tr>")

    table_classes = ["inv-table"]
    if compact:
        table_classes.append("compact")
    if is_final:
        table_classes.append("is-result")

    return (
        f'<div class="inv-scroll"><table class="{" ".join(table_classes)}">'
        f'{thead}<tbody>{"".join(tbody_rows)}</tbody></table></div>'
    )


def kind_chip_html(kind: str) -> str:
    """Devuelve el HTML del chip identificador del tipo de operación."""
    meta = KIND_META.get(kind, KIND_META["otro"])
    label = meta["label"]
    icon = meta["icon"]
    return (
        f'<span class="chip-kind chip-{kind}">'
        f'<span class="material-icons">{icon}</span>{label}</span>'
    )
