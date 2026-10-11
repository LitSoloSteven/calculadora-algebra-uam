"""Estrategias de recorte y formateo JSON para la serialización de contexto de IA.

Implementa la cascada progresiva de reducción de tamaño para garantizar que
el bloque [CONTEXTO] cumpla con los límites de longitud permitidos sin perder
información esencial.
"""

import copy
import dataclasses
import json
from typing import Any

from src.ai.constantes import (
    LONGITUD_ETIQUETA_FALLBACK,
    LONGITUD_TEXTO_CORTO,
    MAXIMO_CARACTERES_CONTEXTO,
)


def _json_default(obj: Any) -> Any:
    """Serializador por defecto para fracciones y objetos estructurados."""
    from fractions import Fraction
    if isinstance(obj, Fraction):
        return str(obj)
    if hasattr(obj, "rows") and hasattr(obj, "cols"):
        return {"rows": getattr(obj, "rows"), "cols": getattr(obj, "cols")}
    return str(obj)[:LONGITUD_TEXTO_CORTO]


def _build_minimal_fallback(
    herramienta: str, vista: str, max_caracteres: int
) -> str:
    """Genera bloque de contexto mínimo garantizando no exceder el límite."""
    t = str(herramienta or "")[:LONGITUD_ETIQUETA_FALLBACK]
    v = str(vista or "")[:LONGITUD_ETIQUETA_FALLBACK]
    min_dict = {"v": 1, "tool": t, "view": v, "meta": {"truncated": True}}
    min_json = json.dumps(min_dict, ensure_ascii=False, separators=(",", ":"))
    if len(min_json) > max_caracteres:
        base_len = len('{"v":1,"tool":"","view":"","meta":{"truncated":true}}')
        disponible = max(0, max_caracteres - base_len)
        t_len = min(len(t), disponible // 2)
        v_len = min(len(v), disponible - t_len)
        min_dict["tool"] = t[:t_len]
        min_dict["view"] = v[:v_len]
        min_json = json.dumps(min_dict, ensure_ascii=False, separators=(",", ":"))
    return f"[CONTEXTO]\n{min_json}\n[/CONTEXTO]"


def _recorte_eliminar_detalle_foco(c: Any) -> None:
    """Estrategia 1: Elimina el detalle opcional del paso enfocado."""
    if c.foco and c.foco.detalle:
        c.foco = dataclasses.replace(c.foco, detalle=None)


def _recorte_eliminar_extras_resultado(c: Any) -> None:
    """Estrategia 2: Elimina pasos y matrices intermedias del resultado."""
    if c.resultado:
        for clave in ("inverse", "steps", "segment_steps", "pasos"):
            c.resultado.pop(clave, None)


def _reducir_matriz_en_diccionario(mat_dict: dict, ancho_objetivo: int) -> None:
    """Reduce la ventana visible de una matriz en el diccionario de entrada."""
    if not isinstance(mat_dict, dict) or "data" not in mat_dict:
        return
    if "window" not in mat_dict:
        filas_len = len(mat_dict["data"])
        columnas_len = len(mat_dict["data"][0]) if filas_len else 0
        mat_dict["window"] = [filas_len, columnas_len]

    w_r, w_c = mat_dict["window"]
    nuevo_r = min(w_r, ancho_objetivo)
    nuevo_c = min(w_c, ancho_objetivo)
    if nuevo_r == 0:
        mat_dict.pop("data", None)
        mat_dict["window"] = [0, 0]
        return

    mat_dict["data"] = [fila[:nuevo_c] for fila in mat_dict["data"][:nuevo_r]]
    mat_dict["window"] = [nuevo_r, nuevo_c]


def _reducir_vector_en_diccionario(v: dict, ancho_objetivo: int) -> None:
    """Reduce el vector en diccionario si su longitud excede el objetivo."""
    if len(v.get("data", [])) <= ancho_objetivo:
        return
    v["data"] = v["data"][:ancho_objetivo]
    if "window" not in v:
        orientacion = v.get("orientation")
        v["window"] = [ancho_objetivo, 1] if orientacion == "column" else [1, ancho_objetivo]


def _reducir_elemento_entrada(v: Any, ancho_objetivo: int) -> None:
    """Reduce matrices o vectores individuales encontrados en la entrada."""
    if not isinstance(v, dict):
        return
    if "rows" in v and "cols" in v and "data" in v:
        _reducir_matriz_en_diccionario(v, ancho_objetivo)
    elif "data" in v and "orientation" in v:
        _reducir_vector_en_diccionario(v, ancho_objetivo)


def _recorte_ventanas_entrada(c: Any, ancho_objetivo: int) -> None:
    """Estrategia 3: Reduce el tamaño de ventana de matrices o vectores."""
    if "data" in c.entrada:
        _reducir_matriz_en_diccionario(c.entrada, ancho_objetivo)
        return
    for v in c.entrada.values():
        _reducir_elemento_entrada(v, ancho_objetivo)


def _recorte_resultado_a_estado(c: Any) -> None:
    """Estrategia 4: Colapsa el resultado a únicamente el estado y mensaje esencial."""
    if not c.resultado:
        return
    estado = c.resultado.get("status", "")
    linea = (
        c.resultado.get("message")
        or c.resultado.get("clasificacion")
        or ""
    )
    c.resultado = {"status": estado}
    if linea:
        c.resultado["message"] = linea


def _conservar_solo_primera_fila(dic: dict) -> None:
    """Conserva únicamente la primera fila del diccionario dejando las demás fuera."""
    if len(dic) <= 1:
        return
    primer_clave = next(iter(dic.keys()))
    for k in list(dic.keys()):
        if k != primer_clave:
            dic.pop(k, None)


def _recorte_filas_foco(c: Any) -> None:
    """Estrategia 5: Conserva únicamente la primera fila antes y después en el foco."""
    if not c.foco:
        return
    _conservar_solo_primera_fila(c.foco.filas_antes)
    _conservar_solo_primera_fila(c.foco.filas_despues)


def _truncar_filas_a_4_columnas(dic: dict) -> None:
    """Trunca las listas de valores de cada fila a 4 elementos."""
    for k in dic:
        dic[k] = dic[k][:4]


def _recorte_columnas_foco(c: Any) -> None:
    """Estrategia 6: Trunca celdas de filas a 4 elementos y remueve columnas del foco."""
    if not c.foco:
        return
    _truncar_filas_a_4_columnas(c.foco.filas_antes)
    _truncar_filas_a_4_columnas(c.foco.filas_despues)
    c.foco = dataclasses.replace(c.foco, columnas=None)


def _construir_foco_diccionario(foco: Any) -> dict:
    """Serializa el objeto StepRef a diccionario para el contexto."""
    f = {
        "index": foco.indice,
        "total": foco.total,
        "kind": foco.tipo,
        "op": foco.operacion,
        "rows_before": foco.filas_antes,
        "rows_after": foco.filas_despues,
    }
    if foco.columnas:
        f["cols"] = list(foco.columnas)
    if foco.detalle:
        f["detail"] = foco.detalle
    return f


def _construir_meta_contexto(c: Any, truncado: bool) -> dict:
    """Construye metadatos de ventana, obsolescencia y truncado."""
    from src.ai.context import window_note_from

    meta = {}
    if c.nota_ventana:
        meta["window"] = c.nota_ventana
    elif isinstance(c.entrada, dict):
        wn = window_note_from(*c.entrada.values())
        if wn:
            meta["window"] = wn
    if c.desactualizado:
        meta["stale"] = True
    if truncado:
        meta["truncated"] = True
    return meta


def _construir_diccionario_contexto(c: Any, truncado: bool) -> dict:
    """Construye el diccionario de datos para serialización JSON."""
    d = {
        "v": 1,
        "tool": c.herramienta,
        "view": c.vista,
        "input": c.entrada,
    }
    if c.resultado is not None:
        d["result"] = c.resultado
    if c.foco is not None:
        d["focus"] = _construir_foco_diccionario(c.foco)
    meta = _construir_meta_contexto(c, truncado)
    if meta:
        d["meta"] = meta
    return d


def _formatear_cadena_contexto(c: Any, truncado: bool = False) -> str:
    """Genera el bloque delimitado [CONTEXTO] en formato JSON."""
    datos = _construir_diccionario_contexto(c, truncado)
    res = json.dumps(
        datos, ensure_ascii=False, separators=(",", ":"), default=_json_default
    )
    return f"[CONTEXTO]\n{res}\n[/CONTEXTO]"


def ejecutar_cascada_recortes(
    ctx: Any, *, max_chars: int = MAXIMO_CARACTERES_CONTEXTO
) -> str:
    """Aplica la cascada ordenada de estrategias de recorte hasta cumplir el límite."""
    contexto_trabajo = copy.deepcopy(ctx)
    cadena = _formatear_cadena_contexto(contexto_trabajo, truncado=False)
    if len(cadena) <= max_chars:
        return cadena

    pasos_recorte = [
        lambda c: _recorte_eliminar_detalle_foco(c),
        lambda c: _recorte_eliminar_extras_resultado(c),
        lambda c: _recorte_ventanas_entrada(c, 4),
        lambda c: _recorte_ventanas_entrada(c, 3),
        lambda c: _recorte_ventanas_entrada(c, 0),
        lambda c: _recorte_resultado_a_estado(c),
        lambda c: _recorte_filas_foco(c),
        lambda c: _recorte_columnas_foco(c),
    ]

    for aplicar_estrategia in pasos_recorte:
        aplicar_estrategia(contexto_trabajo)
        cadena = _formatear_cadena_contexto(contexto_trabajo, truncado=True)
        if len(cadena) <= max_chars:
            return cadena

    return _build_minimal_fallback(
        contexto_trabajo.herramienta, contexto_trabajo.vista, max_chars
    )
