"""Módulo de contexto y serialización para el asistente de IA.

Proporciona estructuras de datos y funciones para capturar el estado matemático
actual y empaquetarlo en un bloque JSON estructurado con control estricto de tamaño.
"""

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Dict, List, Sequence, Tuple

from src.ai.constantes import (
    COLUMNAS_MAXIMAS_RECORTE,
    LONGITUD_MAXIMA_CADENA_USUARIO,
    LONGITUD_MAXIMA_NUMERO,
    MAXIMO_CARACTERES_CONTEXTO,
    MAXIMO_MATRIZ_COMPLETA,
    TAMANIO_VENTANA_MATRIZ,
)
from src.ai.estrategias_recorte import (
    _build_minimal_fallback,
    ejecutar_cascada_recortes,
)


@dataclass(frozen=True, init=False)
class StepRef:
    """Referencia inmutable al paso enfocado para explicación pedagógica."""

    indice: int
    total: int
    tipo: str
    operacion: str
    filas_antes: Dict[str, List[str]]
    filas_despues: Dict[str, List[str]]
    columnas: Tuple[int, int] | None
    detalle: Dict[str, Any] | None

    def __init__(
        self,
        indice: int = 0,
        total: int = 0,
        tipo: str = "",
        operacion: str = "",
        *,
        filas_antes: Dict[str, List[str]] | None = None,
        filas_despues: Dict[str, List[str]] | None = None,
        columnas: Tuple[int, int] | None = None,
        detalle: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        object.__setattr__(self, "indice", kwargs.get("index", indice))
        object.__setattr__(self, "total", kwargs.get("total", total))
        object.__setattr__(self, "tipo", kwargs.get("kind", tipo))
        object.__setattr__(self, "operacion", kwargs.get("op", operacion))
        object.__setattr__(self, "filas_antes", kwargs.get("rows_before", filas_antes) or {})
        object.__setattr__(self, "filas_despues", kwargs.get("rows_after", filas_despues) or {})
        object.__setattr__(self, "columnas", kwargs.get("cols", columnas))
        object.__setattr__(self, "detalle", kwargs.get("detail", detalle))

    def __getattr__(self, n: str) -> Any:
        m = {
            "index": "indice", "kind": "tipo", "op": "operacion",
            "rows_before": "filas_antes", "rows_after": "filas_despues",
            "cols": "columnas", "detail": "detalle",
        }
        if n in m:
            return getattr(self, m[n])
        raise AttributeError(f"'{type(self).__name__}' no tiene atributo '{n}'")


@dataclass(init=False)
class AIContext:
    """Contenedor de estado para el bloque de contexto enviado a la IA."""

    herramienta: str
    vista: str
    etiqueta: str
    entrada: Dict[str, Any]
    resultado: Dict[str, Any] | None
    foco: StepRef | None
    nota_ventana: str | None
    desactualizado: bool
    vacio: bool

    def __init__(
        self,
        herramienta: str = "",
        vista: str = "",
        etiqueta: str = "",
        entrada: Dict[str, Any] | None = None,
        *,
        resultado: Dict[str, Any] | None = None,
        foco: StepRef | None = None,
        nota_ventana: str | None = None,
        desactualizado: bool = False,
        vacio: bool = False,
        **kwargs: Any,
    ) -> None:
        self.herramienta = kwargs.get("tool", herramienta)
        self.vista = kwargs.get("view", vista)
        self.etiqueta = kwargs.get("label", etiqueta)
        self.entrada = kwargs.get("input", entrada) if entrada is not None else kwargs.get("input", {})
        self.resultado = kwargs.get("result", resultado)
        self.foco = kwargs.get("focus", foco)
        self.nota_ventana = kwargs.get("window_note", nota_ventana)
        self.desactualizado = kwargs.get("stale", desactualizado)
        self.vacio = kwargs.get("empty", vacio)

    def __getattr__(self, n: str) -> Any:
        m = {
            "tool": "herramienta", "view": "vista", "label": "etiqueta",
            "input": "entrada", "result": "resultado", "focus": "foco",
            "window_note": "nota_ventana", "stale": "desactualizado", "empty": "vacio",
        }
        if n in m:
            return getattr(self, m[n])
        raise AttributeError(f"'{type(self).__name__}' no tiene atributo '{n}'")

    def __setattr__(self, n: str, v: Any) -> None:
        m = {
            "tool": "herramienta", "view": "vista", "label": "etiqueta",
            "input": "entrada", "result": "resultado", "focus": "foco",
            "window_note": "nota_ventana", "stale": "desactualizado", "empty": "vacio",
        }
        super().__setattr__(m.get(n, n), v)


def clip_text(texto: str, longitud_maxima: int) -> str:
    """Recorta una cadena al tamaño indicado añadiendo puntos suspensivos si excede."""
    s = str(texto)
    if len(s) <= longitud_maxima:
        return s
    return s[:longitud_maxima - 1] + "…"


def sanitize_user_string(
    cadena: str, limite: int = LONGITUD_MAXIMA_CADENA_USUARIO
) -> str:
    """Limpia caracteres de control y etiquetas de contexto en texto de usuario."""
    s = str(cadena)
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)
    s = re.sub(r"(?i)\[/?CONTEXTO\]", "", s)
    return clip_text(s, limite)


def compact_number(valor: str, longitud_maxima: int = LONGITUD_MAXIMA_NUMERO) -> str:
    """Formatea valores numéricos largos aproximando fracciones cuando excede el límite."""
    s = str(valor).strip()
    if len(s) <= longitud_maxima:
        return s
    if "/" in s:
        try:
            num, den = s.split("/")
            aprox = f"≈{float(num) / float(den):.1f}"
            if len(aprox) <= longitud_maxima:
                return aprox
        except Exception:
            pass
    return clip_text(s, longitud_maxima)


def _es_celda_invalida(val: str) -> bool:
    """Evalúa si una celda contiene un valor textual no numérico o inválido."""
    if val in ("0", "", "0.0"):
        return False
    try:
        float(val.split("/")[0]) if "/" in val else float(val)
        return False
    except Exception:
        return True


def describir_matriz(
    filas: Sequence[Sequence[Any]],
    *,
    maximo_completa: int = MAXIMO_MATRIZ_COMPLETA,
    ventana: int = TAMANIO_VENTANA_MATRIZ,
) -> dict:
    """Genera descriptor estructurado de una matriz para el contexto de IA."""
    total_filas = len(filas)
    total_columnas = len(filas[0]) if total_filas > 0 else 0
    if total_filas <= maximo_completa and total_columnas <= maximo_completa:
        datos = [[compact_number(c) for c in r] for r in filas]
        return {"rows": total_filas, "cols": total_columnas, "data": datos}

    filas_v, columnas_v = min(total_filas, ventana), min(total_columnas, ventana)
    datos, invalidos = [], 0
    for i in range(total_filas):
        fila_datos = []
        for j in range(total_columnas):
            val = str(filas[i][j]).strip()
            if _es_celda_invalida(val):
                invalidos += 1
            if i < filas_v and j < columnas_v:
                fila_datos.append(compact_number(val))
        if i < filas_v:
            datos.append(fila_datos)

    res = {
        "rows": total_filas, "cols": total_columnas,
        "window": [filas_v, columnas_v], "data": datos,
    }
    if invalidos > 0:
        res["invalid"] = invalidos
    return res


def window_note_from(*descriptores: dict) -> str | None:
    """Devuelve nota descriptiva de la ventana si alguna matriz está truncada."""
    con_ventana = [
        d for d in descriptores
        if isinstance(d, dict) and isinstance(d.get("window"), (list, tuple)) and len(d["window"]) >= 2
    ]
    if not con_ventana:
        return None
    mayor = max(con_ventana, key=lambda d: d.get("rows", 0) * d.get("cols", 0))
    w, c = mayor["window"][0], mayor["window"][1]
    filas, columnas = mayor.get("rows", 0), mayor.get("cols", 0)
    return f"ventana {w}×{c} de {filas}×{columnas}"


def extraer_filas(
    filas_datos: Sequence[Sequence[Any]],
    indices_filas: Sequence[int],
    columna_centro: int,
    columnas_maximas: int = COLUMNAS_MAXIMAS_RECORTE,
) -> Tuple[Dict[str, List[str]], Tuple[int, int] | None]:
    """Extrae un subconjunto de filas y columnas centrado alrededor de un pivote."""
    total_columnas = len(filas_datos[0]) if filas_datos else 0
    inicio_columna, fin_columna, rango_columnas = 0, total_columnas, None

    if total_columnas > columnas_maximas:
        inicio_columna = max(0, columna_centro - columnas_maximas // 2)
        fin_columna = min(total_columnas, inicio_columna + columnas_maximas)
        if fin_columna - inicio_columna < columnas_maximas:
            inicio_columna = max(0, fin_columna - columnas_maximas)
        rango_columnas = (inicio_columna + 1, fin_columna)

    resultado = {}
    for indice in indices_filas:
        if 0 <= indice < len(filas_datos):
            fila = filas_datos[indice]
            resultado[str(indice + 1)] = [
                compact_number(c) for c in fila[inicio_columna:fin_columna]
            ]
    return resultado, rango_columnas


def _normalizar_para_huella(objeto: Any) -> Any:
    """Normaliza recursivamente estructuras de datos para generar huella determinista."""
    if isinstance(objeto, dict):
        return {str(k): _normalizar_para_huella(v) for k, v in objeto.items()}
    if isinstance(objeto, (list, tuple)):
        return [_normalizar_para_huella(x) for x in objeto]
    return objeto


def fingerprint(objeto: Any) -> str:
    """Calcula el hash SHA-1 determinista de una estructura de datos de entrada."""
    serializado = json.dumps(_normalizar_para_huella(objeto), sort_keys=True, default=str)
    return hashlib.sha1(serializado.encode("utf-8")).hexdigest()


def is_stale(entrada_actual: Any, huella_resultado: str | None) -> bool:
    """Verifica si la entrada actual difiere de la huella del resultado previo."""
    if huella_resultado is None:
        return False
    return fingerprint(entrada_actual) != huella_resultado


def _serialize_context_core(
    ctx: AIContext, *, max_chars: int = MAXIMO_CARACTERES_CONTEXTO
) -> str:
    """Delega la ejecución de la cascada de recorte al motor especializado."""
    return ejecutar_cascada_recortes(ctx, max_chars=max_chars)


def serialize_context(
    ctx: AIContext, *, max_chars: int = MAXIMO_CARACTERES_CONTEXTO
) -> str:
    """Serializa el contexto a bloque seguro [CONTEXTO] con fallback robusto ante errores."""
    try:
        return ejecutar_cascada_recortes(ctx, max_chars=max_chars)
    except Exception:
        h = getattr(ctx, "herramienta", getattr(ctx, "tool", ""))
        v = getattr(ctx, "vista", getattr(ctx, "view", ""))
        return _build_minimal_fallback(h, v, max_chars)
