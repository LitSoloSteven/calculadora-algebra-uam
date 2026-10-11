"""Resolutor de matriz inversa mediante Gauss-Jordan sobre [A | I] con verificacion."""

from fractions import Fraction

from src.backend.constantes import ERROR, EXITO, SINGULAR
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import (
    matriz_a_latex,
    matriz_particionada_a_latex,
)
from src.backend.resolutores.operaciones_matrices.operaciones import (
    ResolutorOperacionesMatrices,
)
from src.backend.resolutores.sistemas_lineales.gauss_jordan import (
    ResolutorGaussJordan,
)
from src.backend.utilidades.formateadores import formatear_fraccion_str, numero_a_latex


class ResolutorInversa:
    """Calcula la matriz inversa A^-1 con desgloses, pasos y verificaciones algebraicas."""

    def __init__(self) -> None:
        """Inicializa el resolutor con soporte de operaciones matriciales."""
        self.resolutor_ops = ResolutorOperacionesMatrices()

    def _construir_aumentada(self, matriz_a: Matriz, n: int) -> tuple[Matriz, str]:
        """Construye la matriz [A | I] de tamano n x 2n."""
        datos = []
        for i in range(n):
            fila = [matriz_a.obtener(i, j) for j in range(n)]
            fila.extend(Fraction(1) if i == j else Fraction(0) for j in range(n))
            datos.append(fila)
        aumentada = Matriz(n, 2 * n, datos)
        return aumentada, matriz_particionada_a_latex(aumentada, n)

    def _extraer_inversa(self, reducida: Matriz, n: int) -> Matriz:
        """Extrae el bloque derecho n x n de la matriz reducida [I | A^-1]."""
        datos = [
            [reducida.obtener(i, n + j) for j in range(n)]
            for i in range(n)
        ]
        return Matriz(n, n, datos)

    def _formatear_pasos(self, pasos: list[dict], n: int, construir_latex: bool) -> list[dict]:
        """Formatea los pasos con matriz particionada en LaTeX si se solicita."""
        formateados = []
        for p in pasos:
            mat = p.get("matriz")
            tex = matriz_particionada_a_latex(mat, n) if (mat and construir_latex) else None
            desc = p.get("descripcion", p.get("description", ""))
            formateados.append({
                "descripcion": desc,
                "description": desc,
                "matriz": mat,
                "matrix": mat,
                "detalle_latex": tex,
                "detail_latex": tex,
            })
        return formateados

    def _verificar_producto(
        self,
        matriz_a: Matriz,
        inversa: Matriz,
        n: int,
        inverso: bool,
    ) -> dict:
        """Verifica que el producto A · A^-1 o A^-1 · A coincida con la identidad."""
        izq = inversa if inverso else matriz_a
        der = matriz_a if inverso else inversa
        res = self.resolutor_ops.multiplicar(izq, der)
        prod = res.get("matriz_resultado")
        identidad = Matriz(n, n, [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)])
        es_exacto = (prod == identidad) if prod else False
        etiq = "A^{-1} \\cdot A = I" if inverso else "A \\cdot A^{-1} = I"
        status_word = "Correcto" if es_exacto else "Incorrecto"
        izq_nom = "A^{-1}" if inverso else "A"
        der_nom = "A" if inverso else "A^{-1}"
        prod_tex = matriz_a_latex(prod) if prod else ""
        detalle_latex = f"{izq_nom} \\cdot {der_nom} = {prod_tex} \\quad (\\text{{{status_word}}})"
        desc = f"Verificación {'A⁻¹·A' if inverso else 'A·A⁻¹'} = I."
        return {
            "propiedad": etiq,
            "description": desc,
            "descripcion": desc,
            "se_cumple": es_exacto,
            "coincide": es_exacto,
            "matriz_producto_latex": prod_tex,
            "product_latex": prod_tex,
            "detalle_latex": detalle_latex,
            "detail_latex": detalle_latex,
        }

    def _verificar_propiedad_transpuesta(self, matriz_a: Matriz, inversa: Matriz) -> dict:
        """Verifica la identidad (A^T)^-1 = (A^-1)^T mediante (A^-1)^T · A^T = I."""
        trans_a = self.resolutor_ops.transponer(matriz_a)
        trans_inv = self.resolutor_ops.transponer(inversa)
        n = matriz_a.filas
        res_mul = self.resolutor_ops.multiplicar(trans_inv, trans_a)
        prod = res_mul.get("matriz_resultado")
        identidad = Matriz(n, n, [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)])
        es_exacto = (prod == identidad) if prod else False
        status_word = "Coinciden" if es_exacto else "Difieren"
        prod_tex = matriz_a_latex(prod) if prod else ""
        detalle_latex = f"(A^{{-1}})^T \\cdot A^T = {prod_tex} \\quad (\\text{{{status_word}}})"
        desc = "Verificación (Aᵀ)⁻¹ = (A⁻¹)ᵀ."
        return {
            "propiedad": "(A^T)^{-1} = (A^{-1})^T",
            "description": desc,
            "descripcion": desc,
            "se_cumple": es_exacto,
            "coincide": es_exacto,
            "inversa_transpuesta_latex": matriz_a_latex(trans_inv),
            "detalle_latex": detalle_latex,
            "detail_latex": detalle_latex,
        }

    @staticmethod
    def _validar_cuadrada(matriz_a: Matriz) -> str | None:
        """Valida si el objeto es Matriz y si es cuadrada, devolviendo mensaje de error o None."""
        if not isinstance(matriz_a, Matriz):
            return "Se esperaba una instancia de Matriz."
        if matriz_a.filas != matriz_a.columnas:
            return f"La matriz debe ser cuadrada: recibido {matriz_a.filas}×{matriz_a.columnas}."
        return None

    def _construir_resultado_exito(
        self,
        matriz_a: Matriz,
        inversa: Matriz,
        meta: tuple[Fraction, str, list[dict]],
    ) -> dict:
        """Construye el diccionario de resultado exitoso con verificaciones."""
        det, aug_tex, pasos = meta
        n = matriz_a.filas
        v1 = self._verificar_producto(matriz_a, inversa, n, inverso=False)
        v2 = self._verificar_producto(matriz_a, inversa, n, inverso=True)
        v3 = self._verificar_propiedad_transpuesta(matriz_a, inversa)
        return {
            "estado": EXITO,
            "status": "SUCCESS",
            "mensaje": f"Inversa calculada con éxito ({n}×{n}).",
            "message": f"Inversa calculada con éxito ({n}×{n}).",
            "determinante": det,
            "determinant": det,
            "matriz_aumentada_inicial_latex": aug_tex,
            "inversa": inversa,
            "inverse": inversa,
            "inversa_latex": matriz_a_latex(inversa),
            "pasos": pasos,
            "steps": pasos,
            "paso_verificacion": v1,
            "verification_step": v1,
            "paso_verificacion_inverso": v2,
            "verification_reverse_step": v2,
            "paso_propiedad_transpuesta": v3,
            "transpose_property_step": v3,
        }

    def resolver(
        self,
        matriz_a: Matriz,
        *,
        construir_detalle_latex: bool = True,
        **opciones,
    ) -> dict:
        """Calcula A^-1 mediante Gauss-Jordan o reporta que la matriz es singular."""
        if "build_step_latex" in opciones and opciones["build_step_latex"] is not None:
            construir_detalle_latex = bool(opciones["build_step_latex"])
        err = self._validar_cuadrada(matriz_a)
        if err:
            return {"estado": ERROR, "status": "ERROR", "mensaje": err, "message": err}

        n = matriz_a.filas
        det = self.resolutor_ops.determinante(matriz_a)
        if det == 0:
            return _construir_respuesta_singular(
                det, "La matriz es singular (det = 0). No tiene inversa."
            )

        aumentada, aug_tex = self._construir_aumentada(matriz_a, n)
        reduccion = ResolutorGaussJordan(aumentada, num_terminos_independientes=n).resolver_reduccion()

        if reduccion["rango"] < n:
            msg = f"La matriz es singular (rango {reduccion['rango']} < {n}). No tiene inversa."
            pasos_fmt = self._formatear_pasos(reduccion["pasos"], n, construir_detalle_latex)
            return _construir_respuesta_singular(det, msg, aug_tex, pasos_fmt)

        inversa = self._extraer_inversa(reduccion["matriz_reducida"], n)
        pasos = self._formatear_pasos(reduccion["pasos"], n, construir_detalle_latex)
        return self._construir_resultado_exito(matriz_a, inversa, (det, aug_tex, pasos))


def _construir_respuesta_singular(
    det: Fraction,
    mensaje: str,
    aug_tex: str | None = None,
    pasos: list[dict] | None = None,
) -> dict:
    """Construye el diccionario de salida cuando la matriz no es invertible."""
    res = {
        "estado": SINGULAR,
        "status": "SINGULAR",
        "mensaje": mensaje,
        "message": mensaje,
        "determinante": det,
        "determinant": det,
    }
    if pasos is not None:
        res["matriz_aumentada_inicial_latex"] = aug_tex
        res["pasos"] = pasos
        res["steps"] = pasos
    return res
