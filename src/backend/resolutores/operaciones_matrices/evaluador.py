"""Evaluador de expresiones algebraicas matriciales complejas paso a paso."""

from fractions import Fraction
import re

from src.backend.constantes import ERROR, EXITO
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.analizador_expresiones import (
    convertir_a_rpn,
    tokenizar_expresion,
)
from src.backend.resolutores.operaciones_matrices.formateadores import (
    matriz_a_latex,
    multiplicar_matriz_a_latex,
    sumar_restar_matriz_a_latex,
)
from src.backend.resolutores.operaciones_matrices.operaciones import (
    ResolutorOperacionesMatrices,
)


def _es_escalar(val: object) -> bool:
    """Indica si el valor es un escalar numerico en vez de una Matriz."""
    return not isinstance(val, Matriz)


def _crear_paso_segmento(
    datos_operacion: tuple[str, str, str],
    operandos: tuple[str, str | None],
    tex: str,
    res_mat: Matriz,
    pasos: list,
) -> dict:
    """Construye un paso intermedio con claves duales E4 para compatibilidad."""
    temp, muestra, tipo = datos_operacion
    nom_a, nom_b = operandos
    res_tex = matriz_a_latex(res_mat)
    return {
        "variable_temporal": temp,
        "temp_var": temp,
        "muestra_operacion": muestra,
        "operation_display": muestra,
        "tipo_operacion": tipo,
        "operation_type": tipo,
        "nombre_operando_a": nom_a,
        "operand_a_name": nom_a,
        "nombre_operando_b": nom_b,
        "operand_b_name": nom_b,
        "matriz_simbolica_latex": tex,
        "symbolic_matrix_latex": tex,
        "matriz_resultado_latex": res_tex,
        "result_matrix_latex": res_tex,
        "matriz_resultado": res_mat,
        "result_matrix": res_mat,
        "pasos_celda_a_celda": pasos,
        "cell_by_cell_steps": pasos,
    }


def _empaquetar_error_evaluador(mensaje: str) -> dict:
    """Construye la respuesta de error para el evaluador de expresiones."""
    return {
        "estado": ERROR,
        "status": "ERROR",
        "mensaje": mensaje,
        "message": mensaje,
        "matriz_resultado": None,
        "result_matrix": None,
        "pasos_segmento": [],
        "segment_steps": [],
    }


def _empaquetar_exito_evaluador(
    expresion: str, final_nom: str, final_val: Matriz, pasos: list
) -> dict:
    """Construye la respuesta exitosa con claves duales para el evaluador."""
    res_tex = matriz_a_latex(final_val)
    msg = f"Expresión '{expresion}' resuelta con éxito."
    return {
        "estado": EXITO,
        "status": "SUCCESS",
        "mensaje": msg,
        "message": msg,
        "variable_final": final_nom,
        "final_variable": final_nom,
        "final_var": final_nom,
        "matriz_resultado": final_val,
        "result_matrix": final_val,
        "matriz_resultado_latex": res_tex,
        "result_matrix_latex": res_tex,
        "pasos_segmento": pasos,
        "segment_steps": pasos,
    }


class EvaluadorExpresionesMatriciales:
    """Parsea y evalua expresiones matriciales (ej. 2A - B(C - D^T)) en pasos atómicos."""

    def __init__(self) -> None:
        """Inicializa el evaluador con el resolutor de operaciones base."""
        self.resolutor_ops = ResolutorOperacionesMatrices()
        self.pasos_globales: list[dict] = []

    def _tokenizar(self, expr: str) -> list[str]:
        """Convierte la cadena en tokens e inserta multiplicaciones implicitas."""
        return tokenizar_expresion(expr)

    def _a_rpn(self, tokens: list[str]) -> list[str]:
        """Aplica Shunting-Yard para convertir tokens a Notacion Polaca Inversa."""
        return convertir_a_rpn(tokens)

    def _procesar_transpuesta(self, pila: list, contador: int) -> int:
        """Aplica la transpuesta sobre el operando superior de la pila."""
        if not pila:
            raise ValueError("Operación de transpuesta sin operando.")
        nombre, val = pila.pop()
        if _es_escalar(val):
            pila.append((f"{nombre}ᵀ", val))
            return contador

        temp = f"T_{{{contador}}}"
        res_mat = self.resolutor_ops.transponer(val)
        paso = _crear_paso_segmento(
            (temp, f"{temp} = {nombre}^T", "Transposición"),
            (nombre, None),
            f"{nombre}^T",
            res_mat,
            [],
        )
        self.pasos_globales.append(paso)
        pila.append((temp, res_mat))
        return contador + 1

    def _procesar_negacion(self, pila: list, contador: int) -> int:
        """Aplica la negacion unaria sobre el operando superior de la pila."""
        if not pila:
            raise ValueError("Operación de negación sin operando.")
        nombre, val = pila.pop()
        if _es_escalar(val):
            pila.append((f"-{nombre}", -val))
            return contador

        temp = f"T_{{{contador}}}"
        res_dict = self.resolutor_ops.multiplicar_escalar(Fraction(-1), val)
        res_mat = res_dict["matriz_resultado"]
        paso = _crear_paso_segmento(
            (temp, f"{temp} = -{nombre}", "Negación"),
            (nombre, None),
            f"-{nombre}",
            res_mat,
            [],
        )
        self.pasos_globales.append(paso)
        pila.append((temp, res_mat))
        return contador + 1

    def _ejecutar_binaria_matrices(
        self, token: str, nom_a: str, val_a: Matriz, nom_b: str, val_b: Matriz
    ) -> tuple[Matriz, list, str, str]:
        """Aplica suma, resta o producto entre dos matrices."""
        if token == "*":
            res = self.resolutor_ops.multiplicar(val_a, val_b)
            if res["estado"] == ERROR:
                raise ValueError(f"Error ({nom_a} * {nom_b}): {res['mensaje']}")
            return res["matriz_resultado"], res["pasos"], multiplicar_matriz_a_latex(val_a, val_b), "Multiplicación de Matrices"
        if token == "+":
            res = self.resolutor_ops.sumar(val_a, val_b)
            if res["estado"] == ERROR:
                raise ValueError(f"Error ({nom_a} + {nom_b}): {res['mensaje']}")
            return res["matriz_resultado"], res["pasos"], sumar_restar_matriz_a_latex(val_a, val_b, "+"), "Suma"
        res = self.resolutor_ops.restar(val_a, val_b)
        if res["estado"] == ERROR:
            raise ValueError(f"Error ({nom_a} - {nom_b}): {res['mensaje']}")
        return res["matriz_resultado"], res["pasos"], sumar_restar_matriz_a_latex(val_a, val_b, "-"), "Resta"

    def _resolver_producto_escalar_matriz(
        self, izq_nom: str, izq_val: Any, der_nom: str, der_val: Any
    ) -> tuple[Matriz, list, str, str]:
        """Calcula el producto entre un escalar y una matriz."""
        esc = izq_val if _es_escalar(izq_val) else der_val
        mat = der_val if _es_escalar(izq_val) else izq_val
        res_dict = self.resolutor_ops.multiplicar_escalar(esc, mat)
        return (
            res_dict["matriz_resultado"],
            res_dict["pasos"],
            f"{izq_nom} \\cdot {der_nom}",
            "Multiplicación Escalar",
        )

    def _despachar_binaria(
        self,
        token: str,
        izq: tuple[str, Any],
        der: tuple[str, Any],
    ) -> tuple[Matriz, list, str, str]:
        """Determina y ejecuta la operación binaria entre operandos mixtos o matriciales."""
        izq_nom, izq_val = izq
        der_nom, der_val = der
        hay_escalar = _es_escalar(izq_val) or _es_escalar(der_val)
        if token == "*" and hay_escalar:
            return self._resolver_producto_escalar_matriz(izq_nom, izq_val, der_nom, der_val)
        if token in ("+", "-") and hay_escalar:
            raise ValueError("No se puede sumar ni restar un escalar con una matriz.")
        return self._ejecutar_binaria_matrices(token, izq_nom, izq_val, der_nom, der_val)

    def _procesar_binaria(self, token: str, pila: list, contador: int) -> int:
        """Resuelve una operacion binaria (+, -, *) entre operandos de la pila."""
        if len(pila) < 2:
            raise ValueError("Expresión matemática mal formada.")
        der = pila.pop()
        izq = pila.pop()

        if token == "*" and _es_escalar(izq[1]) and _es_escalar(der[1]):
            pila.append((f"{izq[1] * der[1]}", izq[1] * der[1]))
            return contador

        temp = f"T_{{{contador}}}"
        res_mat, pasos, tex, op_pal = self._despachar_binaria(token, izq, der)
        paso = _crear_paso_segmento(
            (temp, f"{temp} = {izq[0]} {token} {der[0]}", op_pal),
            (izq[0], der[0]),
            tex,
            res_mat,
            pasos,
        )
        self.pasos_globales.append(paso)
        pila.append((temp, res_mat))
        return contador + 1

    def _consumir_token_rpn(
        self,
        t: str,
        pila: list,
        matrices_dict: dict[str, Matriz],
        contador: int,
    ) -> int:
        """Procesa un token individual en el recorrido RPN y actualiza la pila."""
        if re.match(r"^\d+(\.\d+)?$", t):
            pila.append((t, Fraction(t)))
            return contador
        if re.match(r"^[A-Za-z][A-Za-z0-9_]*$", t):
            if t not in matrices_dict:
                raise ValueError(f"La matriz '{t}' no ha sido definida.")
            pila.append((t, matrices_dict[t]))
            return contador
        if t == "ᵀ":
            return self._procesar_transpuesta(pila, contador)
        if t == "¬":
            return self._procesar_negacion(pila, contador)
        if t in ("+", "-", "*"):
            return self._procesar_binaria(t, pila, contador)
        return contador

    def evaluar(self, expresion: str, matrices_dict: dict[str, Matriz]) -> dict:
        """Evalua la expresion algebraica completa sobre el catalogo de matrices."""
        self.pasos_globales = []
        try:
            tokens = self._tokenizar(expresion)
            rpn = self._a_rpn(tokens)
            pila: list = []
            contador = 1
            for t in rpn:
                contador = self._consumir_token_rpn(t, pila, matrices_dict, contador)

            if len(pila) != 1:
                return _empaquetar_error_evaluador("La expresión no pudo ser evaluada completamente.")
            final_nom, final_val = pila.pop()
            if _es_escalar(final_val):
                return _empaquetar_error_evaluador("El resultado final es un escalar, no una matriz.")
        except ValueError as e:
            return _empaquetar_error_evaluador(str(e))

        return _empaquetar_exito_evaluador(expresion, final_nom, final_val, self.pasos_globales)
