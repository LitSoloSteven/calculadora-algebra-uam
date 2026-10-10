"""Construcción pura de pasos y grupos didácticos para la Calculadora de Números Romanos."""

from __future__ import annotations

import html
from typing import Any

from nicegui import ui

from src.frontend.components.reproductor_pasos.modelo import (
    GrupoReproductor,
    PasoReproductor,
)

TABLA_CANONICA = (
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
    (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
)


def desglosar_pasos_canonicos(n: int) -> list[dict[str, Any]]:
    """Devuelve las deducciones voraces paso a paso para convertir decimal a romano."""
    pasos: list[dict[str, Any]] = []
    resto = n
    for val, rom in TABLA_CANONICA:
        while resto >= val:
            nuevo_resto = resto - val
            pasos.append({"valor_restado": val, "simbolo": rom, "anterior": resto, "restante": nuevo_resto})
            resto = nuevo_resto
    return pasos


class _CuerpoHtml:
    """Cuerpo ejecutable que renderiza un bloque HTML estilizado."""

    def __init__(self, html_codigo: str) -> None:
        self.html_codigo = html_codigo

    def __call__(self) -> None:
        ui.html(self.html_codigo).classes("w-full")

    def __str__(self) -> str:
        return self.html_codigo


def _crear_tarjeta_operando(etiqueta: str, rom: str, dec: int) -> str:
    """Genera la tarjeta HTML de decodificación de un operando."""
    e_rom, e_dec = html.escape(str(rom)), html.escape(str(dec))
    return (
        f"<div class='p-5 rounded-xl border flex items-center justify-between w-full my-2' style='background: var(--bg-panel); border-color: var(--border-input); box-shadow: var(--elev-2);'>"
        f"<div class='flex flex-col gap-1'><span class='text-base font-semibold text-sec'>{etiqueta}</span>"
        f"<span class='text-3xl md:text-4xl font-mono font-bold text-main'>{e_rom}</span></div>"
        f"<span class='text-3xl md:text-4xl font-mono font-black' style='color: var(--accent);'>= {e_dec}</span></div>"
    )


def _crear_pasos_decodificacion(val_a: str, dec_a: int, val_b: str, dec_b: int, grp_idx: int) -> list[dict[str, Any]]:
    """Crea los 2 pasos iniciales de decodificación de operandos a decimal."""
    tit = "Decodificación de operandos a decimal"
    return [
        {
            "tipo": "decodificacion", "etiqueta_tipo": "Decodificación",
            "descripcion": f"Operando A: {val_a} = {dec_a}",
            "explicacion": f"Decodificamos el numeral romano {val_a} a su valor decimal {dec_a} aplicando reglas aditivas y sustractivas.",
            "cuerpo": _CuerpoHtml(_crear_tarjeta_operando("Operando A", val_a, dec_a)),
            "indice_grupo": grp_idx, "titulo_grupo": tit,
        },
        {
            "tipo": "decodificacion", "etiqueta_tipo": "Decodificación",
            "descripcion": f"Operando B: {val_b} = {dec_b}",
            "explicacion": f"Decodificamos el numeral romano {val_b} a su valor decimal {dec_b} aplicando reglas aditivas y sustractivas.",
            "cuerpo": _CuerpoHtml(_crear_tarjeta_operando("Operando B", val_b, dec_b)),
            "indice_grupo": grp_idx, "titulo_grupo": tit,
        },
    ]


def _crear_tabla_iteraciones(val_a: str, dec_a: int, hasta_iter: int, total_b: int, res_rom: str) -> str:
    """Genera la tabla HTML de sumas sucesivas hasta la iteración actual."""
    filas = []
    acum = 0
    for i in range(1, hasta_iter + 1):
        acum += dec_a
        bg = "background-color: var(--accent-glow, rgba(16, 185, 129, 0.15));" if i == hasta_iter else ""
        valor_parcial = html.escape(res_rom if i == total_b else str(acum))
        filas.append(
            f"<tr style='{bg}'>"
            f"<td class='p-2 text-center text-sec font-bold border-b border-[var(--border-input)]'>Paso {i}</td>"
            f"<td class='p-2 text-center text-main font-semibold border-b border-[var(--border-input)]'>+ {html.escape(val_a)} ({dec_a})</td>"
            f"<td class='p-2 text-center text-main font-black border-b border-[var(--border-input)]'>{acum}</td>"
            f"<td class='p-2 text-center border-b border-[var(--border-input)]'>"
            f"<span class='font-black px-3 py-1 rounded-lg text-sm border' style='background: var(--bg-elevated); color: var(--accent); border-color: var(--border-input);'>{valor_parcial}</span>"
            f"</td></tr>"
        )

    return (
        f"<div class='overflow-x-auto w-full my-2' style='min-width: 0;'><table class='w-full text-sm border-collapse' style='overflow-wrap: anywhere;'>"
        f"<thead><tr class='bg-[var(--bg-elevated)]'><th class='p-2 text-sec text-center'>Iteración</th><th class='p-2 text-sec text-center'>Operando Sumado</th>"
        f"<th class='p-2 text-sec text-center'>Acumulado (Dec)</th><th class='p-2 text-sec text-center'>Valor Parcial</th>"
        f"</tr></thead><tbody>{''.join(filas)}</tbody></table></div>"
    )


def _crear_pasos_multiplicacion(
    val_a: str, dec_a: int, val_b: str, dec_b: int, res_rom: str, res_dec: int, grp_idx: int, titulo: str
) -> list[dict[str, Any]]:
    """Construye la secuencia de pasos para multiplicación romana por sumas sucesivas."""
    pasos: list[dict[str, Any]] = []
    html_def = (
        f"<div class='p-4 rounded-xl border w-full text-center my-2' style='background: var(--bg-panel); border-color: var(--border-input);'>"
        f"<span class='text-sec text-sm'>Definición:</span> <span class='text-main font-bold text-lg'>{val_a} × {val_b} = sumar {dec_a}, {dec_b} veces</span></div>"
    )
    pasos.append({
        "tipo": "definicion", "etiqueta_tipo": "Definición",
        "descripcion": f"Definición: sumar {dec_a}, {dec_b} veces",
        "explicacion": f"La multiplicación romana se realiza sumando sucesivamente {val_a} ({dec_a}) un total de {dec_b} veces.",
        "cuerpo": _CuerpoHtml(html_def), "indice_grupo": grp_idx, "titulo_grupo": titulo,
    })

    acum = 0
    for i in range(1, dec_b + 1):
        acum += dec_a
        pasos.append({
            "tipo": "iteracion", "etiqueta_tipo": "Iteración",
            "descripcion": f"Paso {i}: acumulado = {acum}",
            "explicacion": f"Iteración {i} de {dec_b}: sumamos {dec_a} al acumulado previo, alcanzando {acum}.",
            "cuerpo": _CuerpoHtml(_crear_tabla_iteraciones(val_a, dec_a, i, dec_b, res_rom)),
            "indice_grupo": grp_idx, "titulo_grupo": titulo,
        })

    html_prod = (
        f"<div class='p-4 rounded-xl border w-full text-center my-2' style='background: var(--bg-panel); border-color: var(--border-input);'>"
        f"<span class='text-sec text-sm'>Producto final:</span> <span class='text-2xl font-black' style='color: var(--accent);'>{dec_a} × {dec_b} = {res_dec}</span></div>"
    )
    pasos.append({
        "tipo": "producto", "etiqueta_tipo": "Producto",
        "descripcion": f"Producto total: {dec_a} × {dec_b} = {res_dec}",
        "explicacion": f"Completadas las {dec_b} sumas sucesivas, el producto decimal final es {res_dec}.",
        "cuerpo": _CuerpoHtml(html_prod), "indice_grupo": grp_idx, "titulo_grupo": titulo,
    })
    return pasos


def _crear_paso_validacion_resta(dec_a: int, dec_b: int, grp_idx: int, titulo: str) -> dict[str, Any]:
    """Crea el paso de validación A > B para la resta romana."""
    html_val = (
        f"<div class='p-4 rounded-xl border w-full my-2' style='background: var(--bg-panel); border-color: var(--border-input);'>"
        f"<div class='flex justify-between items-center'><span class='text-main font-bold text-lg'>Validación: {dec_a} > {dec_b} ✓</span>"
        f"<span class='text-xs font-bold px-3 py-1 rounded-md' style='background: var(--accent-glow); color: var(--accent);'>Correcto</span></div>"
        f"<p class='text-xs text-sec mt-2'>Los números romanos no contemplan el cero ni valores negativos. El minuendo debe superar estrictamente al sustraendo.</p></div>"
    )
    return {
        "tipo": "validacion", "etiqueta_tipo": "Validación",
        "descripcion": f"Validación: {dec_a} > {dec_b}",
        "explicacion": "Los números romanos no contemplan el cero ni valores negativos. El minuendo debe superar al sustraendo.",
        "cuerpo": _CuerpoHtml(html_val), "indice_grupo": grp_idx, "titulo_grupo": titulo,
    }


def _crear_pasos_operacion(
    op: str, val_a: str, dec_a: int, val_b: str, dec_b: int, res_rom: str, res_dec: int, grp_idx: int
) -> tuple[str, str, list[dict[str, Any]]]:
    """Genera los pasos de la operación aritmética según su tipo."""
    if op == "mult":
        titulo = "Multiplicación mediante sumas sucesivas"
        return titulo, "multiplicacion", _crear_pasos_multiplicacion(val_a, dec_a, val_b, dec_b, res_rom, res_dec, grp_idx, titulo)

    nombre = "Suma" if op == "suma" else "Resta"
    titulo, simbolo = f"Ejecución aritmética de la {nombre.lower()}", "+" if op == "suma" else "−"
    pasos: list[dict[str, Any]] = []
    if op == "resta":
        pasos.append(_crear_paso_validacion_resta(dec_a, dec_b, grp_idx, titulo))

    html_op = (
        f"<div class='p-5 rounded-xl border flex items-center justify-center gap-4 w-full my-2' style='background: var(--bg-panel); border-color: var(--border-input);'>"
        f"<span class='text-3xl md:text-4xl font-mono font-bold text-main'>{dec_a}</span>"
        f"<span class='text-2xl font-bold text-sec'>{simbolo}</span>"
        f"<span class='text-3xl md:text-4xl font-mono font-bold text-main'>{dec_b}</span>"
        f"<span class='text-2xl font-bold text-sec'>=</span>"
        f"<span class='text-4xl md:text-5xl font-mono font-black' style='color: var(--accent);'>{res_dec}</span></div>"
    )
    expl_op = "Sumamos directamente los valores decimales de ambos operandos." if op == "suma" else f"Restamos {dec_b} de {dec_a} obteniendo {res_dec}."
    pasos.append({
        "tipo": "operacion", "etiqueta_tipo": "Operación",
        "descripcion": f"{dec_a} {simbolo} {dec_b} = {res_dec}", "explicacion": expl_op,
        "cuerpo": _CuerpoHtml(html_op), "indice_grupo": grp_idx, "titulo_grupo": titulo,
    })
    return titulo, "operacion", pasos


def _crear_tabla_construccion(pasos_can: list[dict], hasta_indice: int) -> str:
    """Genera la tabla HTML de sustracciones voraces hasta la fila actual."""
    filas = []
    for i in range(hasta_indice + 1):
        p = pasos_can[i]
        ant, val, rem, sym = p["anterior"], p["valor_restado"], p["restante"], html.escape(str(p["simbolo"]))
        bg = "background-color: var(--accent-glow, rgba(16, 185, 129, 0.15));" if i == hasta_indice else ""
        filas.append(
            f"<tr style='{bg}'>"
            f"<td class='p-2 text-center text-main font-black border-b border-[var(--border-input)] font-mono'>{ant} − {val}</td>"
            f"<td class='p-2 text-center border-b border-[var(--border-input)]'>"
            f"<span class='font-black px-4 py-1.5 rounded-lg text-lg border tracking-widest' style='background: var(--bg-elevated); color: var(--accent); border-color: var(--border-input);'>{sym}</span>"
            f"</td><td class='p-2 text-center text-sec font-bold border-b border-[var(--border-input)] font-mono'>= {rem}</td></tr>"
        )
    return (
        f"<div class='overflow-x-auto w-full my-2' style='min-width: 0;'>"
        f"<table class='w-full text-sm border-collapse' style='overflow-wrap: anywhere;'>"
        f"<thead><tr class='bg-[var(--bg-elevated)]'>"
        f"<th class='p-2 text-sec text-center'>Sustracción</th><th class='p-2 text-sec text-center'>Glifo Asignado</th><th class='p-2 text-sec text-center'>Residuo</th>"
        f"</tr></thead><tbody>{''.join(filas)}</tbody></table></div>"
    )


def _crear_pasos_construccion(
    val_a: str, val_b: str, simbolo_op: str, res_rom: str, res_dec: int, grp_idx: int
) -> list[dict[str, Any]]:
    """Genera los pasos de notación y construcción canónica romana."""
    titulo_grp = "Notación y construcción canónica romana"
    pasos_can = desglosar_pasos_canonicos(res_dec)
    pasos: list[dict[str, Any]] = []

    for i, p in enumerate(pasos_can):
        desc = f"Sustracción: {p['anterior']} − {p['valor_restado']} = {p['restante']} (glifo {p['simbolo']})"
        expl = f"Restamos el valor {p['valor_restado']}, asignamos el glifo {p['simbolo']} y queda un residuo de {p['restante']}."
        pasos.append({
            "tipo": "construccion", "etiqueta_tipo": "Construcción",
            "descripcion": desc, "explicacion": expl,
            "cuerpo": _CuerpoHtml(_crear_tabla_construccion(pasos_can, i)),
            "indice_grupo": grp_idx, "titulo_grupo": titulo_grp,
        })

    e_a, e_b, e_rom = html.escape(str(val_a)), html.escape(str(val_b)), html.escape(str(res_rom))
    html_final = (
        f"<div class='p-6 rounded-2xl border flex flex-col items-center justify-center w-full my-2' style='background: var(--bg-panel); border-color: var(--border-input); box-shadow: var(--elev-2);'>"
        f"<span class='text-xs font-bold text-sec tracking-widest uppercase'>Expresión final verificada</span>"
        f"<div class='flex items-baseline gap-4 mt-3 flex-wrap justify-center font-mono'>"
        f"<span class='text-2xl md:text-3xl text-sec font-medium'>{e_a} {simbolo_op} {e_b} =</span>"
        f"<span class='text-4xl md:text-5xl font-black tracking-widest' style='color: var(--accent);'>{e_rom}</span>"
        f"<span class='text-lg md:text-xl text-sec'>({res_dec})</span></div></div>"
    )
    pasos.append({
        "tipo": "resultado", "etiqueta_tipo": "Resultado",
        "descripcion": f"{val_a} {simbolo_op} {val_b} = {res_rom} ({res_dec})",
        "explicacion": "Ensamblamos todos los glifos canónicos para formar el numeral romano definitivo.",
        "cuerpo": _CuerpoHtml(html_final), "indice_grupo": grp_idx, "titulo_grupo": titulo_grp,
    })
    return pasos


def _convertir_a_pasos_reproductor(raw_pasos: list[dict[str, Any]]) -> tuple[PasoReproductor, ...]:
    """Convierte los diccionarios de pasos en instancias inmutables de PasoReproductor."""
    total = len(raw_pasos)
    return tuple(
        PasoReproductor(
            indice=i, tipo=p["tipo"], etiqueta_tipo=p["etiqueta_tipo"],
            descripcion=p["descripcion"], explicacion=p["explicacion"],
            indice_grupo=p["indice_grupo"], cuerpo=p["cuerpo"],
            meta_explicar={"index": i + 1, "total": total, "kind": "otro", "op": f"{p['titulo_grupo']}: {p['descripcion']}", "rows_before": {}, "rows_after": {}, "cols": None},
        )
        for i, p in enumerate(raw_pasos)
    )


def construir_pasos_romanos(
    res: Any, operacion: str
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Construye las tuplas de pasos y grupos didácticos para una operación romana."""
    if not res:
        return (), ()

    val_a, val_b = getattr(res, "operando_a_romano", ""), getattr(res, "operando_b_romano", "")
    dec_a, dec_b = getattr(res, "operando_a_decimal", 0), getattr(res, "operando_b_decimal", 0)
    res_rom, res_dec = getattr(res, "resultado_romano", ""), getattr(res, "resultado_decimal", 0)
    simbolo_op = {"suma": "+", "resta": "−", "mult": "×"}.get(operacion, "+")

    raw_pasos: list[dict[str, Any]] = []
    grupos: list[GrupoReproductor] = []

    # Grupo 1: Decodificación
    pasos_deco = _crear_pasos_decodificacion(val_a, dec_a, val_b, dec_b, len(grupos))
    indices_deco = tuple(range(len(raw_pasos), len(raw_pasos) + len(pasos_deco)))
    raw_pasos.extend(pasos_deco)
    grupos.append(GrupoReproductor(titulo="Decodificación de operandos a decimal", resumen=f"{len(indices_deco)} operaciones", tipo="decodificacion", indices_pasos=indices_deco))

    # Grupo 2: Operación aritmética
    titulo_op, tipo_op, pasos_op = _crear_pasos_operacion(operacion, val_a, dec_a, val_b, dec_b, res_rom, res_dec, len(grupos))
    indices_op = tuple(range(len(raw_pasos), len(raw_pasos) + len(pasos_op)))
    raw_pasos.extend(pasos_op)
    grupos.append(GrupoReproductor(titulo=titulo_op, resumen=f"{len(indices_op)} operaciones", tipo=tipo_op, indices_pasos=indices_op))

    # Grupo 3: Construcción canónica
    pasos_const = _crear_pasos_construccion(val_a, val_b, simbolo_op, res_rom, res_dec, len(grupos))
    indices_const = tuple(range(len(raw_pasos), len(raw_pasos) + len(pasos_const)))
    raw_pasos.extend(pasos_const)
    grupos.append(GrupoReproductor(titulo="Notación y construcción canónica romana", resumen=f"{len(indices_const)} operaciones", tipo="construccion", indices_pasos=indices_const))

    return _convertir_a_pasos_reproductor(raw_pasos), tuple(grupos)
