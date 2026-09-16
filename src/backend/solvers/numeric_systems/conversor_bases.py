class ConversorBases:

    def decimal_a_todo(self, valor_str):
        try:
            num = int(valor_str)
            return self._formatear_salida(num)
        except ValueError:
            return {"error": "Valor decimal inválido. Solo usa números del 0 al 9."}

    def binario_a_todo(self, valor_str):
        try:
            num = int(valor_str, 2)
            return self._formatear_salida(num)
        except ValueError:
            return {"error": "Valor binario inválido. Solo usa 0 y 1."}

    def octal_a_todo(self, valor_str):
        try:
            num = int(valor_str, 8)
            return self._formatear_salida(num)
        except ValueError:
            return {"error": "Valor octal inválido. Solo usa números del 0 al 7."}

    def hexadecimal_a_todo(self, valor_str):
        try:
            num = int(valor_str, 16)
            return self._formatear_salida(num)
        except ValueError:
            return {"error": "Valor hexadecimal inválido. Usa 0-9 y A-F."}

    def _formatear_salida(self, num):
        return {
            "decimal": str(num),
            "binario": bin(num)[2:],
            "octal": oct(num)[2:],
            "hexadecimal": hex(num)[2:].upper()
        }