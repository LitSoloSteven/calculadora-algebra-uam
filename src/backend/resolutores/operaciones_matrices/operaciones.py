"""Operaciones algebraicas fundamentales entre matrices con trazabilidad paso a paso."""

from fractions import Fraction
from typing import Any

from src.backend.constantes import ERROR, EXITO
from src.backend.excepciones import ErrorDiscrepanciaDimension
from src.backend.modelos.matriz import Matriz, Numerico
from src.backend.resolutores.operaciones_matrices.determinante import (
    ResolutorDeterminante,
)
from src.backend.resolutores.trazado import TrazadorPasos
from src.backend.utilidades.formateadores import (
    formatear_fraccion_str,
    numero_a_latex,
)
from src.backend.utilidades.validadores import (
    ValidadorMatriz,
    validar_dimensiones_multiplicacion,
    validar_mismas_dimensiones,
)


class ResolutorOperacionesMatrices(TrazadorPasos):
    """Ejecuta suma, resta, producto escalar, producto matricial, transpuesta y determinante."""

    def _procesar_celda_binaria(
        self,
        matriz_a: Matriz,
        matriz_b: Matriz,
        resultado: Matriz,
        posicion_op: tuple[int, int, str],
    ) -> str:
        """Calcula el valor de la celda y registra el paso correspondiente."""
        r, c, simbolo_op = posicion_op
        val_a = matriz_a.obtener(r, c)
        val_b = matriz_b.obtener(r, c)
        res_val = val_a + val_b if simbolo_op == "+" else val_a - val_b
        resultado.establecer(r, c, res_val)
        a_tex, b_tex, res_tex = numero_a_latex(val_a), numero_a_latex(val_b), numero_a_latex(res_val)
        detalle = (
            f"C_{{{r+1},{c+1}}} = A_{{{r+1},{c+1}}} {simbolo_op} B_{{{r+1},{c+1}}} "
            f"= ({a_tex}) {simbolo_op} ({b_tex}) = {res_tex}"
        )
        self._registrar_paso(
            f"Celda ({r+1}, {c+1}): {formatear_fraccion_str(val_a)} {simbolo_op} "
            f"{formatear_fraccion_str(val_b)} = {formatear_fraccion_str(res_val)}",
            matriz_actual=resultado,
            detalle_latex=detalle,
        )
        return detalle

    def _operacion_binaria_elemento_a_elemento(
        self,
        matriz_a: Matriz,
        matriz_b: Matriz,
        *,
        simbolo_op: str,
        palabra_op: str,
    ) -> dict:
        """Helper para realizar suma o resta celda a celda."""
        self.pasos = []
        try:
            validar_mismas_dimensiones(matriz_a, matriz_b)
        except ValueError as e:
            return {"estado": ERROR, "mensaje": str(e), "matriz_resultado": None, "pasos": []}

        m, n = matriz_a.filas, matriz_a.columnas
        resultado = Matriz(m, n)
        self._registrar_paso(f"Iniciando {palabra_op} de matrices {m}×{n}")

        detalles_latex = [
            self._procesar_celda_binaria(matriz_a, matriz_b, resultado, (r, c, simbolo_op))
            for r in range(m)
            for c in range(n)
        ]

        return {
            "estado": EXITO,
            "mensaje": f"{palabra_op.capitalize()} completada con éxito ({m}×{n}).",
            "matriz_resultado": resultado,
            "pasos": self.pasos,
            "detalles_latex": detalles_latex,
        }

    def sumar(self, matriz_a: Matriz, matriz_b: Matriz) -> dict:
        """Suma matricial elemento a elemento: C_{i,j} = A_{i,j} + B_{i,j}."""
        return self._operacion_binaria_elemento_a_elemento(
            matriz_a, matriz_b, simbolo_op="+", palabra_op="suma"
        )

    def restar(self, matriz_a: Matriz, matriz_b: Matriz) -> dict:
        """Resta matricial elemento a elemento: C_{i,j} = A_{i,j} - B_{i,j}."""
        return self._operacion_binaria_elemento_a_elemento(
            matriz_a, matriz_b, simbolo_op="-", palabra_op="resta"
        )

    def multiplicar_escalar(self, escalar: Any, matriz_a: Matriz) -> dict:
        """Multiplica un escalar por una matriz conservando precision exacta."""
        self.pasos = []
        ok, escalar_frac, err = ValidadorMatriz.parsear_numero_exacto(escalar)
        if not ok:
            return {"estado": ERROR, "mensaje": f"Escalar inválido: {err}", "matriz_resultado": None, "pasos": []}

        m, n = matriz_a.filas, matriz_a.columnas
        resultado = Matriz(m, n)
        k_str = formatear_fraccion_str(escalar_frac)
        self._registrar_paso(f"Iniciando multiplicación escalar: {k_str} · A ({m}×{n})")

        detalles_latex = []
        for r in range(m):
            for c in range(n):
                val_a = matriz_a.obtener(r, c)
                prod = escalar_frac * val_a
                resultado.establecer(r, c, prod)
                k_tex, a_tex, res_tex = numero_a_latex(escalar_frac), numero_a_latex(val_a), numero_a_latex(prod)
                detalle = f"C_{{{r+1},{c+1}}} = ({k_tex}) \\cdot A_{{{r+1},{c+1}}} = ({k_tex})({a_tex}) = {res_tex}"
                detalles_latex.append(detalle)
                self._registrar_paso(
                    f"Celda ({r+1}, {c+1}): {k_str} · {formatear_fraccion_str(val_a)} = {formatear_fraccion_str(prod)}",
                    matriz_actual=resultado,
                    detalle_latex=detalle,
                )

        return {
            "estado": EXITO,
            "mensaje": f"Multiplicación escalar completada con éxito ({m}×{n}).",
            "matriz_resultado": resultado,
            "pasos": self.pasos,
            "detalles_latex": detalles_latex,
        }

    def _calcular_celda_producto(
        self,
        matriz_a: Matriz,
        matriz_b: Matriz,
        r: int,
        c: int,
        n: int,
    ) -> tuple[Fraction, str, str]:
        """Calcula el producto punto de una fila y una columna."""
        suma_celda = Fraction(0)
        terminos_texto, terminos_latex = [], []
        for k in range(n):
            val_a = matriz_a.obtener(r, k)
            val_b = matriz_b.obtener(k, c)
            suma_celda += val_a * val_b
            terminos_texto.append(f"({formatear_fraccion_str(val_a)})·({formatear_fraccion_str(val_b)})")
            terminos_latex.append(f"({numero_a_latex(val_a)})({numero_a_latex(val_b)})")

        exp_texto = f"{' + '.join(terminos_texto)} = {formatear_fraccion_str(suma_celda)}"
        exp_latex = f"C_{{{r+1},{c+1}}} = {' + '.join(terminos_latex)} = {numero_a_latex(suma_celda)}"
        return suma_celda, exp_texto, exp_latex

    def multiplicar(self, matriz_a: Matriz, matriz_b: Matriz) -> dict:
        """Multiplicacion matricial C = A * B con desglose algebraico celda a celda."""
        self.pasos = []
        try:
            validar_dimensiones_multiplicacion(matriz_a, matriz_b)
        except ValueError as e:
            return {"estado": ERROR, "mensaje": str(e), "matriz_resultado": None, "pasos": []}

        m, n, q = matriz_a.filas, matriz_a.columnas, matriz_b.columnas
        resultado = Matriz(m, q)
        self._registrar_paso(
            f"Multiplicación de A ({m}×{n}) por B ({n}×{q}). Matriz resultante C de {m}×{q}."
        )

        detalles_latex = []
        for r in range(m):
            for c in range(q):
                suma_val, exp_t, exp_l = self._calcular_celda_producto(matriz_a, matriz_b, r, c, n)
                resultado.establecer(r, c, suma_val)
                detalles_latex.append(exp_l)
                self._registrar_paso(
                    f"Fila {r+1} de A × Columna {c+1} de B: {exp_t}",
                    matriz_actual=resultado,
                    detalle_latex=exp_l,
                )

        return {
            "estado": EXITO,
            "mensaje": f"Multiplicación completada con éxito. Matriz resultante de {m}×{q}.",
            "matriz_resultado": resultado,
            "pasos": self.pasos,
            "detalles_latex": detalles_latex,
        }

    def transponer(self, matriz_a: Matriz) -> Matriz:
        """Devuelve la matriz transpuesta (Aᵀ)_{i,j} = A_{j,i} sin registrar pasos."""
        nuevos_datos = [
            [matriz_a.obtener(i, j) for i in range(matriz_a.filas)]
            for j in range(matriz_a.columnas)
        ]
        return Matriz(matriz_a.columnas, matriz_a.filas, nuevos_datos)

    def determinante(self, matriz_a: Matriz) -> Fraction:
        """Calcula el determinante de una matriz cuadrada delegando en el resolutor LU."""
        if matriz_a.filas != matriz_a.columnas:
            raise ErrorDiscrepanciaDimension(
                "determinante",
                (matriz_a.filas, matriz_a.columnas),
                (matriz_a.filas, matriz_a.filas),
            )
        resultado = ResolutorDeterminante.resolver_lu(matriz_a)
        return resultado["determinante"]
