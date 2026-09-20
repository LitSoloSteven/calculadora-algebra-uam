import re
from src.backend.models.matrix import Matrix
from src.backend.utils.validators import MatrixValidator
from fractions import Fraction

class SystemParser:
    # Regex: Grupo 1 = Signo (+/-). Alternativa A (término con variable):
    # Grupo 2 = Coeficiente (ej: 2, 3.5, 1/2), Grupo 3 = Variable (ej: x, y, z, x1).
    # Alternativa B (término puramente numérico / constante en el LHS): Grupo 4.
    TERM_REGEX = re.compile(r'([+-]?)\s*(?:([\d\.\/]*)\s*\*?\s*([a-zA-Z][a-zA-Z0-9_]*)|([\d\.\/]+))')

    @classmethod
    def parse_system(cls, raw_text: str, strict_variables: bool = True) -> tuple[bool, Matrix | None, list[str], str]:
        """
        Procesa el texto ingresado y retorna:
        (éxito: bool, matriz_aumentada: Matrix, lista_variables: list[str], mensaje: str)
        """
        lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
        if not lines:
            return False, None, [], "El texto ingresado está vacío."

        parsed_equations = []
        all_variables = set()

        for line_idx, line in enumerate(lines, 1):
            if '=' not in line:
                return False, None, [], f"Línea {line_idx}: Falta el signo '=' en la ecuación '{line}'."
            
            parts = line.split('=')
            if len(parts) != 2:
                return False, None, [], f"Línea {line_idx}: Debe contener un único '=' ('{line}')."

            lhs_str, rhs_str = parts[0].strip(), parts[1].strip()

            # Delegado a MatrixValidator
            success_rhs, rhs_val, err_rhs = MatrixValidator.parse_number_exact(rhs_str)
            if not success_rhs:
                return False, None, [], f"Línea {line_idx}: Término independiente inválido '{rhs_str}': {err_rhs}"

            eq_coeffs, const_lhs, err_lhs = cls._parse_lhs(lhs_str)
            if err_lhs:
                return False, None, [], f"Línea {line_idx}: {err_lhs}"

            # Las constantes que aparecen en el lado izquierdo se trasladan al
            # lado derecho en vez de rechazar la ecuación (ej. "2x + 5 = 10" -> "2x = 5").
            rhs_val -= const_lhs

            parsed_equations.append((eq_coeffs, rhs_val))
            all_variables.update(eq_coeffs.keys())

        if not all_variables:
            return False, None, [], "No se detectaron variables válidas en el sistema."

        def natural_sort_key(s):
            # Divide el string en fragmentos de texto y números. 
            # Convierte los fragmentos numéricos a enteros para un orden matemático real.
            return [int(texto) if texto.isdigit() else texto.lower() for texto in re.split(r'(\d+)', s)]

        sorted_vars = sorted(list(all_variables), key=natural_sort_key)
        
        # Delegado a MatrixValidator
        if strict_variables:
            is_coherent, err_coherence = MatrixValidator.validate_variable_coherence(parsed_equations)
            if not is_coherent:
                return False, None, [], err_coherence

        # Construcción del objeto Matrix
        rows = len(parsed_equations)
        cols = len(sorted_vars) + 1  # Coeficientes + columna b
        matrix_data = []

        for eq_coeffs, rhs_val in parsed_equations:
            row = [eq_coeffs.get(var, Fraction(0)) for var in sorted_vars]
            row.append(rhs_val)
            matrix_data.append(row)

        matrix = Matrix(rows, cols, matrix_data)
        return True, matrix, sorted_vars, "Sistema procesado correctamente."

    @classmethod
    def _parse_lhs(cls, lhs_str: str) -> tuple[dict[str, Fraction], Fraction, str | None]:
        coeffs: dict[str, Fraction] = {}
        constant_sum = Fraction(0)
        cleaned_str = lhs_str.replace(" ", "")
        
        matches = list(cls.TERM_REGEX.finditer(lhs_str))
        
        # Verificar sintaxis inválida (multiplicaciones *, potencias ^, etc.)
        reconstructed = "".join(m.group(0).replace(" ", "") for m in matches)
        if len(reconstructed) != len(cleaned_str):
            return {}, Fraction(0), f"Contiene operadores o sintaxis no válida en '{lhs_str}'."

        for match in matches:
            sign_str, coeff_str, var_name, const_str = match.groups()
            # int * Fraction devuelve Fraction: no se contamina con float.
            sign = -1 if sign_str == '-' else 1

            if var_name:
                if not coeff_str:
                    val = Fraction(1)
                else:
                    success, parsed_val, _ = MatrixValidator.parse_number_exact(coeff_str)
                    if not success:
                        return {}, Fraction(0), f"Coeficiente inválido '{coeff_str}' en la variable '{var_name}'."
                    val = parsed_val

                final_coeff = sign * val
                coeffs[var_name] = coeffs.get(var_name, Fraction(0)) + final_coeff

            elif const_str:
                # Término puramente numérico (constante) en el lado izquierdo.
                success, parsed_val, _ = MatrixValidator.parse_number_exact(const_str)
                if not success:
                    return {}, Fraction(0), f"Término independiente inválido '{const_str}' en '{lhs_str}'."
                constant_sum += sign * parsed_val

        if not coeffs:
            return {}, Fraction(0), f"No se encontraron variables válidas en '{lhs_str}'."

        return coeffs, constant_sum, None