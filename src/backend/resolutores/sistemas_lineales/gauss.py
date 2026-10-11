"""Resolutor de eliminacion gaussiana con aritmetica exacta de fracciones."""

from fractions import Fraction

from src.backend.constantes import (
    CERO_EPSILON,
    SIN_SOLUCION,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
)
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.analisis_rouche import (
    analizar_sistema_rouche,
)
from src.backend.resolutores.sistemas_lineales.sustitucion import (
    ejecutar_sustitucion_hacia_atras,
)
from src.backend.utilidades.formateadores import formatear_fraccion_str


def verificar_estado_sistema(
    matriz: Matriz, num_vars: int, rango: int, eps: float
) -> tuple[str, str]:
    """Evalua si el sistema es inconsistente, indeterminado o determinado."""
    m = matriz.filas
    for r in range(m):
        todos_ceros = all(abs(matriz.obtener(r, c)) < eps for c in range(num_vars))
        termino_no_nulo = abs(matriz.obtener(r, num_vars)) >= eps
        if todos_ceros and termino_no_nulo:
            return SIN_SOLUCION, "Sistema Inconsistente: Sin Solución."

    if rango < num_vars:
        return SOLUCIONES_INFINITAS, "Sistema Consistente Indeterminado: Presenta Infinitas Soluciones"
    return SOLUCION_UNICA, "Sistema Consistente Determinado: Presenta Solución Única."


def eliminar_fila_exacta(
    fila_pivote: list,
    fila_destino: list,
    col_idx: int,
    idx_destino: int,
    idx_pivote: int,
) -> tuple[list, str]:
    """Aplica la operacion elemental exacta F_dest = F_dest - c * F_piv."""
    piv_val = Fraction(fila_pivote[col_idx])
    dest_val = Fraction(fila_destino[col_idx])
    if dest_val == 0:
        return fila_destino, ""

    factor = dest_val / piv_val
    nueva_fila = [Fraction(tv) - factor * Fraction(pv) for tv, pv in zip(fila_destino, fila_pivote)]
    desc = (
        f"Fila {idx_destino + 1} = Fila {idx_destino + 1} − "
        f"({formatear_fraccion_str(factor)}) · Fila {idx_pivote + 1}"
    )
    return nueva_fila, desc


class ResolutorGauss:
    """Implementa el metodo de eliminacion de Gauss y analisis completo del sistema."""

    REDUCCION_COMPLETA: bool = False

    def __init__(
        self,
        matriz_aumentada: Matriz,
        eps: float = CERO_EPSILON,
        nombres_variables: list[str] | None = None,
        num_terminos_independientes: int = 1,
        variable_names: list[str] | None = None,
    ) -> None:
        """Inicializa el resolutor con la matriz aumentada y parametros de control."""
        if not isinstance(num_terminos_independientes, int) or num_terminos_independientes < 1:
            raise ValueError("num_terminos_independientes debe ser un entero >= 1.")
        if num_terminos_independientes >= matriz_aumentada.columnas:
            raise ValueError(
                "num_terminos_independientes debe ser menor que las columnas de la matriz."
            )
        self.matriz_inicial = matriz_aumentada.clonar()
        self.matriz = matriz_aumentada.clonar()
        self.eps = eps
        self.nombres_variables = nombres_variables if nombres_variables is not None else variable_names
        self.num_terminos_independientes = num_terminos_independientes
        self.pasos: list[dict] = []

    def _num_variables(self) -> int:
        """Cantidad de columnas tratadas como variables del sistema."""
        return self.matriz.columnas - self.num_terminos_independientes

    def _registrar_paso(self, descripcion: str) -> None:
        """Registra un paso intermedio con la copia de la matriz actual."""
        copia = self.matriz.clonar()
        self.pasos.append({
            "descripcion": descripcion,
            "description": descripcion,
            "matriz": copia,
            "matrix": copia,
        })

    def _seleccionar_pivote(self, col: int, fila_pivote: int) -> int | None:
        """Busca la fila con el maximo valor absoluto en la columna indicada."""
        max_fila = fila_pivote
        max_val = abs(self.matriz.obtener(fila_pivote, col))
        for r in range(fila_pivote + 1, self.matriz.filas):
            val = abs(self.matriz.obtener(r, col))
            if val > max_val:
                max_val = val
                max_fila = r
        if max_val < self.eps:
            return None
        return max_fila

    def _normalizar_pivotes(self, columnas_pivote: list[int], reduccion_completa: bool) -> None:
        """Escala cada fila pivote para que su coeficiente principal sea 1."""
        prefijo = "Normalizar pivote a 1" if reduccion_completa else "Normalizar pivote"
        for r, c in enumerate(columnas_pivote):
            val = self.matriz.obtener(r, c)
            if abs(val) >= self.eps and abs(val - 1) > self.eps:
                escala = Fraction(1) / Fraction(val)
                nueva_fila = [self.matriz.obtener(r, col) * escala for col in range(self.matriz.columnas)]
                for col_idx, elem in enumerate(nueva_fila):
                    self.matriz.establecer(r, col_idx, elem)
                self._registrar_paso(
                    f"{prefijo}: Fila {r + 1} = Fila {r + 1} / {formatear_fraccion_str(val)}"
                )

    def _registrar_seleccion_pivote(
        self, col: int, fila_pivote: int, reduccion_completa: bool
    ) -> list[int]:
        """Registra el pivote seleccionado y devuelve las filas objetivo a eliminar."""
        m = self.matriz.filas
        if reduccion_completa:
            self._registrar_paso(f"Pivote seleccionado en Fila {fila_pivote + 1}, Columna {col + 1}")
            return [r for r in range(m) if r != fila_pivote]
        val_str = formatear_fraccion_str(self.matriz.obtener(fila_pivote, col))
        self._registrar_paso(
            f"Pivote seleccionado en Fila {fila_pivote + 1}, Columna {col + 1} (valor = {val_str})"
        )
        return list(range(fila_pivote + 1, m))

    def _eliminar_filas_objetivo(
        self, fila_pivote: int, col: int, filas_objetivo: list[int]
    ) -> None:
        """Aplica la operacion de eliminacion exacta sobre cada fila objetivo."""
        fila_piv_datos = [self.matriz.obtener(fila_pivote, c) for c in range(self.matriz.columnas)]
        for r in filas_objetivo:
            if abs(self.matriz.obtener(r, col)) > self.eps:
                fila_dest_datos = [self.matriz.obtener(r, c) for c in range(self.matriz.columnas)]
                nueva_f, desc = eliminar_fila_exacta(
                    fila_piv_datos, fila_dest_datos, col, r, fila_pivote
                )
                for c_idx, elem in enumerate(nueva_f):
                    self.matriz.establecer(r, c_idx, elem)
                self._registrar_paso(desc)

    def _eliminar(self, reduccion_completa: bool) -> tuple[int, list[int]]:
        """Ejecuta la eliminacion progresiva con aritmetica exacta de fracciones."""
        m = self.matriz.filas
        fila_pivote = 0
        columnas_pivote: list[int] = []
        self._registrar_paso("Matriz inicial aumentada [A|b]:")

        for col in range(self._num_variables()):
            if fila_pivote >= m:
                break
            max_fila = self._seleccionar_pivote(col, fila_pivote)
            if max_fila is None:
                continue

            if max_fila != fila_pivote:
                self.matriz.intercambiar_filas(fila_pivote, max_fila)
                self._registrar_paso(f"Intercambio: Fila {fila_pivote + 1} ↔ Fila {max_fila + 1}")

            filas_objetivo = self._registrar_seleccion_pivote(col, fila_pivote, reduccion_completa)
            self._eliminar_filas_objetivo(fila_pivote, col, filas_objetivo)
            columnas_pivote.append(col)
            fila_pivote += 1

        self._normalizar_pivotes(columnas_pivote, reduccion_completa)
        return fila_pivote, columnas_pivote

    def resolver_reduccion(self) -> dict:
        """Ejecuta eliminacion sin sustitucion para inversion o sistemas multiples."""
        rango, columnas_pivote = self._eliminar(reduccion_completa=self.REDUCCION_COMPLETA)
        return {
            "matriz_reducida": self.matriz,
            "rango": rango,
            "columnas_pivote": columnas_pivote,
            "pasos": self.pasos,
        }

    def resolver(self) -> dict:
        """Resuelve el sistema Ax = b completo reportando clasificacion y pasos."""
        if self.num_terminos_independientes != 1:
            raise ValueError("resolver() requiere exactamente 1 termino independiente.")

        rango, columnas_pivote = self._eliminar(reduccion_completa=self.REDUCCION_COMPLETA)
        num_vars = self._num_variables()
        estado, mensaje = verificar_estado_sistema(self.matriz, num_vars, rango, self.eps)
        es_homogeneo = all(
            abs(self.matriz_inicial.obtener(r, num_vars)) < self.eps
            for r in range(self.matriz_inicial.filas)
        )
        analisis = analizar_sistema_rouche(estado, rango, num_vars, es_homogeneo, columnas_pivote)

        if estado == SIN_SOLUCION:
            return _empaquetar_respuesta_sin_solucion(self.matriz, estado, mensaje, analisis, self.pasos)

        sol_datos = ejecutar_sustitucion_hacia_atras(
            self.matriz, columnas_pivote, num_vars, self.nombres_variables
        )
        return _empaquetar_respuesta_con_solucion(
            (self.matriz, estado, mensaje), analisis, self.pasos, sol_datos
        )


def _empaquetar_respuesta_sin_solucion(
    matriz: Matriz, estado: str, mensaje: str, analisis: dict, pasos: list[dict]
) -> dict:
    """Construye el diccionario de salida cuando el sistema es inconsistente."""
    return {
        "estado": estado,
        "status": "NO_SOLUTION",
        "mensaje": mensaje,
        "message": mensaje,
        "classification": mensaje,
        "matriz_escalonada": matriz,
        "echelon_matrix": matriz,
        "solucion": None,
        "solution": None,
        "solucion_exacta": None,
        "solution_exact": None,
        "columnas_libres": [],
        "free_cols": [],
        "parametros_solucion": None,
        "solution_param": None,
        "analisis_sistema": analisis,
        "pasos": pasos,
        "steps": pasos,
        "pasos_sustitucion_regresiva": [],
        "back_substitution_steps": [],
    }


def _empaquetar_respuesta_con_solucion(
    info_sistema: tuple[Matriz, str, str],
    analisis: dict,
    pasos: list[dict],
    sol_datos: tuple[list[str], list[Fraction], list[str], list[int], dict | None],
) -> dict:
    """Construye el diccionario de salida para soluciones únicas o infinitas."""
    matriz, estado, mensaje = info_sistema
    sol, sol_exacta, pasos_sust, libres, params = sol_datos
    status = "UNIQUE_SOLUTION" if estado == SOLUCION_UNICA else "INFINITE_SOLUTIONS"
    return {
        "estado": estado,
        "status": status,
        "mensaje": mensaje,
        "message": mensaje,
        "classification": mensaje,
        "matriz_escalonada": matriz,
        "echelon_matrix": matriz,
        "solucion": sol,
        "solution": sol,
        "solucion_exacta": sol_exacta,
        "solution_exact": sol_exacta,
        "columnas_libres": libres,
        "free_cols": libres,
        "parametros_solucion": params,
        "solution_param": params,
        "analisis_sistema": analisis,
        "pasos": pasos,
        "steps": pasos,
        "pasos_sustitucion_regresiva": pasos_sust,
        "back_substitution_steps": pasos_sust,
    }
