"""Resolutor de combinación lineal de vectores en R^n."""

import re

from src.backend.constantes import (
    ERROR,
    SIN_SOLUCION,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
)
from src.backend.excepciones import ErrorVectorInvalido
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.base import (
    BaseResolutorVectores,
)
from src.backend.resolutores.operaciones_vectores.formateadores import (
    matriz_aumentada_gauss_a_latex,
)
from src.backend.resolutores.operaciones_vectores.planteamiento import (
    construir_paso_comprobacion,
    construir_pasos_planteamiento,
)
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss


def _limpiar_pasos_gauss(pasos_brutos: list[dict], k: int) -> list[dict]:
    """Descarta el paso inicial redundante y normaliza descripciones y LaTeX."""
    limpios = []
    lista = pasos_brutos[1:] if len(pasos_brutos) > 1 else pasos_brutos
    for idx, paso in enumerate(lista, start=1):
        m = paso.get("matriz") or paso.get("matrix")
        mat_tex = paso.get("detalle_latex") or paso.get("detail_latex")
        if not mat_tex and m:
            mat_tex = matriz_aumentada_gauss_a_latex(m, k)
        desc_bruta = paso.get("descripcion", "") or paso.get("description", "")
        desc_limpia = re.sub(r"^\d+\.\s*", "", desc_bruta)
        limpios.append({
            "numero_paso": idx,
            "step_number": idx,
            "descripcion": desc_limpia,
            "description": desc_limpia,
            "matriz": m.clonar() if m else None,
            "matrix": m.clonar() if m else None,
            "detalle_latex": mat_tex,
            "detail_latex": mat_tex,
        })
    return limpios


def _construir_error_combinacion_lineal(mensaje: str) -> dict:
    """Construye la respuesta estructurada de error."""
    return {
        "estado": ERROR,
        "status": "ERROR",
        "es_combinacion_lineal": False,
        "coeficientes": None,
        "coeficientes_str": None,
        "solucion_parametrica": None,
        "parametros_libres": [],
        "mensaje": mensaje,
        "message": mensaje,
        "pasos_planteamiento": [],
        "setup_steps": [],
        "pasos": [],
        "steps": [],
        "pasos_gauss": [],
        "gauss_steps": [],
        "pasos_sustitucion": [],
        "back_substitution_steps": [],
        "paso_verificacion": None,
        "verification_step": None,
    }


def _construir_aumentada(b: Matriz, vectores: list[Matriz]) -> Matriz:
    """Construye la matriz aumentada [v_1 | ... | v_k | b]."""
    n, k = b.filas, len(vectores)
    datos = [
        [vectores[j].obtener(i, 0) for j in range(k)] + [b.obtener(i, 0)]
        for i in range(n)
    ]
    return Matriz(n, k + 1, datos)


def _validar_listas_nombres(
    k: int,
    variables: list[str] | None,
    vectores: list[str] | None,
) -> str | None:
    """Valida tamaños y tipos de las listas de nombres opcionales."""
    if variables is not None and (not isinstance(variables, list) or len(variables) != k):
        return f"nombres_variables debe ser lista de longitud {k}."
    if vectores is not None and (not isinstance(vectores, list) or len(vectores) != k):
        return f"nombres_vectores debe ser lista de longitud {k}."
    return None


def _empaquetar_unica(
    b: Matriz,
    vectores: list[Matriz],
    config: tuple[list[str], list[str], str],
    resultado_gauss: dict,
    pasos_agrupados: tuple[list[dict], list[dict], list[dict]],
) -> dict:
    """Empaqueta el resultado cuando existe combinación lineal única."""
    vars_nom, vecs_nom, sujeto = config
    planteamiento, gauss_limpios, combinados = pasos_agrupados
    coefs = list(resultado_gauss.get("solucion_exacta", []))
    coefs_str = list(resultado_gauss.get("solucion", []))
    verificacion = construir_paso_comprobacion(b, vectores, coefs, vars_nom, vecs_nom)
    msg = f"b es combinación lineal {sujeto} (representación única)."
    return {
        "estado": SOLUCION_UNICA,
        "status": "UNIQUE",
        "es_combinacion_lineal": True,
        "coeficientes": coefs,
        "coeficientes_str": coefs_str,
        "solucion_parametrica": None,
        "parametros_libres": [],
        "mensaje": msg,
        "message": msg,
        "pasos_planteamiento": planteamiento,
        "setup_steps": planteamiento,
        "pasos": combinados,
        "steps": combinados,
        "pasos_gauss": gauss_limpios,
        "gauss_steps": gauss_limpios,
        "pasos_sustitucion": resultado_gauss.get("back_substitution_steps") or resultado_gauss.get("pasos_sustitucion_regresiva", []),
        "back_substitution_steps": resultado_gauss.get("back_substitution_steps") or resultado_gauss.get("pasos_sustitucion_regresiva", []),
        "paso_verificacion": verificacion,
        "verification_step": verificacion,
    }


def _empaquetar_infinitas(
    config: tuple[list[str], str],
    resultado_gauss: dict,
    pasos_agrupados: tuple[list[dict], list[dict], list[dict]],
) -> dict:
    """Empaqueta el resultado cuando hay infinitas combinaciones lineales."""
    vars_nom, sujeto = config
    planteamiento, gauss_limpios, combinados = pasos_agrupados
    sol = list(resultado_gauss.get("solucion", []))
    columnas_libres = resultado_gauss.get("columnas_libres") or []
    libres = [vars_nom[c] for c in columnas_libres]
    msg = f"b es combinación lineal {sujeto}. Existen infinitas representaciones; se muestra la paramétrica."
    return {
        "estado": SOLUCIONES_INFINITAS,
        "status": "INFINITE",
        "es_combinacion_lineal": True,
        "coeficientes": None,
        "coeficientes_str": None,
        "solucion_parametrica": sol,
        "parametros_libres": libres,
        "mensaje": msg,
        "message": msg,
        "pasos_planteamiento": planteamiento,
        "setup_steps": planteamiento,
        "pasos": combinados,
        "steps": combinados,
        "pasos_gauss": gauss_limpios,
        "gauss_steps": gauss_limpios,
        "pasos_sustitucion": resultado_gauss.get("back_substitution_steps") or resultado_gauss.get("pasos_sustitucion_regresiva", []),
        "back_substitution_steps": resultado_gauss.get("back_substitution_steps") or resultado_gauss.get("pasos_sustitucion_regresiva", []),
        "paso_verificacion": None,
        "verification_step": None,
    }


def _empaquetar_sin_solucion(
    sujeto: str,
    pasos_agrupados: tuple[list[dict], list[dict], list[dict]],
) -> dict:
    """Empaqueta el resultado cuando no existe combinación lineal."""
    planteamiento, gauss_limpios, combinados = pasos_agrupados
    msg = f"b NO es combinación lineal {sujeto}."
    return {
        "estado": SIN_SOLUCION,
        "status": "NO_SOLUTION",
        "es_combinacion_lineal": False,
        "coeficientes": None,
        "coeficientes_str": None,
        "solucion_parametrica": None,
        "parametros_libres": [],
        "mensaje": msg,
        "message": msg,
        "pasos_planteamiento": planteamiento,
        "setup_steps": planteamiento,
        "pasos": combinados,
        "steps": combinados,
        "pasos_gauss": gauss_limpios,
        "gauss_steps": gauss_limpios,
        "pasos_sustitucion": [],
        "back_substitution_steps": [],
        "paso_verificacion": None,
        "verification_step": None,
    }


def _combinar_pasos_vectoriales(planteamiento: list[dict], gauss: list[dict]) -> list[dict]:
    """Combina pasos de planteamiento y pasos gaussianos con numeración continua."""
    combinados = [dict(s) for s in planteamiento]
    for idx, gs in enumerate(gauss, start=len(planteamiento) + 1):
        s_copia = dict(gs)
        s_copia["numero_paso"] = idx
        s_copia["step_number"] = idx
        combinados.append(s_copia)
    return combinados


class ResolutorCombinacionLineal(BaseResolutorVectores):
    """Determina si un vector b es combinación lineal de un conjunto de vectores."""

    def _validar_dimensiones_vectores(self, b: Matriz, vectores: list[Matriz]) -> str | None:
        """Verifica compatibilidad de dimensiones de columna entre b y vectores."""
        try:
            self.validar_vector_columna(b, "b")
            n = b.filas
            for i, v in enumerate(vectores):
                self.validar_vector_columna(v, f"v_{i + 1}")
                if v.filas != n:
                    return f"Dimensiones incompatibles: b tiene dim {n}, v_{i + 1} tiene dim {v.filas}."
        except ErrorVectorInvalido as e:
            return str(e)
        return None

    def _validar_entradas(
        self,
        b: Matriz,
        vectores: list[Matriz],
        nombres_variables: list[str] | None,
        nombres_vectores: list[str] | None,
    ) -> str | None:
        """Valida que los vectores y nombres cumplan los invariantes de dimensión."""
        if not isinstance(vectores, list) or len(vectores) == 0:
            return "Se requiere al menos un vector."
        err_nombres = _validar_listas_nombres(len(vectores), nombres_variables, nombres_vectores)
        if err_nombres:
            return err_nombres
        return self._validar_dimensiones_vectores(b, vectores)

    def resolver(
        self,
        b: Matriz,
        vectores: list[Matriz],
        *,
        nombres_variables: list[str] | None = None,
        nombres_vectores: list[str] | None = None,
    ) -> dict:
        """Determina si b es combinación lineal de vectores mediante eliminación de Gauss."""
        err = self._validar_entradas(b, vectores, nombres_variables, nombres_vectores)
        if err:
            return _construir_error_combinacion_lineal(err)

        k = len(vectores)
        sujeto = "del vector" if k == 1 else f"de los {k} vectores"
        vars_nom = nombres_variables if nombres_variables else [f"c_{j + 1}" for j in range(k)]
        vecs_nom = nombres_vectores if nombres_vectores else [f"v_{j + 1}" for j in range(k)]

        aumentada = _construir_aumentada(b, vectores)
        planteamiento = construir_pasos_planteamiento(b, vectores, vars_nom, aumentada=aumentada)

        resolutor_g = ResolutorGauss(aumentada, nombres_variables=vars_nom)
        res_g = resolutor_g.resolver()
        gauss_limpios = _limpiar_pasos_gauss(res_g.get("pasos", []), k)
        pasos_combinados = _combinar_pasos_vectoriales(planteamiento, gauss_limpios)

        estado_g = res_g["estado"]
        agrupados = (planteamiento, gauss_limpios, pasos_combinados)
        if estado_g == SOLUCION_UNICA:
            return _empaquetar_unica(b, vectores, (vars_nom, vecs_nom, sujeto), res_g, agrupados)
        if estado_g == SOLUCIONES_INFINITAS:
            return _empaquetar_infinitas((vars_nom, sujeto), res_g, agrupados)
        return _empaquetar_sin_solucion(sujeto, agrupados)

