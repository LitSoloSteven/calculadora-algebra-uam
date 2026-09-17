class ConversorBases:
    def decimal_a_todo(self, valor_str):
        try:
            num = int(valor_str)
            res = self._formatear_salida(num)
            res["pasos"] = self._generar_pasos(valor_str, 10)
            return res
        except ValueError:
            return {"error": "Valor decimal inválido. Solo usa números del 0 al 9."}

    def binario_a_todo(self, valor_str):
        try:
            num = int(valor_str, 2)
            res = self._formatear_salida(num)
            res["pasos"] = self._generar_pasos(valor_str, 2)
            return res
        except ValueError:
            return {"error": "Valor binario inválido. Solo usa 0 y 1."}

    def octal_a_todo(self, valor_str):
        try:
            num = int(valor_str, 8)
            res = self._formatear_salida(num)
            res["pasos"] = self._generar_pasos(valor_str, 8)
            return res
        except ValueError:
            return {"error": "Valor octal inválido. Solo usa números del 0 al 7."}

    def hexadecimal_a_todo(self, valor_str):
        try:
            num = int(valor_str, 16)
            res = self._formatear_salida(num)
            res["pasos"] = self._generar_pasos(valor_str, 16)
            return res
        except ValueError:
            return {"error": "Valor hexadecimal inválido. Usa 0-9 y A-F."}

    def _formatear_salida(self, num):
        return {
            "decimal": str(num),
            "binario": bin(num)[2:],
            "octal": oct(num)[2:],
            "hexadecimal": hex(num)[2:].upper()
        }

    def _generar_pasos(self, valor_str, base_origen):
        num = int(valor_str, base_origen)
        pasos = []
        
        if base_origen != 10:
            paso1 = {
                "titulo": f"Paso 1: Convertir de base {base_origen} a Decimal",
                "explicacion": "Se multiplica cada dígito por la base origen elevada a su posición (de derecha a izquierda, empezando en 0).",
            }
            explicacion_mat = []
            longitud = len(valor_str)
            for i, digito in enumerate(valor_str):
                potencia = longitud - 1 - i
                val = int(digito, 16) if base_origen == 16 else int(digito)
                explicacion_mat.append(f"({val} × {base_origen}^{potencia})")
            
            paso1["operacion"] = f"{' + '.join(explicacion_mat)} = {num}"
            pasos.append(paso1)
        
        paso_final = {
            "titulo": "Paso Final: Convertir de Decimal a la Base Destino",
            "explicacion": "Se divide el número decimal de forma sucesiva entre la base destino anotando los residuos.",
            "operacion": "El resultado final se lee tomando el último cociente seguido de los residuos de abajo hacia arriba."
        }
        pasos.append(paso_final)
        
        return pasos