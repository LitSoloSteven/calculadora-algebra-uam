class ConversorBases:
    def _limpiar_entrada(self, valor_str):
        # 1. Normalización (quitar espacios y guiones bajos)
        limpio = str(valor_str).strip().replace(" ", "").replace("_", "").upper()
        
        # 2. Extraer signo
        es_negativo = limpio.startswith("-")
        if es_negativo or limpio.startswith("+"):
            limpio = limpio[1:]
            
        # 3. Remover prefijos (0B, 0O, 0X)
        if limpio.startswith("0B") or limpio.startswith("0O") or limpio.startswith("0X"):
            limpio = limpio[2:]
            
        return es_negativo, limpio

    def decimal_a_todo(self, valor_str, base_destino='todas'):
        return self._procesar(valor_str, 10, base_destino)

    def binario_a_todo(self, valor_str, base_destino='todas'):
        return self._procesar(valor_str, 2, base_destino)

    def octal_a_todo(self, valor_str, base_destino='todas'):
        return self._procesar(valor_str, 8, base_destino)

    def hexadecimal_a_todo(self, valor_str, base_destino='todas'):
        return self._procesar(valor_str, 16, base_destino)

    def _procesar(self, valor_str, base_origen, base_destino):
        es_negativo, limpio = self._limpiar_entrada(valor_str)
        if not limpio:
            return {"error": "El valor ingresado está vacío."}
            
        try:
            magnitud = int(limpio, base_origen)
            num = -magnitud if es_negativo else magnitud
            
            res = self._formatear_salida(num)
            res["pasos"] = self._generar_pasos(limpio, magnitud, base_origen, base_destino, es_negativo)
            return res
        except ValueError:
            return {"error": f"Valor inválido para la base {base_origen}."}

    def _formatear_salida(self, num):
        signo = "-" if num < 0 else ""
        mag = abs(num)
        return {
            "decimal": f"{signo}{mag}",
            "binario": f"{signo}{format(mag, 'b')}",
            "octal": f"{signo}{format(mag, 'o')}",
            "hexadecimal": f"{signo}{format(mag, 'X')}"
        }

    def _generar_pasos(self, limpio, magnitud, base_origen, base_destino_str, es_negativo):
        pasos = []
        if base_origen != 10:
            pasos.append(self._generar_expansion_posicional(limpio, base_origen, magnitud))
            
        destinos = []
        if base_destino_str == 'todas':
            destinos = [b for b in [2, 8, 10, 16] if b != base_origen and b != 10]
        else:
            map_base = {'binario': 2, 'octal': 8, 'decimal': 10, 'hexadecimal': 16}
            b = map_base.get(base_destino_str)
            if b and b != 10 and b != base_origen:
                destinos.append(b)
                
        for dest in destinos:
            pasos.append(self._generar_divisiones_sucesivas(magnitud, dest))
            
        return pasos

    def _generar_expansion_posicional(self, limpio, base_origen, magnitud):
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
                "producto": producto
            })
            
        return {
            "tipo": "expansion_posicional",
            "base_origen": base_origen,
            "terminos": terminos,
            "total": magnitud
        }

    def _generar_divisiones_sucesivas(self, magnitud, base_destino):
        filas = []
        dividendo = magnitud
        if dividendo == 0:
            filas.append({
                "dividendo": 0,
                "divisor": base_destino,
                "cociente": 0,
                "residuo": 0
            })
            resultado = "0"
        else:
            while dividendo > 0:
                cociente = dividendo // base_destino
                residuo = dividendo % base_destino
                filas.append({
                    "dividendo": dividendo,
                    "divisor": base_destino,
                    "cociente": cociente,
                    "residuo": residuo
                })
                dividendo = cociente
                
            chars = "0123456789ABCDEF"
            resultado = "".join(chars[f["residuo"]] for f in reversed(filas))
            
        return {
            "tipo": "division_sucesiva",
            "base_destino": base_destino,
            "filas": filas,
            "lectura": "Se lee de abajo hacia arriba",
            "resultado": resultado
        }