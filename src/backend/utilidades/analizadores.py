"""Analizadores sintácticos para sistemas de ecuaciones lineales."""

from fractions import Fraction
import re

from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.validadores import ValidadorMatriz


def _clave_orden_natural(cadena: str) -> list[int | str]:
    """Genera una clave de ordenamiento natural para variables alfanuméricas."""
    return [
        int(fragmento) if fragmento.isdigit() else fragmento.lower()
        for fragmento in re.split(r"(\d+)", cadena)
    ]


class AnalizadorSistema:
    """Parsea ecuaciones lineales de texto a matrices aumentadas de coeficientes."""

    EXPRESION_REGULAR_TERMINO = re.compile(
        r"([+-]?)\s*(?:(?:([\d\.\/]+)\s*\*?\s*)?([a-zA-Z][a-zA-Z0-9_]*)|([\d\.\/]+))"
    )

    @classmethod
    def _parsear_renglon(
        cls,
        indice: int,
        linea: str,
    ) -> tuple[bool, dict[str, Fraction], Fraction, str]:
        """Parsea una ecuación individual separando término independiente y variables."""
        if "=" not in linea:
            return False, {}, Fraction(0), f"Línea {indice}: Falta el signo '=' en la ecuación '{linea}'."

        partes = linea.split("=")
        if len(partes) != 2:
            return False, {}, Fraction(0), f"Línea {indice}: Debe contener un único '=' ('{linea}')."

        cadena_izq, cadena_der = partes[0].strip(), partes[1].strip()
        exito_der, valor_der, err_der = ValidadorMatriz.parsear_numero_exacto(cadena_der)
        if not exito_der:
            return False, {}, Fraction(0), f"Línea {indice}: Término independiente inválido '{cadena_der}': {err_der}"

        coefs_izq, const_izq, err_izq = cls._parsear_lado_izquierdo(cadena_izq)
        if err_izq:
            return False, {}, Fraction(0), f"Línea {indice}: {err_izq}"

        valor_der -= const_izq
        return True, coefs_izq, valor_der, ""

    @classmethod
    def _procesar_termino(
        cls,
        coincidencia: re.Match,
    ) -> tuple[bool, str | None, Fraction, str]:
        """Extrae el signo, valor y variable o constante de un término sintáctico."""
        signo_str, coef_str, nombre_var, const_str = coincidencia.groups()
        signo = -1 if signo_str == "-" else 1

        if nombre_var:
            if not coef_str:
                val = Fraction(1)
            else:
                exito, valor_parsed, _ = ValidadorMatriz.parsear_numero_exacto(coef_str)
                if not exito:
                    return False, None, Fraction(0), f"Coeficiente inválido '{coef_str}' en la variable '{nombre_var}'."
                val = valor_parsed
            return True, nombre_var, signo * val, ""

        if const_str:
            exito, valor_parsed, _ = ValidadorMatriz.parsear_numero_exacto(const_str)
            if not exito:
                return False, None, Fraction(0), f"Término independiente inválido '{const_str}'."
            return True, None, signo * valor_parsed, ""

        return True, None, Fraction(0), ""

    @classmethod
    def _parsear_lado_izquierdo(
        cls,
        cadena_izq: str,
    ) -> tuple[dict[str, Fraction], Fraction, str | None]:
        """Extrae los coeficientes de variables y constantes del lado izquierdo."""
        coeficientes: dict[str, Fraction] = {}
        suma_constantes = Fraction(0)
        cadena_limpia = cadena_izq.replace(" ", "")

        coincidencias = list(cls.EXPRESION_REGULAR_TERMINO.finditer(cadena_izq))
        reconstruido = "".join(m.group(0).replace(" ", "") for m in coincidencias)
        if len(reconstruido) != len(cadena_limpia):
            return {}, Fraction(0), f"Contiene operadores o sintaxis no válida en '{cadena_izq}'."

        for match in coincidencias:
            ok, var, valor, err = cls._procesar_termino(match)
            if not ok:
                return {}, Fraction(0), err
            if var:
                coeficientes[var] = coeficientes.get(var, Fraction(0)) + valor
            else:
                suma_constantes += valor

        return coeficientes, suma_constantes, None

    @classmethod
    def parsear_sistema(
        cls,
        texto_crudo: str,
        variables_estrictas: bool = False,
    ) -> tuple[bool, Matriz | None, list[str], str]:
        """Procesa el texto ingresado construyendo una matriz aumentada."""
        lineas = [lin.strip() for lin in texto_crudo.strip().splitlines() if lin.strip()]
        if not lineas:
            return False, None, [], "El texto ingresado está vacío."

        ecuaciones_analizadas = []
        todas_variables = set()

        for indice, linea in enumerate(lineas, 1):
            ok, coefs, valor_der, err = cls._parsear_renglon(indice, linea)
            if not ok:
                return False, None, [], err
            ecuaciones_analizadas.append((coefs, valor_der))
            todas_variables.update(coefs.keys())

        if not todas_variables:
            return False, None, [], "No se detectaron variables válidas en el sistema."

        vars_ordenadas = sorted(list(todas_variables), key=_clave_orden_natural)

        if variables_estrictas:
            coherente, err_coh = ValidadorMatriz.validar_coherencia_variables(ecuaciones_analizadas)
            if not coherente:
                return False, None, [], err_coh

        filas = len(ecuaciones_analizadas)
        columnas = len(vars_ordenadas) + 1
        datos_matriz = []

        for coefs, valor_der in ecuaciones_analizadas:
            fila = [coefs.get(v, Fraction(0)) for v in vars_ordenadas]
            fila.append(valor_der)
            datos_matriz.append(fila)

        return True, Matriz(filas, columnas, datos_matriz), vars_ordenadas, "Sistema procesado correctamente."
