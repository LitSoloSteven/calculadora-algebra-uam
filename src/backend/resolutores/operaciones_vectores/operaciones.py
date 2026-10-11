"""Operaciones algebraicas vectoriales con trazabilidad paso a paso."""

from typing import Any

from src.backend.constantes import ERROR, EXITO
from src.backend.excepciones import ErrorVectorInvalido
from src.backend.modelos.matriz import Matriz, Numerico
from src.backend.resolutores.operaciones_vectores.base import (
    BaseResolutorVectores,
)
from src.backend.resolutores.operaciones_vectores.formateadores import (
    formatear_vector_latex,
    vector_a_latex,
)
from src.backend.utilidades.formateadores import (
    formatear_fraccion_str,
    numero_a_latex,
)
from src.backend.utilidades.validadores import ValidadorMatriz


def _formatear_latex_binario(
    resultado: Matriz,
    v1: Matriz,
    v2: Matriz,
    nombres_simbolo: tuple[str, str, str],
) -> tuple[str, str]:
    """Genera el formateo LaTeX del resultado vectorial y de la ecuación final."""
    nombre1, nombre2, latex_simbolo = nombres_simbolo
    res_tex = vector_a_latex(resultado)
    v1_tex = vector_a_latex(v1)
    v2_tex = vector_a_latex(v2)
    v1_nom = formatear_vector_latex(nombre1)
    v2_nom = formatear_vector_latex(nombre2)
    vector_final_latex = (
        rf"\mathbf{{w}} = {v1_nom} {latex_simbolo} {v2_nom} = {v1_tex} {latex_simbolo} {v2_tex} = {res_tex}"
    )
    return res_tex, vector_final_latex


def _formatear_latex_escalar(
    resultado: Matriz,
    v: Matriz,
    escalar_info: tuple[Numerico, str, str, str],
) -> tuple[str, str]:
    """Genera el formateo LaTeX para el resultado de multiplicación escalar."""
    k_frac, k_tex, nombre, nombre_resultado = escalar_info
    res_tex = vector_a_latex(resultado)
    v_tex = vector_a_latex(v)
    v_nom = formatear_vector_latex(nombre)
    res_nom = formatear_vector_latex(nombre_resultado)
    denominador = getattr(k_frac, "denominator", 1)
    k_paren = rf"\left({k_tex}\right)" if denominador != 1 else f"({k_tex})"
    vector_final_latex = rf"{res_nom} = {k_tex} \cdot {v_nom} = {k_paren} {v_tex} = {res_tex}"
    return res_tex, vector_final_latex


def _empaquetar_error_vector(mensaje: str) -> dict:
    """Construye la respuesta de error para operaciones vectoriales."""
    return {
        "estado": ERROR,
        "status": "ERROR",
        "mensaje": mensaje,
        "message": mensaje,
        "matriz_resultado": None,
        "result_matrix": None,
        "pasos": [],
        "steps": [],
        "detalles_latex": [],
        "latex_details": [],
    }


def _empaquetar_exito_vector(
    mensaje: str,
    res_info: tuple[Matriz, str, str],
    pasos: list[dict],
    detalles_latex: list[str],
) -> dict:
    """Construye la respuesta de éxito con claves duales para operaciones vectoriales."""
    resultado, res_tex, vector_final_latex = res_info
    return {
        "estado": EXITO,
        "status": "SUCCESS",
        "mensaje": mensaje,
        "message": mensaje,
        "matriz_resultado": resultado,
        "result_matrix": resultado,
        "matriz_resultado_latex": res_tex,
        "vector_resultado_latex": vector_final_latex,
        "pasos": pasos,
        "steps": pasos,
        "detalles_latex": detalles_latex,
        "latex_details": detalles_latex,
    }


class ResolutorOperacionesVectores(BaseResolutorVectores):
    """Ejecuta suma, resta y multiplicación escalar con vectores de R^n."""

    def _calcular_celda_binaria(
        self,
        v1: Matriz,
        v2: Matriz,
        resultado: Matriz,
        posicion_op: tuple[int, str, str],
    ) -> str:
        """Calcula el valor de la componente y registra el paso en el trazador."""
        i, op_simbolo, latex_simbolo = posicion_op
        a = v1.obtener(i, 0) if self.es_vector_columna(v1) else v1.obtener(0, i)
        b = v2.obtener(i, 0) if self.es_vector_columna(v2) else v2.obtener(0, i)
        c = a + b if op_simbolo == "+" else a - b

        if self.es_vector_columna(resultado):
            resultado.establecer(i, 0, c)
        else:
            resultado.establecer(0, i, c)

        a_tex = numero_a_latex(a)
        b_tex = numero_a_latex(b)
        c_tex = numero_a_latex(c)
        detalle_latex = f"w_{{{i + 1}}} = ({a_tex}) {latex_simbolo} ({b_tex}) = {c_tex}"
        self._registrar_paso(
            f"Componente {i + 1}: {formatear_fraccion_str(a)} {op_simbolo} "
            f"{formatear_fraccion_str(b)} = {formatear_fraccion_str(c)}",
            matriz_actual=resultado,
            detalle_latex=detalle_latex,
        )
        return detalle_latex

    def _operacion_binaria(
        self,
        v1: Matriz,
        v2: Matriz,
        config: tuple[str, str, bool, str, str, str],
    ) -> dict:
        """Implementación compartida de suma y resta vectorial."""
        nombre1, nombre2, estricto, op_simbolo, op_palabra, latex_simbolo = config
        self.pasos = []
        try:
            self.validar_vector(v1, nombre1)
            self.validar_vector(v2, nombre2)
            v1, v2, ajuste_msg = self.armonizar_dimensiones(v1, v2, nombre1, nombre2, estricto)
        except ErrorVectorInvalido as e:
            return _empaquetar_error_vector(str(e))

        dim = self.dimension_vector(v1)
        resultado = Matriz(v1.filas, v1.columnas)
        self._registrar_paso(f"Iniciando {op_palabra} de vectores (dim {dim})")
        if ajuste_msg:
            self._registrar_paso(ajuste_msg)

        detalles_latex = [
            self._calcular_celda_binaria(v1, v2, resultado, (i, op_simbolo, latex_simbolo))
            for i in range(dim)
        ]
        res_tex, vector_final_latex = _formatear_latex_binario(
            resultado, v1, v2, (nombre1, nombre2, latex_simbolo)
        )
        detalles_latex.append(vector_final_latex)
        mensaje = f"{op_palabra.capitalize()} de vectores completada (dim {dim})."
        return _empaquetar_exito_vector(
            mensaje, (resultado, res_tex, vector_final_latex), self.pasos, detalles_latex
        )

    def sumar(
        self,
        v1: Matriz,
        v2: Matriz,
        *,
        nombre1: str = "v_1",
        nombre2: str = "v_2",
        estricto: bool = False,
    ) -> dict:
        """Suma vectorial componente a componente."""
        return self._operacion_binaria(
            v1, v2, (nombre1, nombre2, estricto, "+", "suma", "+")
        )

    def restar(
        self,
        v1: Matriz,
        v2: Matriz,
        *,
        nombre1: str = "v_1",
        nombre2: str = "v_2",
        estricto: bool = False,
    ) -> dict:
        """Resta vectorial componente a componente."""
        return self._operacion_binaria(
            v1, v2, (nombre1, nombre2, estricto, "-", "resta", "-")
        )

    def _calcular_celda_escalar(
        self,
        v: Matriz,
        resultado: Matriz,
        posicion_k: tuple[int, Any, str, str],
    ) -> str:
        """Calcula el producto de una componente por el escalar y registra el paso."""
        i, k_frac, k_tex, nombre_resultado = posicion_k
        val = v.obtener(i, 0) if self.es_vector_columna(v) else v.obtener(0, i)
        prod = k_frac * val
        if self.es_vector_columna(resultado):
            resultado.establecer(i, 0, prod)
        else:
            resultado.establecer(0, i, prod)

        val_tex = numero_a_latex(val)
        prod_tex = numero_a_latex(prod)
        detalle_latex = f"{nombre_resultado}_{{{i + 1}}} = ({k_tex}) \\cdot ({val_tex}) = {prod_tex}"
        self._registrar_paso(
            f"Componente {i + 1}: {formatear_fraccion_str(k_frac)} · {formatear_fraccion_str(val)} = {formatear_fraccion_str(prod)}",
            matriz_actual=resultado,
            detalle_latex=detalle_latex,
        )
        return detalle_latex

    def _validar_y_parsear_escalar(
        self, v: Matriz, nombre: str, escalar: Numerico
    ) -> tuple[Any, str | None]:
        """Valida el vector y convierte el escalar a Fraction exacta."""
        try:
            self.validar_vector(v, nombre)
        except ErrorVectorInvalido as e:
            return None, str(e)
        ok, k_frac, err = ValidadorMatriz.parsear_numero_exacto(escalar)
        if not ok:
            return None, f"Escalar inválido: {err}"
        return k_frac, None

    def multiplicar_escalar(
        self,
        escalar: Numerico,
        v: Matriz,
        *,
        nombre: str = "v",
        nombre_resultado: str = "w",
    ) -> dict:
        """Multiplicación de un escalar por un vector en R^n."""
        self.pasos = []
        k_frac, err = self._validar_y_parsear_escalar(v, nombre, escalar)
        if err:
            return _empaquetar_error_vector(err)

        dim = self.dimension_vector(v)
        resultado = Matriz(v.filas, v.columnas)
        k_tex = numero_a_latex(k_frac)
        self._registrar_paso(
            f"Iniciando multiplicación escalar: {formatear_fraccion_str(k_frac)} · {nombre} (dim {dim})"
        )

        detalles_latex = [
            self._calcular_celda_escalar(v, resultado, (i, k_frac, k_tex, nombre_resultado))
            for i in range(dim)
        ]
        res_tex, vector_final_latex = _formatear_latex_escalar(
            resultado, v, (k_frac, k_tex, nombre, nombre_resultado)
        )
        detalles_latex.append(vector_final_latex)
        mensaje = f"Multiplicación escalar completada (dim {dim})."
        return _empaquetar_exito_vector(
            mensaje, (resultado, res_tex, vector_final_latex), self.pasos, detalles_latex
        )
