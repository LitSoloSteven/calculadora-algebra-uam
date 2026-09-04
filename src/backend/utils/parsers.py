import re
from src.backend.models.matrix import Matrix
from src.backend.utils.validators import MatrixValidator

class SystemParser:
    # Captura: Grupo 1 = Signo (+/-), Grupo 2 = Magnitud (ej: 2, 3.5, 1/2), Grupo 3 = Variable (ej: x, y, z, x1)
    TERM_REGEX = re.compile(r'([+-]?)\s*([\d\.\/]*)\s*([a-zA-Z][a-zA-Z0-9_]*)')

    @classmethod
    def parse_system(cls, raw_text: str, strict_variables: bool = True) -> tuple[bool, Matrix | None, list[str], str]:
        """
        Procesa un string multilínea de ecuaciones y genera la matriz aumentada [A|b].
        
        Retorna:
            (éxito, objeto Matrix | None, lista_de_variables, mensaje_error)
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

            # 1. Validar el término independiente (Lado derecho / RHS)
            success_rhs, rhs_val, err_rhs = MatrixValidator.parse_number(rhs_str)
            if not success_rhs:
                return False, None, [], f"Línea {line_idx}: Término independiente inválido '{rhs_str}': {err_rhs}"

            # 2. Parsear y validar los términos del lado izquierdo (LHS)
            eq_coeffs, err_lhs = cls._parse_lhs(lhs_str)
            if err_lhs:
                return False, None, [], f"Línea {line_idx}: {err_lhs}"

            parsed_equations.append((eq_coeffs, rhs_val))
            all_variables.update(eq_coeffs.keys())

        if not all_variables:
            return False, None, [], "No se detectaron variables válidas en el sistema."

        # Ordenar las variables alfabéticamente/canónicamente (ej. ['x', 'y', 'z'])
        sorted_vars = sorted(list(all_variables))

        # 3. Validación de consistencia entre ecuaciones
        if strict_variables and len(lines) > 1:
            for idx, (eq_coeffs, _) in enumerate(parsed_equations, 1):
                eq_vars = set(eq_coeffs.keys())
                other_vars = set().union(*[e[0].keys() for i, e in enumerate(parsed_equations) if i != idx - 1])
                
                # Si una ecuación no comparte ninguna variable con el resto del sistema
                if not eq_vars.intersection(other_vars):
                    return False, None, [], (
                        f"Línea {idx}: Las variables {sorted(list(eq_vars))} "
                        f"no coinciden ni se relacionan con las demás ecuaciones del sistema."
                    )

        # 4. Construcción de la matriz aumentada [A|b]
        rows = len(parsed_equations)
        cols = len(sorted_vars) + 1  # Coeficientes + Término independiente
        matrix_data = []

        for eq_coeffs, rhs_val in parsed_equations:
            row = [eq_coeffs.get(var, 0.0) for var in sorted_vars]
            row.append(rhs_val)
            matrix_data.append(row)

        matrix = Matrix(rows, cols, matrix_data)
        return True, matrix, sorted_vars, "Sistema procesado correctamente."

    @classmethod
    def _parse_lhs(cls, lhs_str: str) -> tuple[dict[str, float], str | None]:
        coeffs = {}
        cleaned_str = lhs_str.replace(" ", "")
        
        matches = list(cls.TERM_REGEX.finditer(lhs_str))
        
        # Validar que no haya caracteres no permitidos (ej. multiplicación '*', potencias '^', etc.)
        reconstructed = "".join(m.group(0).replace(" ", "") for m in matches)
        if len(reconstructed) != len(cleaned_str):
            return {}, f"Contiene operadores o sintaxis no válida en '{lhs_str}'."

        for match in matches:
            sign_str, coeff_str, var_name = match.groups()
            if not var_name:
                continue

            sign = -1.0 if sign_str == '-' else 1.0

            if not coeff_str:
                val = 1.0
            else:
                success, parsed_val, _ = MatrixValidator.parse_number(coeff_str)
                if not success:
                    return {}, f"Coeficiente inválido '{coeff_str}' en variable '{var_name}'."
                val = parsed_val

            final_coeff = sign * val
            # Si una variable se repite en la misma línea (ej. x + 2x), se suman
            coeffs[var_name] = coeffs.get(var_name, 0.0) + final_coeff

        if not coeffs:
            return {}, f"No se encontraron variables válidas en '{lhs_str}'."

        return coeffs, None