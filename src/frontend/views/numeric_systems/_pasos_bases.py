"""Construcción pura de pasos y grupos didácticos para el conversor de bases."""

from __future__ import annotations

import html
from typing import Any

from nicegui import ui

from src.frontend.components.reproductor_pasos.cuerpos import render_latex
from src.frontend.components.reproductor_pasos.modelo import (
    GrupoReproductor,
    PasoReproductor,
)

_NOMBRES_BASE = {2: "Binario", 8: "Octal", 10: "Decimal", 16: "Hexadecimal"}


class _CuerpoHtmlLatex:
    """Cuerpo ejecutable que renderiza una tabla HTML y opcionalmente una expresión MathJax."""

    def __init__(self, html_contenido: str, latex_expr: str | None = None) -> None:
        self.html_contenido = html_contenido
        self.latex_expr = latex_expr

    def __call__(self) -> None:
        ui.html(self.html_contenido).classes("w-full")
        if self.latex_expr:
            render_latex(self.latex_expr)

    def __str__(self) -> str:
        return self.html_contenido


def _crear_tabla_expansion(terminos: list[dict], hasta_indice: int, base: int) -> str:
    """Genera la tabla HTML para un paso parcial de expansión posicional."""
    filas_html = []
    subtotal_acum = 0

    for i in range(hasta_indice + 1):
        t = terminos[i]
        d, v = html.escape(str(t["digito"])), html.escape(str(t["valor"]))
        pot, peso = html.escape(str(t["potencia"])), html.escape(str(t["peso"]))
        subtotal_acum += t["producto"]
        prod = html.escape(str(t["producto"]))
        bg = "background-color: var(--accent-glow, rgba(16, 185, 129, 0.15));" if i == hasta_indice else ""
        filas_html.append(
            f"<tr style='{bg}'>"
            f"<td class='p-2 border-b border-[var(--border-input)] text-center font-mono'>{d}</td>"
            f"<td class='p-2 border-b border-[var(--border-input)] text-center'>{v}</td>"
            f"<td class='p-2 border-b border-[var(--border-input)] text-center'>{base}<sup>{pot}</sup></td>"
            f"<td class='p-2 border-b border-[var(--border-input)] text-center'>{peso}</td>"
            f"<td class='p-2 border-b border-[var(--border-input)] text-center font-bold text-[var(--accent)]'>{prod}</td>"
            f"</tr>"
        )

    subtotal_str = html.escape(str(subtotal_acum))
    return (
        f"<div class='overflow-x-auto w-full my-2' style='min-width: 0;'>"
        f"<table class='w-full text-sm border-collapse' style='overflow-wrap: anywhere;'>"
        f"<thead><tr class='bg-[var(--bg-elevated)]'>"
        f"<th class='p-2 text-sec text-center'>Dígito</th><th class='p-2 text-sec text-center'>Valor Int</th>"
        f"<th class='p-2 text-sec text-center'>Posición</th><th class='p-2 text-sec text-center'>Peso</th>"
        f"<th class='p-2 text-sec text-center'>Subtotal</th></tr></thead>"
        f"<tbody>{''.join(filas_html)}</tbody>"
        f"<tfoot><tr class='font-bold bg-[var(--bg-elevated)]'>"
        f"<td colspan='4' class='p-2 text-right text-sec'>Subtotal acumulado:</td>"
        f"<td class='p-2 text-center font-mono font-bold text-[var(--accent)]' style='overflow-wrap: anywhere;'>{subtotal_str}</td>"
        f"</tr></tfoot></table></div>"
    )


def _crear_tabla_division(filas: list[dict], hasta_indice: int) -> str:
    """Genera la tabla HTML para un paso parcial de divisiones sucesivas."""
    filas_html = []
    for i in range(hasta_indice + 1):
        f = filas[i]
        divdo, divsor = html.escape(str(f["dividendo"])), html.escape(str(f["divisor"]))
        coc, res = html.escape(str(f["cociente"])), html.escape(str(f["residuo"]))
        estilo_res = (
            "font-bold text-[var(--btn-primary-text)] bg-[var(--accent)] rounded-md m-1 block"
            if i == hasta_indice
            else "font-mono text-sec"
        )
        filas_html.append(
            f"<tr><td class='p-2 border-b border-[var(--border-input)] text-center' style='overflow-wrap: anywhere;'>{divdo}</td>"
            f"<td class='p-2 border-b border-[var(--border-input)] text-center'>÷ {divsor}</td>"
            f"<td class='p-2 border-b border-[var(--border-input)] text-center font-bold' style='overflow-wrap: anywhere;'>{coc}</td>"
            f"<td class='p-2 border-b border-[var(--border-input)] text-center {estilo_res}'>{res}</td></tr>"
        )

    return (
        f"<div class='overflow-x-auto w-full my-2' style='min-width: 0;'>"
        f"<table class='w-full text-sm border-collapse' style='overflow-wrap: anywhere;'>"
        f"<thead><tr class='bg-[var(--bg-elevated)]'>"
        f"<th class='p-2 text-sec text-center'>Dividendo</th><th class='p-2 text-sec text-center'>Divisor</th>"
        f"<th class='p-2 text-sec text-center'>Cociente</th><th class='p-2 text-sec text-center'>Residuo</th>"
        f"</tr></thead><tbody>{''.join(filas_html)}</tbody></table></div>"
    )


def _crear_paso_resultado_expansion(
    terminos: list[dict], base: int, total_val: str, es_negativo: bool, grp_idx: int, titulo: str
) -> dict[str, Any]:
    """Crea el paso final de resultado para la expansión posicional."""
    eq_terminos = [f"({t['valor']} \\times {base}^{{{t['potencia']}}})" for t in terminos]
    eq_str = " + ".join(eq_terminos)
    if es_negativo:
        eq_str = f"-\\left[ {eq_str} \\right]"
    eq_str += f" = {total_val}"
    tabla = _crear_tabla_expansion(terminos, len(terminos) - 1, base)
    expl = (
        "Sumamos las contribuciones posicionales y aplicamos el signo negativo al total."
        if es_negativo
        else "Sumamos todas las contribuciones posicionales para obtener el valor decimal."
    )
    return {
        "tipo": "resultado", "etiqueta_tipo": "Resultado",
        "descripcion": f"Total expansión posicional: {total_val}",
        "explicacion": expl,
        "cuerpo": _CuerpoHtmlLatex(tabla, eq_str),
        "indice_grupo": grp_idx, "titulo_grupo": titulo,
    }


def _generar_pasos_expansion(paso_raw: dict, titulo: str, grp_idx: int) -> list[dict[str, Any]]:
    """Genera la lista de pasos para una conversión por expansión posicional."""
    terminos = paso_raw.get("terminos", [])
    base = paso_raw.get("base_origen", 10)
    total_val = paso_raw.get("total", "0")
    es_negativo = paso_raw.get("es_negativo", False)

    pasos: list[dict[str, Any]] = []
    for i, t in enumerate(terminos):
        d, v, pot, peso, prod = t["digito"], t["valor"], t["potencia"], t["peso"], t["producto"]
        desc = f"Dígito {d} (valor {v}) × {base}^{pot} = {prod}"
        expl = f"Posición {pot} contando desde la derecha; el peso es {base}^{pot} = {peso} y aporta {prod} al subtotal."
        pasos.append({
            "tipo": "expansion", "etiqueta_tipo": "Expansión",
            "descripcion": desc, "explicacion": expl,
            "cuerpo": _CuerpoHtmlLatex(_crear_tabla_expansion(terminos, i, base)),
            "indice_grupo": grp_idx, "titulo_grupo": titulo,
        })

    pasos.append(_crear_paso_resultado_expansion(terminos, base, total_val, es_negativo, grp_idx, titulo))
    return pasos


def _crear_paso_lectura_division(
    filas: list[dict], base_dest: int, resultado: str, lectura: str, grp_idx: int, titulo: str
) -> dict[str, Any]:
    """Crea el paso final de lectura para las divisiones sucesivas."""
    tabla = _crear_tabla_division(filas, len(filas) - 1)
    escaped_lectura = html.escape(str(lectura))
    html_lectura = (
        f"<div class='flex items-center gap-6 mt-4 font-normal flex-wrap'>"
        f"<div class='overflow-x-auto flex-grow' style='min-width: 0;'>{tabla}</div>"
        f"<div class='flex flex-col items-center justify-center text-sec flex-shrink-0 mx-auto'>"
        f"<span class='material-icons text-3xl'>arrow_upward</span>"
        f"<span class='text-xs text-center w-24'>{escaped_lectura}</span>"
        f"</div></div>"
    )
    return {
        "tipo": "lectura", "etiqueta_tipo": "Lectura",
        "descripcion": f"Resultado en base {base_dest}: {resultado}",
        "explicacion": "Leemos los residuos de abajo hacia arriba para construir el número final.",
        "cuerpo": _CuerpoHtmlLatex(html_lectura, f"{resultado}_{{{base_dest}}}"),
        "indice_grupo": grp_idx, "titulo_grupo": titulo,
    }


def _generar_pasos_division(paso_raw: dict, titulo: str, grp_idx: int) -> list[dict[str, Any]]:
    """Genera la lista de pasos para una conversión por divisiones sucesivas."""
    filas = paso_raw.get("filas", [])
    base_dest = paso_raw.get("base_destino", 10)
    resultado = paso_raw.get("resultado", "0")
    lectura = paso_raw.get("lectura", "Se lee de abajo hacia arriba")

    pasos: list[dict[str, Any]] = []
    for i, f in enumerate(filas):
        divdo, divsor, coc, res = f["dividendo"], f["divisor"], f["cociente"], f["residuo"]
        desc = f"{divdo} ÷ {divsor} = {coc}, residuo {res}"
        expl = f"Dividimos entre {divsor}; guardamos el residuo {res} para formar el número en la base destino."
        pasos.append({
            "tipo": "division", "etiqueta_tipo": "División",
            "descripcion": desc, "explicacion": expl,
            "cuerpo": _CuerpoHtmlLatex(_crear_tabla_division(filas, i)),
            "indice_grupo": grp_idx, "titulo_grupo": titulo,
        })

    pasos.append(_crear_paso_lectura_division(filas, base_dest, resultado, lectura, grp_idx, titulo))
    return pasos


def _procesar_conversion(p: dict, idx_conv: int, grp_idx: int) -> tuple[str, str, list[dict[str, Any]]]:
    """Determina el título, tipo y pasos de una conversión individual."""
    tipo = p.get("tipo")
    if tipo == "expansion_posicional":
        nombre = _NOMBRES_BASE.get(p.get("base_origen"), f"Base {p.get('base_origen')}")
        titulo = f"{idx_conv}. Expansión Posicional desde {nombre}"
        return titulo, "expansion", _generar_pasos_expansion(p, titulo, grp_idx)
    if tipo == "division_sucesiva":
        nombre = _NOMBRES_BASE.get(p.get("base_destino"), f"Base {p.get('base_destino')}")
        titulo = f"{idx_conv}. Divisiones Sucesivas hacia {nombre}"
        return titulo, "division", _generar_pasos_division(p, titulo, grp_idx)
    return "", "", []


def construir_pasos_bases(
    datos_o_pasos: dict | list,
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Convierte los pasos del conversor de bases en tuplas de pasos y grupos didácticos."""
    pasos_raw = datos_o_pasos.get("pasos", []) if isinstance(datos_o_pasos, dict) else (datos_o_pasos or [])
    if not pasos_raw:
        return (), ()

    raw_pasos: list[dict[str, Any]] = []
    grupos: list[GrupoReproductor] = []

    for idx_conv, p in enumerate(pasos_raw, start=1):
        titulo, tipo_grupo, pasos_conv = _procesar_conversion(p, idx_conv, len(grupos))
        if not pasos_conv:
            continue

        indices_grupo = tuple(range(len(raw_pasos), len(raw_pasos) + len(pasos_conv)))
        raw_pasos.extend(pasos_conv)
        k = len(indices_grupo)
        resumen = f"{k} operaciones" if k != 1 else "1 operación"
        grupos.append(GrupoReproductor(titulo=titulo, resumen=resumen, tipo=tipo_grupo, indices_pasos=indices_grupo))

    total = len(raw_pasos)
    pasos = [
        PasoReproductor(
            indice=i, tipo=p["tipo"], etiqueta_tipo=p["etiqueta_tipo"],
            descripcion=p["descripcion"], explicacion=p["explicacion"],
            indice_grupo=p["indice_grupo"], cuerpo=p["cuerpo"],
            meta_explicar={"index": i + 1, "total": total, "kind": "otro", "op": f"{p['titulo_grupo']}: {p['descripcion']}", "rows_before": {}, "rows_after": {}, "cols": None},
        )
        for i, p in enumerate(raw_pasos)
    ]
    return tuple(pasos), tuple(grupos)
