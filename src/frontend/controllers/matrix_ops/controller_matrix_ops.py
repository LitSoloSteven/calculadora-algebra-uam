import json
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator

class MatrixOpsController:
    @staticmethod
    def process_expression(expresion_str: str, matrices_dict_json: str) -> str:
        try:
            matrices_data = json.loads(matrices_dict_json)
            
            # Instanciar las matrices
            matrices = {}
            for name, mat_data in matrices_data.items():
                matrices[name] = Matrix(
                    rows=mat_data["rows"],
                    cols=mat_data["cols"],
                    data=mat_data["data"]
                )
                
            # Llamar al evaluador
            resultado = MatrixExpressionEvaluator.evaluate(expresion_str, matrices)
            
            return json.dumps(resultado, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "status": "ERROR",
                "message": f"Error interno en el controlador: {str(e)}"
            }, ensure_ascii=False)
