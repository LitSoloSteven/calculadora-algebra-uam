"""
Módulo para operaciones aritméticas con números romanos.
Soporta suma, resta y multiplicación de 1 dígito decimal mediante sumas repetidas.
"""

from dataclasses import dataclass, field
import re
from typing import List, Tuple


class RomanNumeralError(ValueError):
    """Excepción para errores de sintaxis o reglas aritméticas en números romanos."""
    pass


DECIMAL_TO_ROMAN_PAIRS: List[Tuple[int, str]] = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]

# Expresión regular estándar para numerales romanos estrictos (1 a 3999)
ROMAN_REGEX = re.compile(
    r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$"
)


@dataclass
class RomanOperationResult:
    """Estructura del resultado de una operación aritmética romana."""
    operacion: str
    operando_a_romano: str
    operando_a_decimal: int
    operando_b_romano: str
    operando_b_decimal: int
    resultado_romano: str
    resultado_decimal: int
    pasos: List[str] = field(default_factory=list)


def int_to_roman(number: int) -> str:
    """Convierte un entero positivo (1 a 3999) a su representación en números romanos."""
    if not isinstance(number, int):
        raise RomanNumeralError(f"El valor debe ser un entero, se recibió: {type(number).__name__}")
    if number < 1 or number > 3999:
        raise RomanNumeralError(
            f"El sistema romano tradicional solo admite números entre 1 y 3999. Recibido: {number}"
        )

    result = []
    value = number
    for val, sym in DECIMAL_TO_ROMAN_PAIRS:
        while value >= val:
            result.append(sym)
            value -= val

    return "".join(result)


def roman_to_int(roman: str) -> int:
    """
    Convierte una cadena de número romano a entero.
    Aplica validación estricta de formato canónico (rechaza IIII, VX, IC, etc.).
    """
    if not isinstance(roman, str):
        raise RomanNumeralError("La entrada debe ser una cadena de texto.")

    cleaned = roman.strip().upper()

    if not cleaned:
        raise RomanNumeralError("La cadena del número romano no puede estar vacía.")

    if not ROMAN_REGEX.match(cleaned):
        raise RomanNumeralError(f"'{roman}' no es un número romano con sintaxis válida.")

    total = 0
    i = 0
    n = len(cleaned)
    char_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}

    while i < n:
        current_val = char_values[cleaned[i]]
        if i + 1 < n and current_val < char_values[cleaned[i + 1]]:
            total += char_values[cleaned[i + 1]] - current_val
            i += 2
        else:
            total += current_val
            i += 1

    canonical = int_to_roman(total)
    if canonical != cleaned:
        raise RomanNumeralError(
            f"'{roman}' no es una forma canónica válida (se esperaba '{canonical}')."
        )

    return total


class RomanCalculator:
    """Calculadora de operaciones aritméticas en números romanos con paso a paso."""

    @staticmethod
    def sumar(a: str, b: str) -> RomanOperationResult:
        """Realiza la suma A + B en números romanos."""
        val_a = roman_to_int(a)
        val_b = roman_to_int(b)
        rom_a = int_to_roman(val_a)
        rom_b = int_to_roman(val_b)

        total_dec = val_a + val_b
        if total_dec > 3999:
            raise RomanNumeralError(
                f"El resultado de la suma ({total_dec}) excede el límite máximo romano de 3999 (MMMCMXCIX)."
            )

        total_rom = int_to_roman(total_dec)

        pasos = [
            f"Paso 1: Convertir operando A a decimal -> {rom_a} = {val_a}",
            f"Paso 2: Convertir operando B a decimal -> {rom_b} = {val_b}",
            f"Paso 3: Realizar la adición decimal -> {val_a} + {val_b} = {total_dec}",
            f"Paso 4: Convertir el total a número romano -> {total_dec} = {total_rom}",
            f"Resultado final: {rom_a} + {rom_b} = {total_rom} ({total_dec})"
        ]

        return RomanOperationResult(
            operacion="suma",
            operando_a_romano=rom_a,
            operando_a_decimal=val_a,
            operando_b_romano=rom_b,
            operando_b_decimal=val_b,
            resultado_romano=total_rom,
            resultado_decimal=total_dec,
            pasos=pasos
        )

    @staticmethod
    def restar(a: str, b: str) -> RomanOperationResult:
        """
        Realiza la resta A - B en números romanos.
        Restricción: Si A <= B, se lanza excepción porque los romanos no usaban cero ni negativos.
        """
        val_a = roman_to_int(a)
        val_b = roman_to_int(b)
        rom_a = int_to_roman(val_a)
        rom_b = int_to_roman(val_b)

        if val_a == val_b:
            raise RomanNumeralError(
                f"Resta inválida ({rom_a} - {rom_b} = 0): En el sistema de numeración romana tradicional no existe el número cero."
            )
        if val_a < val_b:
            raise RomanNumeralError(
                f"Resta inválida ({rom_a} - {rom_b} = {val_a - val_b}): En el sistema de numeración romana tradicional no existen los números negativos."
            )

        total_dec = val_a - val_b
        total_rom = int_to_roman(total_dec)

        pasos = [
            f"Paso 1: Convertir minuendo A a decimal -> {rom_a} = {val_a}",
            f"Paso 2: Convertir sustraendo B a decimal -> {rom_b} = {val_b}",
            f"Paso 3: Validar que A > B ({val_a} > {val_b}) para garantizar resultado positivo no nulo.",
            f"Paso 4: Realizar la sustracción decimal -> {val_a} - {val_b} = {total_dec}",
            f"Paso 5: Convertir la diferencia a número romano -> {total_dec} = {total_rom}",
            f"Resultado final: {rom_a} - {rom_b} = {total_rom} ({total_dec})"
        ]

        return RomanOperationResult(
            operacion="resta",
            operando_a_romano=rom_a,
            operando_a_decimal=val_a,
            operando_b_romano=rom_b,
            operando_b_decimal=val_b,
            resultado_romano=total_rom,
            resultado_decimal=total_dec,
            pasos=pasos
        )

    @staticmethod
    def multiplicar_un_digito(a: str, b: str) -> RomanOperationResult:
        """
        Realiza la multiplicación A * B mediante sumas sucesivas repetidas:
        A * B = A + A + ... + A (B veces).
        Restricción estricta: Ambos operandos deben ser de 1 dígito decimal (1 al 9, es decir, de I a IX).
        """
        val_a = roman_to_int(a)
        val_b = roman_to_int(b)
        rom_a = int_to_roman(val_a)
        rom_b = int_to_roman(val_b)

        if val_a < 1 or val_a > 9:
            raise RomanNumeralError(
                f"El operando A '{rom_a}' ({val_a}) no es de 1 dígito. Debe estar entre I (1) y IX (9)."
            )
        if val_b < 1 or val_b > 9:
            raise RomanNumeralError(
                f"El operando B '{rom_b}' ({val_b}) no es de 1 dígito. Debe estar entre I (1) y IX (9)."
            )

        pasos = [
            f"Paso 1: Convertir factores a decimal -> {rom_a} = {val_a}, {rom_b} = {val_b}",
            f"Paso 2: Validar restricción de 1 dígito: {val_a} ∈ [1, 9] y {val_b} ∈ [1, 9] (Válido).",
            f"Paso 3: Aplicar definición formal de multiplicación por sumas sucesivas:",
            f"         {rom_a} × {rom_b} = sumar '{rom_a}' ({val_a}) un total de {val_b} veces."
        ]

        acumulador_dec = 0
        sumas_romanas_expr = []

        for i in range(1, val_b + 1):
            acumulador_anterior = acumulador_dec
            acumulador_dec += val_a
            sumas_romanas_expr.append(rom_a)
            acum_rom = int_to_roman(acumulador_dec)

            if i == 1:
                pasos.append(
                    f"   - Suma 1: Base inicial = {rom_a} ({val_a})"
                )
            else:
                acum_ant_rom = int_to_roman(acumulador_anterior)
                pasos.append(
                    f"   - Suma {i}: Acumulado anterior {acum_ant_rom} ({acumulador_anterior}) + {rom_a} ({val_a}) = {acum_rom} ({acumulador_dec})"
                )

        total_rom = int_to_roman(acumulador_dec)
        expresion_sumas = " + ".join(sumas_romanas_expr)

        pasos.append(f"Paso 4: Expresión expandida completa: {expresion_sumas} = {total_rom} ({acumulador_dec})")
        pasos.append(f"Resultado final: {rom_a} × {rom_b} = {total_rom} ({acumulador_dec})")

        return RomanOperationResult(
            operacion="multiplicacion",
            operando_a_romano=rom_a,
            operando_a_decimal=val_a,
            operando_b_romano=rom_b,
            operando_b_decimal=val_b,
            resultado_romano=total_rom,
            resultado_decimal=acumulador_dec,
            pasos=pasos
        )