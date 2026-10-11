"""Operaciones aritméticas con números romanos con trazabilidad paso a paso."""

from dataclasses import dataclass, field
import re

ERROR_TIPO_INVALIDO = "INVALID_TYPE"
ERROR_ENTRADA_VACIA = "EMPTY_INPUT"
ERROR_SINTAXIS_INVALIDA = "INVALID_SYNTAX"
ERROR_NO_CANONICO = "NOT_CANONICAL"
ERROR_FUERA_DE_RANGO = "OUT_OF_RANGE"
ERROR_CERO_NO_REPRESENTABLE = "ZERO_NOT_REPRESENTABLE"
ERROR_NEGATIVO_NO_REPRESENTABLE = "NEGATIVE_NOT_REPRESENTABLE"
ERROR_OPERANDO_NO_UN_DIGITO = "OPERAND_NOT_SINGLE_DIGIT"


class ErrorNumeroRomano(ValueError):
    """Excepción estructurada para errores de validación y cálculo en números romanos."""

    def __init__(self, mensaje: str, codigo: str, token_invalido: str | None = None) -> None:
        super().__init__(mensaje)
        self.codigo = codigo
        self.token_invalido = token_invalido
        self.code = codigo
        self.invalid_token = token_invalido

    def a_diccionario(self) -> dict:
        """Serializa el error a un diccionario para respuestas de API."""
        return {
            "estado": "ERROR",
            "status": "ERROR",
            "codigo_error": self.codigo,
            "error_code": self.codigo,
            "mensaje": str(self),
            "message": str(self),
            "token": self.token_invalido,
        }

    to_dict = a_diccionario


PARES_DECIMAL_A_ROMANO: list[tuple[int, str]] = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]

PATRON_ROMANO = re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")


@dataclass
class ResultadoOperacionRomana:
    """Estructura del resultado de una operación aritmética romana."""

    operacion: str
    operando_a_romano: str
    operando_a_decimal: int
    operando_b_romano: str
    operando_b_decimal: int
    resultado_romano: str
    resultado_decimal: int
    pasos: list[str] = field(default_factory=list)


def entero_a_romano(numero: int) -> str:
    """Convierte un entero positivo (1 a 3999) a su representación en números romanos."""
    if not isinstance(numero, int):
        raise ErrorNumeroRomano(
            f"El valor debe ser un entero, se recibió: {type(numero).__name__}",
            codigo=ERROR_TIPO_INVALIDO,
            token_invalido=str(numero),
        )
    if numero < 1 or numero > 3999:
        raise ErrorNumeroRomano(
            f"El sistema romano tradicional solo admite números entre 1 y 3999. Recibido: {numero}",
            codigo=ERROR_FUERA_DE_RANGO,
            token_invalido=str(numero),
        )

    resultado = []
    valor = numero
    for val, sym in PARES_DECIMAL_A_ROMANO:
        while valor >= val:
            resultado.append(sym)
            valor -= val
    return "".join(resultado)


def _validar_formato_romano(romano: str) -> str:
    """Valida tipo no nulo, no vacío y sintaxis regex del número romano."""
    if not isinstance(romano, str):
        raise ErrorNumeroRomano(
            "La entrada debe ser una cadena de texto.",
            codigo=ERROR_TIPO_INVALIDO,
            token_invalido=str(romano),
        )
    limpio = romano.strip().upper()
    if not limpio:
        raise ErrorNumeroRomano(
            "La cadena del número romano no puede estar vacía.",
            codigo=ERROR_ENTRADA_VACIA,
            token_invalido=romano,
        )
    if not PATRON_ROMANO.match(limpio):
        raise ErrorNumeroRomano(
            f"'{romano}' no es un número romano con sintaxis válida.",
            codigo=ERROR_SINTAXIS_INVALIDA,
            token_invalido=romano,
        )
    return limpio


def romano_a_entero(romano: str) -> int:
    """Convierte una cadena de número romano a entero con validación estricta canónica."""
    limpio = _validar_formato_romano(romano)
    total, i, n = 0, 0, len(limpio)
    valores_car = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    while i < n:
        actual = valores_car[limpio[i]]
        if i + 1 < n and actual < valores_car[limpio[i + 1]]:
            total += valores_car[limpio[i + 1]] - actual
            i += 2
        else:
            total += actual
            i += 1

    canonico = entero_a_romano(total)
    if canonico != limpio:
        raise ErrorNumeroRomano(
            f"'{romano}' no es una forma canónica válida (se esperaba '{canonico}').",
            codigo=ERROR_NO_CANONICO,
            token_invalido=romano,
        )
    return total


class CalculadoraRomana:
    """Calculadora de operaciones aritméticas en números romanos con paso a paso."""

    @staticmethod
    def sumar(a: str, b: str) -> ResultadoOperacionRomana:
        """Realiza la suma A + B en números romanos."""
        val_a, val_b = romano_a_entero(a), romano_a_entero(b)
        rom_a, rom_b = entero_a_romano(val_a), entero_a_romano(val_b)
        total_dec = val_a + val_b
        if total_dec > 3999:
            raise ErrorNumeroRomano(
                f"El resultado de la suma ({total_dec}) excede el límite máximo romano de 3999 (MMMCMXCIX).",
                codigo=ERROR_FUERA_DE_RANGO,
                token_invalido=str(total_dec),
            )

        total_rom = entero_a_romano(total_dec)
        pasos = [
            f"1. Convertir operando A a decimal -> {rom_a} = {val_a}",
            f"2. Convertir operando B a decimal -> {rom_b} = {val_b}",
            f"3. Realizar la adición decimal -> {val_a} + {val_b} = {total_dec}",
            f"4. Convertir el total a número romano -> {total_dec} = {total_rom}",
            f"Resultado final: {rom_a} + {rom_b} = {total_rom} ({total_dec})",
        ]
        return ResultadoOperacionRomana("suma", rom_a, val_a, rom_b, val_b, total_rom, total_dec, pasos)

    @staticmethod
    def restar(a: str, b: str) -> ResultadoOperacionRomana:
        """Realiza la resta A - B en números romanos."""
        val_a, val_b = romano_a_entero(a), romano_a_entero(b)
        rom_a, rom_b = entero_a_romano(val_a), entero_a_romano(val_b)
        if val_a == val_b:
            raise ErrorNumeroRomano(
                f"Resta inválida ({rom_a} - {rom_b} = 0): En el sistema de numeración romana tradicional no existe el número cero.",
                codigo=ERROR_CERO_NO_REPRESENTABLE,
            )
        if val_a < val_b:
            raise ErrorNumeroRomano(
                f"Resta inválida ({rom_a} - {rom_b} = {val_a - val_b}): En el sistema de numeración romana tradicional no existen los números negativos.",
                codigo=ERROR_NEGATIVO_NO_REPRESENTABLE,
            )

        total_dec = val_a - val_b
        total_rom = entero_a_romano(total_dec)
        pasos = [
            f"1. Convertir minuendo A a decimal -> {rom_a} = {val_a}",
            f"2. Convertir sustraendo B a decimal -> {rom_b} = {val_b}",
            f"3. Validar que A > B ({val_a} > {val_b}) para garantizar resultado positivo no nulo.",
            f"4. Realizar la sustracción decimal -> {val_a} - {val_b} = {total_dec}",
            f"5. Convertir la diferencia a número romano -> {total_dec} = {total_rom}",
            f"Resultado final: {rom_a} - {rom_b} = {total_rom} ({total_dec})",
        ]
        return ResultadoOperacionRomana("resta", rom_a, val_a, rom_b, val_b, total_rom, total_dec, pasos)

    @staticmethod
    def _calcular_sumas_multiplicacion(
        val_a: int, val_b: int, rom_a: str, pasos: list[str]
    ) -> tuple[int, str]:
        """Ejecuta el bucle de sumas sucesivas para la multiplicación de 1 dígito."""
        acumulador_dec = 0
        sumas_romanas = []
        for i in range(1, val_b + 1):
            acum_ant = acumulador_dec
            acumulador_dec += val_a
            sumas_romanas.append(rom_a)
            acum_rom = entero_a_romano(acumulador_dec)
            if i == 1:
                pasos.append(f"   - Suma 1: Base inicial = {rom_a} ({val_a})")
            else:
                acum_ant_rom = entero_a_romano(acum_ant)
                pasos.append(
                    f"   - Suma {i}: Acumulado anterior {acum_ant_rom} ({acum_ant}) + {rom_a} ({val_a}) = {acum_rom} ({acumulador_dec})"
                )
        return acumulador_dec, " + ".join(sumas_romanas)

    @classmethod
    def multiplicar_un_digito(cls, a: str, b: str) -> ResultadoOperacionRomana:
        """Realiza la multiplicación A * B mediante sumas sucesivas repetidas."""
        val_a, val_b = romano_a_entero(a), romano_a_entero(b)
        rom_a, rom_b = entero_a_romano(val_a), entero_a_romano(val_b)
        if val_a < 1 or val_a > 9:
            raise ErrorNumeroRomano(
                f"El operando A '{rom_a}' ({val_a}) no es de 1 dígito. Debe estar entre I (1) y IX (9).",
                codigo=ERROR_OPERANDO_NO_UN_DIGITO, token_invalido=a,
            )
        if val_b < 1 or val_b > 9:
            raise ErrorNumeroRomano(
                f"El operando B '{rom_b}' ({val_b}) no es de 1 dígito. Debe estar entre I (1) y IX (9).",
                codigo=ERROR_OPERANDO_NO_UN_DIGITO, token_invalido=b,
            )

        pasos = [
            f"1. Convertir factores a decimal -> {rom_a} = {val_a}, {rom_b} = {val_b}",
            f"2. Validar restricción de 1 dígito: {val_a} ∈ [1, 9] y {val_b} ∈ [1, 9] (Válido).",
            f"3. Aplicar definición formal de multiplicación por sumas sucesivas:",
            f"   {rom_a} × {rom_b} = sumar '{rom_a}' ({val_a}) un total de {val_b} veces.",
        ]
        acumulador_dec, exp_sumas = cls._calcular_sumas_multiplicacion(val_a, val_b, rom_a, pasos)
        total_rom = entero_a_romano(acumulador_dec)
        pasos.append(f"4. Expresión expandida completa: {exp_sumas} = {total_rom} ({acumulador_dec})")
        pasos.append(f"Resultado final: {rom_a} × {rom_b} = {total_rom} ({acumulador_dec})")
        return ResultadoOperacionRomana("multiplicacion", rom_a, val_a, rom_b, val_b, total_rom, acumulador_dec, pasos)
