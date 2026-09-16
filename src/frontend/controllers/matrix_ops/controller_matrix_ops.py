import json
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator


# 1. Creamos un codificador JSON para enseñar a Python cómo serializar la clase Matrix
class MatrixEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Matrix):
            return {"rows": obj.rows, "cols": obj.cols, "data": obj.data}
        if isinstance(obj, Fraction):
            return float(obj) if obj.denominator != 1 else obj.numerator
        return super().default(obj)

class MatrixOpsController:
    @staticmethod
    def process_expression(expresion_str: str, matrices_dict_json: str) -> str:
        try:
            matrices_data = json.loads(matrices_dict_json)
            
            # Instanciar las matrices recibidas desde la UI
            matrices = {}
            for name, mat_data in matrices_data.items():
                matrices[name] = Matrix(
                    rows=mat_data["rows"],
                    cols=mat_data["cols"],
                    data=mat_data["data"]
                )
                
            # 2. INSTANCIAR el evaluador antes de usarlo
            evaluator = MatrixExpressionEvaluator()
            resultado = evaluator.evaluate(expresion_str, matrices)
            
            # 3. Empaquetar usando nuestro codificador personalizado (cls=MatrixEncoder)
            return json.dumps(resultado, ensure_ascii=False, cls=MatrixEncoder)
            
        except Exception as e:
            return json.dumps({
                "status": "ERROR",
                "message": f"Error interno en el controlador: {str(e)}"
            }, ensure_ascii=False)