"""Validación y parseo de entradas numéricas y matrices."""

from fractions import Fraction
from typing import Any

from src.backend.constantes import (
    LIMITE_RECONSTRUCCION_ESTRICTA,
    LONGITUD_MAXIMA_CADENA_NUMERO,
    MSJ_NOTACION_CIENTIFICA_NO_SOPORTADA,
    MSJ_NUMERO_DEMASIADO_LARGO,
)
from src.backend.excepciones import ErrorDiscrepanciaDimension
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.verificacion import verificar_solucion


class ValidadorMatriz:
    """Métodos estáticos para validación y parseo de matrices y números."""

    verificar_solucion = staticmethod(verificar_solucion)

    @staticmethod
    def _rechazar_cadena_no_soportada(val_limpio: str) -> str | None:
        """Determina si la cadena contiene notación científica o longitud excesiva."""
        if "e" in val_limpio or "E" in val_limpio:
            return MSJ_NOTACION_CIENTIFICA_NO_SOPORTADA
        if len(val_limpio) > LONGITUD_MAXIMA_CADENA_NUMERO:
            return MSJ_NUMERO_DEMASIADO_LARGO
        return None

    @staticmethod
    def parsear_numero_exacto(val: Any) -> tuple[bool, Fraction, str]:
        """Convierte una entrada numérica a fracción exacta con validaciones DoS."""
        if isinstance(val, (int, Fraction)):
            return True, Fraction(val), ""

        if isinstance(val, float):
            try:
                return True, Fraction(val).limit_denominator(LIMITE_RECONSTRUCCION_ESTRICTA), ""
            except (ValueError, OverflowError):
                try:
                    return True, Fraction(str(val)), ""
                except (ValueError, ZeroDivisionError):
                    return False, Fraction(0), "Valor flotante no convertible a fracción."

        if isinstance(val, str):
            val_limpio = val.strip()
            if not val_limpio:
                return False, Fraction(0), "El campo está vacío."

            rechazo = ValidadorMatriz._rechazar_cadena_no_soportada(val_limpio)
            if rechazo is not None:
                return False, Fraction(0), rechazo

            try:
                return True, Fraction(val_limpio), ""
            except ZeroDivisionError:
                return False, Fraction(0), "División por cero en la fracción ingresada."
            except ValueError:
                return False, Fraction(0), "El valor ingresado no es un número o fracción válida."

        return False, Fraction(0), f"Tipo no soportado: {type(val).__name__}"

    @staticmethod
    def parsear_numero(val: Any) -> tuple[bool, float, str]:
        """Parsea una entrada numérica retornando un flotante serializable."""
        ok, fraccion, mensaje = ValidadorMatriz.parsear_numero_exacto(val)
        if not ok:
            return False, 0.0, mensaje
        return True, float(fraccion), ""

    @staticmethod
    def validar_dimensiones(filas: int, columnas: int) -> tuple[bool, str]:
        """Valida que las dimensiones sean enteros positivos mayores a cero."""
        if not isinstance(filas, int) or not isinstance(columnas, int):
            return False, "Las dimensiones deben ser números enteros."
        if filas <= 0 or columnas <= 0:
            return False, "El número de filas y columnas debe ser mayor a 0."
        return True, "Dimensiones válidas."

    @staticmethod
    def validar_datos_matriz(
        datos: list[list[float]],
        filas_esperadas: int,
        columnas_esperadas: int,
    ) -> tuple[bool, str]:
        """Verifica que la matriz posea la forma bidimensional requerida."""
        if len(datos) != filas_esperadas:
            return False, f"Se esperaban {filas_esperadas} filas, pero se recibieron {len(datos)}."
        for i, fila in enumerate(datos):
            if len(fila) != columnas_esperadas:
                return False, f"La fila {i} tiene {len(fila)} columnas; se esperaban {columnas_esperadas}."
        return True, "Datos matriciales estructurados correctamente."

    @staticmethod
    def validar_y_parsear_matriz_cruda(
        datos_crudos: list[list[Any]],
        filas_esperadas: int,
        columnas_esperadas: int,
    ) -> tuple[bool, list[list[Fraction]], str]:
        """Valida y convierte una cuadrícula de celdas a fracciones exactas."""
        if len(datos_crudos) != filas_esperadas:
            return False, [], f"Se esperaban {filas_esperadas} filas, pero hay {len(datos_crudos)}."

        matriz_analizada = []
        for indice_fila, fila in enumerate(datos_crudos):
            if len(fila) != columnas_esperadas:
                return False, [], f"La fila {indice_fila + 1} no tiene {columnas_esperadas} columnas."
            fila_analizada = []
            for indice_col, item in enumerate(fila):
                exito, valor_frac, mensaje_err = ValidadorMatriz.parsear_numero_exacto(item)
                if not exito:
                    return False, [], f"Error en celda [{indice_fila + 1}, {indice_col + 1}]: {mensaje_err}"
                fila_analizada.append(valor_frac)
            matriz_analizada.append(fila_analizada)

        return True, matriz_analizada, "Matriz parseada correctamente."

    @staticmethod
    def validar_coherencia_variables(
        ecuaciones_analizadas: list[tuple[dict[str, Fraction], Fraction]],
    ) -> tuple[bool, str]:
        """Verifica que las ecuaciones no formen sistemas inconexos o disjuntos."""
        if len(ecuaciones_analizadas) <= 1:
            return True, "Coherencia de variables válida."

        for indice, (coeficientes, _) in enumerate(ecuaciones_analizadas, 1):
            variables_actuales = set(coeficientes.keys())
            otras_variables = set().union(
                *[e[0].keys() for i, e in enumerate(ecuaciones_analizadas) if i != indice - 1]
            )
            if not variables_actuales.intersection(otras_variables):
                return False, (
                    f"Línea {indice}: Las variables {sorted(list(variables_actuales))} "
                    f"no tienen relación ni comparten columnas con el resto de ecuaciones."
                )

        return True, "Coherencia de variables válida."

    @staticmethod
    def validar_datos_crudos(datos_crudos: Any) -> tuple[bool, str]:
        """Verifica que la estructura de datos cruda no sea nula ni vacía."""
        if datos_crudos is None:
            return False, "Los datos de la matriz no pueden ser nulos."
        if isinstance(datos_crudos, list) and len(datos_crudos) == 0:
            return False, "La matriz no puede estar vacía."
        return True, "Datos válidos."


def validar_mismas_dimensiones(matriz_a: Matriz, matriz_b: Matriz) -> None:
    """Valida dimensiones idénticas en ambas matrices para operaciones elementales."""
    if matriz_a.filas != matriz_b.filas or matriz_a.columnas != matriz_b.columnas:
        raise ErrorDiscrepanciaDimension(
            operacion="suma/resta",
            forma_a=(matriz_a.filas, matriz_a.columnas),
            forma_b=(matriz_b.filas, matriz_b.columnas),
        )


def validar_dimensiones_multiplicacion(matriz_a: Matriz, matriz_b: Matriz) -> None:
    """Valida compatibilidad entre columnas de A y filas de B para producto matricial."""
    if matriz_a.columnas != matriz_b.filas:
        raise ErrorDiscrepanciaDimension(
            operacion="multiplicación (A.columnas debe igualar B.filas)",
            forma_a=(matriz_a.filas, matriz_a.columnas),
            forma_b=(matriz_b.filas, matriz_b.columnas),
        )
