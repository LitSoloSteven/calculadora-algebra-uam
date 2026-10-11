"""Conversor y trazador didáctico de cambios de base numérica posicional."""

from typing import Any

from src.backend.constantes import ERROR, EXITO


class ConversorBases:
    """Convierte números entre bases 2, 8, 10 y 16 con desglose de pasos."""

    @staticmethod
    def _limpiar_entrada(valor_str: Any, base_origen: int) -> tuple[bool, str]:
        """Normaliza la cadena, extrae el signo y remueve prefijos estándar."""
        limpio = str(valor_str).strip().replace(" ", "").replace("_", "").upper()
        es_negativo = limpio.startswith("-")
        if es_negativo or limpio.startswith("+"):
            limpio = limpio[1:]

        prefijos = {2: "0B", 8: "0O", 16: "0X"}
        prefijo = prefijos.get(base_origen)
        if prefijo and limpio.startswith(prefijo):
            limpio = limpio[2:]
        return es_negativo, limpio

    def decimal_a_todo(self, valor_str: Any, base_destino: str = "todas") -> dict:
        """Convierte desde base decimal a las demás bases."""
        return self._procesar(valor_str, 10, base_destino)

    def binario_a_todo(self, valor_str: Any, base_destino: str = "todas") -> dict:
        """Convierte desde base binaria a las demás bases."""
        return self._procesar(valor_str, 2, base_destino)

    def octal_a_todo(self, valor_str: Any, base_destino: str = "todas") -> dict:
        """Convierte desde base octal a las demás bases."""
        return self._procesar(valor_str, 8, base_destino)

    def hexadecimal_a_todo(self, valor_str: Any, base_destino: str = "todas") -> dict:
        """Convierte desde base hexadecimal a las demás bases."""
        return self._procesar(valor_str, 16, base_destino)

    def _procesar(self, valor_str: Any, base_origen: int, base_destino: str) -> dict:
        """Parsea la entrada, calcula representaciones y genera el paso a paso."""
        es_negativo, limpio = self._limpiar_entrada(valor_str, base_origen)
        if not limpio:
            return {"estado": ERROR, "error": "El valor ingresado está vacío."}

        try:
            magnitud = int(limpio, base_origen)
            num = -magnitud if es_negativo else magnitud
            res = self._formatear_salida(num)
            res["estado"] = EXITO
            res["pasos"] = self._generar_pasos(limpio, magnitud, base_origen, base_destino, es_negativo)
            return res
        except ValueError:
            return {"estado": ERROR, "error": f"Valor inválido para la base {base_origen}."}

    @staticmethod
    def _formatear_salida(num: int) -> dict:
        """Devuelve las cadenas formateadas en decimal, binario, octal y hexadecimal."""
        signo = "-" if num < 0 else ""
        mag = abs(num)
        return {
            "decimal": f"{signo}{mag}",
            "binario": f"{signo}{format(mag, 'b')}",
            "octal": f"{signo}{format(mag, 'o')}",
            "hexadecimal": f"{signo}{format(mag, 'X')}",
        }

    def _generar_pasos(
        self,
        limpio: str,
        magnitud: int,
        base_origen: int,
        base_destino_str: str,
        es_negativo: bool,
    ) -> list[dict]:
        """Genera expansiones polinomiales y divisiones sucesivas según origen y destino."""
        pasos = []
        if base_origen != 10:
            pasos.append(self._generar_expansion_posicional(limpio, base_origen, magnitud, es_negativo))

        destinos = []
        if base_destino_str == "todas":
            destinos = [b for b in [2, 8, 10, 16] if b != base_origen and b != 10]
        else:
            map_base = {"binario": 2, "octal": 8, "decimal": 10, "hexadecimal": 16}
            b = map_base.get(base_destino_str)
            if b and b != 10 and b != base_origen:
                destinos.append(b)

        for dest in destinos:
            pasos.append(self._generar_divisiones_sucesivas(magnitud, dest, es_negativo))
        return pasos

    @staticmethod
    def _generar_expansion_posicional(
        limpio: str, base_origen: int, magnitud: int, es_negativo: bool
    ) -> dict:
        """Genera el desglose posicional en potencias de la base de origen."""
        terminos = []
        longitud = len(limpio)
        for i, digito in enumerate(limpio):
            potencia = longitud - 1 - i
            val = int(digito, base_origen)
            peso = base_origen ** potencia
            producto = val * peso
            terminos.append({
                "digito": digito,
                "valor": val,
                "potencia": potencia,
                "peso": peso,
                "producto": producto,
            })
        return {
            "tipo": "expansion_posicional",
            "base_origen": base_origen,
            "terminos": terminos,
            "total": f"-{magnitud}" if es_negativo else str(magnitud),
            "es_negativo": es_negativo,
        }

    @staticmethod
    def _generar_divisiones_sucesivas(magnitud: int, base_destino: int, es_negativo: bool) -> dict:
        """Genera el algoritmo de divisiones sucesivas hacia la base de destino."""
        filas = []
        dividendo = magnitud
        if dividendo == 0:
            filas.append({"dividendo": 0, "divisor": base_destino, "cociente": 0, "residuo": 0})
            resultado = "0"
        else:
            while dividendo > 0:
                cociente = dividendo // base_destino
                residuo = dividendo % base_destino
                filas.append({"dividendo": dividendo, "divisor": base_destino, "cociente": cociente, "residuo": residuo})
                dividendo = cociente
            chars = "0123456789ABCDEF"
            resultado_abs = "".join(chars[f["residuo"]] for f in reversed(filas))
            resultado = f"-{resultado_abs}" if es_negativo else resultado_abs

        return {
            "tipo": "division_sucesiva",
            "base_destino": base_destino,
            "filas": filas,
            "lectura": "Se lee de abajo hacia arriba",
            "resultado": resultado,
        }
