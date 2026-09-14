import re
from typing import Dict, List, Tuple
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver
from src.backend.utils.formatters import (
    matrix_to_latex,
    sum_sub_matrix_to_latex,
    multiply_matrix_to_latex
)

class MatrixExpressionEvaluator:
    """
    Evalúa expresiones algebraicas complejas de matrices como 'A - B(C - D)'
    descomponiéndolas en suboperaciones paso a paso (T1, T2, ...).
    """

    def __init__(self):
        self.ops_solver = MatrixOpsSolver()
        self.global_steps = []

    def _preprocess_expression(self, expr: str) -> str:
        """
        Limpia espacios y añade el operador '*' explícito donde hay multiplicación implícita.
        Ejemplos: 'B(C-D)' -> 'B*(C-D)', '(A+B)C' -> '(A+B)*C', 'A B' -> 'A*B'
        """
        expr = expr.replace(" ", "")
        # Letra seguida de parentesis de apertura: B( -> B*(
        expr = re.sub(r'([A-Za-z0-9])\(', r'\1*(', expr)
        # Parentesis de cierre seguido de letra: )C -> )*C
        expr = re.sub(r'\)([A-Za-z0-9])', r')*\1', expr)
        # Parentesis de cierre seguido de parentesis de apertura: )( -> )*(
        expr = re.sub(r'\)\(', r')*(', expr)
        # Letra seguida de letra (ej. AB -> A*B)
        expr = re.sub(r'([A-Za-z])([A-Za-z])', r'\1*\2', expr)
        return expr

    def _tokenize(self, expr: str) -> List[str]:
        """Convierte la cadena de expresión en una lista de tokens."""
        token_pattern = re.compile(r'[A-Za-z]+|[\+\-\*\(\)]')
        return token_pattern.findall(expr)

    def _to_rpn(self, tokens: List[str]) -> List[str]:
        """
        Algoritmo Shunting-Yard para convertir infijo a Notación Polaca Inversa (RPN).
        Precedencia: * (multiplicación) > +, - (suma/resta).
        """
        precedence = {'+': 1, '-': 1, '*': 2}
        output = []
        stack = []

        for token in tokens:
            if token.isalpha():
                output.append(token)
            elif token == '(':
                stack.append(token)
            elif token == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if not stack:
                    raise ValueError("Error de sintaxis: Paréntesis desbalanceados.")
                stack.pop()  # Eliminar '('
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

    def evaluate(self, expression: str, matrices_dict: Dict[str, Matrix]) -> dict:
        """
        Evalúa la expresión algebraica e incrementa el historial de pasos por cada segmento.
        """
        self.global_steps = []
        try:
            clean_expr = self._preprocess_expression(expression)
            tokens = self._tokenize(clean_expr)
            rpn_tokens = self._to_rpn(tokens)
        except ValueError as e:
            return {
                "status": "ERROR",
                "message": str(e),
                "result_matrix": None,
                "segment_steps": []
            }

        stack: List[Tuple[str, Matrix]] = []  # Tupla: (Nombre_Variable, Objeto_Matrix)
        temp_counter = 1

        for token in rpn_tokens:
            if token.isalpha():
                if token not in matrices_dict:
                    return {
                        "status": "ERROR",
                        "message": f"La matriz '{token}' no ha sido definida por el usuario.",
                        "result_matrix": None,
                        "segment_steps": []
                    }
                stack.append((token, matrices_dict[token]))
            elif token in ('+', '-', '*'):
                if len(stack) < 2:
                    return {
                        "status": "ERROR",
                        "message": "Expresión matemática mal formada.",
                        "result_matrix": None,
                        "segment_steps": []
                    }

                right_name, right_mat = stack.pop()
                left_name, left_mat = stack.pop()
                temp_name = f"T_{temp_counter}"
                temp_counter += 1

                # Ejecutar la operación de segmento según el operador
                if token == '+':
                    res = self.ops_solver.add(left_mat, right_mat)
                    symbolic_latex = sum_sub_matrix_to_latex(left_mat, right_mat, "+")
                    op_word = "Suma"
                elif token == '-':
                    res = self.ops_solver.subtract(left_mat, right_mat)
                    symbolic_latex = sum_sub_matrix_to_latex(left_mat, right_mat, "-")
                    op_word = "Resta"
                elif token == '*':
                    res = self.ops_solver.multiply(left_mat, right_mat)
                    symbolic_latex = multiply_matrix_to_latex(left_mat, right_mat)
                    op_word = "Multiplicación"

                if res["status"] == "ERROR":
                    return {
                        "status": "ERROR",
                        "message": f"Error en segmento {temp_name} ({left_name} {token} {right_name}): {res['message']}",
                        "result_matrix": None,
                        "segment_steps": self.global_steps
                    }

                res_mat = res["result_matrix"]
                
                # Guardar el registro detallado del segmento
                segment_info = {
                    "temp_variable": temp_name,
                    "operation_display": f"{temp_name} = {left_name} {token} {right_name}",
                    "operation_type": op_word,
                    "operand_a_name": left_name,
                    "operand_b_name": right_name,
                    "symbolic_matrix_latex": symbolic_latex,
                    "result_matrix_latex": matrix_to_latex(res_mat),
                    "result_matrix": res_mat,
                    "cell_by_cell_steps": res["steps"]
                }
                self.global_steps.append(segment_info)

                # Apilar la matriz temporal resultante para el siguiente nivel de evaluación
                stack.append((temp_name, res_mat))

        if len(stack) != 1:
            return {
                "status": "ERROR",
                "message": "La expresión no pudo ser evaluada completamente.",
                "result_matrix": None,
                "segment_steps": []
            }

        final_name, final_matrix = stack.pop()

        return {
            "status": "SUCCESS",
            "message": f"Expresión '{expression}' resuelta con éxito.",
            "final_variable": final_name,
            "result_matrix": final_matrix,
            "result_matrix_latex": matrix_to_latex(final_matrix),
            "segment_steps": self.global_steps
        }