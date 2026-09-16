import re
from typing import Dict, List, Tuple, Union
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver
from src.backend.utils.formatters import (
    matrix_to_latex,
    sum_sub_matrix_to_latex,
    multiply_matrix_to_latex
)

class MatrixExpressionEvaluator:
    """
    Evalúa expresiones algebraicas complejas de matrices (ej. '2A - B(C - D^T)')
    descomponiéndolas en suboperaciones paso a paso.
    """

    def __init__(self):
        self.ops_solver = MatrixOpsSolver()
        self.global_steps = []

    def _tokenize(self, expr: str) -> List[str]:
        """Convierte la cadena en tokens y agrega multiplicaciones implícitas."""
        expr = expr.replace(" ", "")
        # Normalizar notación de transpuesta a un símbolo único ᵀ
        expr = expr.replace("^T", "ᵀ").replace("^t", "ᵀ")
        
        # Captura: 1) Números, 2) Variables alfanuméricas, 3) ᵀ, 4) Operadores
        token_pattern = re.compile(r'\d+\.\d+|\d+|[A-Za-z][A-Za-z0-9_]*|ᵀ|[\+\-\*\(\)]')
        raw_tokens = token_pattern.findall(expr)
        
        tokens = []
        for i, token in enumerate(raw_tokens):
            # Hack para el menos unario: convierte '-A' en '0 - A'
            if token == '-' and (i == 0 or raw_tokens[i-1] == '('):
                tokens.append('0')
                
            tokens.append(token)
            
            # Inserción de multiplicación implícita (ej. 2A -> 2 * A, A(B) -> A * (B))
            if i < len(raw_tokens) - 1:
                next_token = raw_tokens[i+1]
                is_current_operand = re.match(r'^[A-Za-z]|\d|\)|ᵀ', token)
                is_next_operand = re.match(r'^[A-Za-z]|\d|\(', next_token)
                
                if is_current_operand and is_next_operand:
                    tokens.append('*')
                    
        return tokens

    def _to_rpn(self, tokens: List[str]) -> List[str]:
        """Algoritmo Shunting-Yard para Notación Polaca Inversa."""
        precedence = {'+': 1, '-': 1, '*': 2, 'ᵀ': 3}
        output = []
        stack = []

        for token in tokens:
            if re.match(r'^[A-Za-z][A-Za-z0-9_]*$|^\d+(\.\d+)?$', token):
                output.append(token)
            elif token == '(':
                stack.append(token)
            elif token == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if not stack:
                    raise ValueError("Error de sintaxis: Paréntesis desbalanceados.")
                stack.pop()
            elif token in precedence:
                while (stack and stack[-1] != '(' and 
                       precedence.get(stack[-1], 0) >= precedence[token]):
                    output.append(stack.pop())
                stack.append(token)

        while stack:
            top = stack.pop()
            if top in '()':
                raise ValueError("Error de sintaxis: Paréntesis desbalanceados.")
            output.append(top)

        return output

    def _scalar_multiply(self, scalar: float, matrix: Matrix) -> Matrix:
        """Multiplicación manual de un escalar por una matriz."""
        new_data = [[val * scalar for val in row] for row in matrix.data]
        return Matrix(matrix.rows, matrix.cols, new_data)

    def _transpose(self, matrix: Matrix) -> Matrix:
        """Transposición manual de la matriz."""
        new_data = [[matrix.data[j][i] for j in range(matrix.rows)] for i in range(matrix.cols)]
        return Matrix(matrix.cols, matrix.rows, new_data)

    def evaluate(self, expression: str, matrices_dict: Dict[str, Matrix]) -> dict:
        self.global_steps = []
        try:
            tokens = self._tokenize(expression)
            rpn_tokens = self._to_rpn(tokens)
        except ValueError as e:
            return {"status": "ERROR", "message": str(e), "result_matrix": None, "segment_steps": []}

        stack = []
        temp_counter = 1

        for token in rpn_tokens:
            if re.match(r'^\d+(\.\d+)?$', token):
                stack.append((token, float(token)))
                
            elif re.match(r'^[A-Za-z][A-Za-z0-9_]*$', token):
                if token not in matrices_dict:
                    return {"status": "ERROR", "message": f"La matriz '{token}' no ha sido definida.", "result_matrix": None, "segment_steps": []}
                stack.append((token, matrices_dict[token]))
                
            elif token == 'ᵀ':
                if not stack:
                    return {"status": "ERROR", "message": "Operación de transpuesta sin operando.", "result_matrix": None, "segment_steps": []}
                name, val = stack.pop()
                
                if isinstance(val, float):
                    stack.append((f"{name}ᵀ", val))
                    continue
                    
                temp_name = f"T_{temp_counter}"
                temp_counter += 1
                res_mat = self._transpose(val)
                
                self.global_steps.append({
                    "temp_variable": temp_name,
                    "operation_display": f"{temp_name} = {name}^T",
                    "operation_type": "Transposición",
                    "operand_a_name": name,
                    "operand_b_name": None,
                    "symbolic_matrix_latex": f"{name}^T",
                    "result_matrix_latex": matrix_to_latex(res_mat),
                    "result_matrix": res_mat,
                    "cell_by_cell_steps": [] 
                })
                stack.append((temp_name, res_mat))
                
            elif token in ('+', '-', '*'):
                if len(stack) < 2:
                    return {"status": "ERROR", "message": "Expresión matemática mal formada.", "result_matrix": None, "segment_steps": []}

                right_name, right_val = stack.pop()
                left_name, left_val = stack.pop()
                temp_name = f"T_{temp_counter}"
                temp_counter += 1
                
                cell_steps = []
                
                if token == '*':
                    if isinstance(left_val, float) and isinstance(right_val, Matrix):
                        res_mat = self._scalar_multiply(left_val, right_val)
                        symbolic_latex = f"{left_name} \\cdot {right_name}"
                        op_word = "Multiplicación Escalar"
                    elif isinstance(right_val, float) and isinstance(left_val, Matrix):
                        res_mat = self._scalar_multiply(right_val, left_val)
                        symbolic_latex = f"{left_name} \\cdot {right_name}"
                        op_word = "Multiplicación Escalar"
                    elif isinstance(left_val, float) and isinstance(right_val, float):
                        # Escalar * Escalar
                        res_val = left_val * right_val
                        stack.append((f"{res_val}", res_val))
                        temp_counter -= 1
                        continue
                    else:
                        # Matriz * Matriz
                        res = self.ops_solver.multiply(left_val, right_val)
                        if res["status"] == "ERROR":
                            return {"status": "ERROR", "message": f"Error ({left_name} * {right_name}): {res['message']}", "result_matrix": None, "segment_steps": []}
                        res_mat = res["result_matrix"]
                        cell_steps = res["steps"]
                        symbolic_latex = multiply_matrix_to_latex(left_val, right_val)
                        op_word = "Multiplicación de Matrices"
                        
                elif token == '+':
                    if isinstance(left_val, float) or isinstance(right_val, float):
                        return {"status": "ERROR", "message": "No se puede sumar un escalar y una matriz.", "result_matrix": None, "segment_steps": []}
                    res = self.ops_solver.add(left_val, right_val)
                    if res["status"] == "ERROR":
                        return {"status": "ERROR", "message": f"Error ({left_name} + {right_name}): {res['message']}", "result_matrix": None, "segment_steps": []}
                    res_mat = res["result_matrix"]
                    cell_steps = res["steps"]
                    symbolic_latex = sum_sub_matrix_to_latex(left_val, right_val, "+")
                    op_word = "Suma"
                    
                elif token == '-':
                    if isinstance(left_val, float) or isinstance(right_val, float):
                        return {"status": "ERROR", "message": "No se puede restar un escalar y una matriz.", "result_matrix": None, "segment_steps": []}
                    res = self.ops_solver.subtract(left_val, right_val)
                    if res["status"] == "ERROR":
                        return {"status": "ERROR", "message": f"Error ({left_name} - {right_name}): {res['message']}", "result_matrix": None, "segment_steps": []}
                    res_mat = res["result_matrix"]
                    cell_steps = res["steps"]
                    symbolic_latex = sum_sub_matrix_to_latex(left_val, right_val, "-")
                    op_word = "Resta"

                self.global_steps.append({
                    "temp_variable": temp_name,
                    "operation_display": f"{temp_name} = {left_name} {token} {right_name}",
                    "operation_type": op_word,
                    "operand_a_name": left_name,
                    "operand_b_name": right_name,
                    "symbolic_matrix_latex": symbolic_latex,
                    "result_matrix_latex": matrix_to_latex(res_mat),
                    "result_matrix": res_mat,
                    "cell_by_cell_steps": cell_steps
                })
                stack.append((temp_name, res_mat))

        if len(stack) != 1:
            return {"status": "ERROR", "message": "La expresión no pudo ser evaluada completamente.", "result_matrix": None, "segment_steps": []}

        final_name, final_val = stack.pop()
        
        if isinstance(final_val, float):
            return {"status": "ERROR", "message": "El resultado final es un escalar, no una matriz.", "result_matrix": None, "segment_steps": []}

        return {
            "status": "SUCCESS",
            "message": f"Expresión '{expression}' resuelta con éxito.",
            "final_variable": final_name,
            "result_matrix": final_val,
            "result_matrix_latex": matrix_to_latex(final_val),
            "segment_steps": self.global_steps
        }