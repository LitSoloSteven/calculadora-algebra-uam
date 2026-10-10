import json
import logging
from src.backend.exceptions import AlgebraLinealError
from src.backend.models.matrix import Matrix
from src.backend.solvers.vector_ops.operations import VectorOpsSolver
from src.backend.solvers.vector_ops.linear_combination import LinearCombinationSolver
from src.backend.utils.validators import MatrixValidator
from src.frontend.controllers.vector_ops._shared import parse_payload

logger = logging.getLogger(__name__)

def construir_vector_desde_dict(vec_dict: dict) -> Matrix:
    orientacion = vec_dict.get("orientation", "column")
    datos_crudos = vec_dict.get("data", [])
    
    valores_parseados = []
    for val_str in datos_crudos:
        exito, val, err = MatrixValidator.parsear_numero_exacto(str(val_str))
        if not exito:
            raise ValueError(f"Valor inválido: {val_str}. {err}")
        valores_parseados.append(val)
        
    if orientacion == 'column':
        return Matrix(len(valores_parseados), 1, [[v] for v in valores_parseados])
    else:
        return Matrix(1, len(valores_parseados), [valores_parseados])

build_vector_from_dict = construir_vector_desde_dict


class VectorOpsController:
    @staticmethod
    def procesar_suma_resta(payload_str: str) -> str:
        from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixEncoder
        data, err = parse_payload(payload_str)
        if err: return err
        
        try:
            op = data.get("operation")
            v1 = construir_vector_desde_dict(data.get("v1", {}))
            v2 = construir_vector_desde_dict(data.get("v2", {}))
            strict = data.get("strict", False)
            
            solver = VectorOpsSolver()
            if op == "add":
                res = solver.sumar(v1, v2, name1="v_1", name2="v_2", strict=strict)
            else:
                res = solver.restar(v1, v2, name1="v_1", name2="v_2", strict=strict)
                
            for step in res.get("steps", []):
                step.pop("matrix", None)
            res.pop("result_matrix", None)
                
            return json.dumps(res, cls=MatrixEncoder)
        except (AlgebraLinealError, ValueError) as e:
            return json.dumps({"status": "ERROR", "message": str(e)})
        except Exception:
            logger.exception("Error inesperado en process_add_subtract")
            return json.dumps({"status": "ERROR", "message": "Ocurrió un error inesperado al procesar la operación. Inténtalo de nuevo."})

    process_add_subtract = procesar_suma_resta

    @staticmethod
    def procesar_multiplicacion_escalar(payload_str: str) -> str:
        from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixEncoder
        data, err = parse_payload(payload_str)
        if err: return err
        
        try:
            scalar_str = str(data.get("scalar", "0"))
            exito, k, msg = MatrixValidator.parsear_numero_exacto(scalar_str)
            if not exito:
                return json.dumps({"status": "ERROR", "message": f"Escalar inválido: {msg}"})
                
            v = construir_vector_desde_dict(data.get("v", {}))
            
            solver = VectorOpsSolver()
            res = solver.multiplicar_escalar(k, v, name="v", result_name="w")
            
            for step in res.get("steps", []):
                step.pop("matrix", None)
            res.pop("result_matrix", None)
            
            return json.dumps(res, cls=MatrixEncoder)
        except (AlgebraLinealError, ValueError) as e:
            return json.dumps({"status": "ERROR", "message": str(e)})
        except Exception:
            logger.exception("Error inesperado en process_scalar_multiply")
            return json.dumps({"status": "ERROR", "message": "Ocurrió un error inesperado al procesar la multiplicación por escalar. Inténtalo de nuevo."})

    process_scalar_multiply = procesar_multiplicacion_escalar

    @staticmethod
    def procesar_combinacion_lineal(payload_str: str) -> str:
        from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixEncoder
        data, err = parse_payload(payload_str)
        if err: return err
        
        try:
            b_data = data.get("b", {})
            b = construir_vector_desde_dict(b_data)
            
            vectors_raw = data.get("vectors", [])
            vectors = []
            for v_data in vectors_raw:
                vectors.append(construir_vector_desde_dict(v_data))
            
            solver = LinearCombinationSolver()
            res = solver.resolver(b, vectors)
            
            # Formatear matrices y construir steps_meta sobre gauss_steps
            from src.backend.solvers.matrix_ops.formatters import matrix_to_latex
            from src.frontend.controllers.linear_systems._shared import build_steps_meta

            setup_steps = res.get("setup_steps", [])
            gauss_steps = res.get("gauss_steps", [])
            initial_mat = setup_steps[-1].get("matrix") if setup_steps else None

            if gauss_steps:
                res["steps_meta"] = build_steps_meta(gauss_steps, initial=initial_mat)
            elif "steps" in res:
                res["steps_meta"] = build_steps_meta(res["steps"])

            for s_list in (setup_steps, gauss_steps, res.get("steps", [])):
                for step in s_list:
                    if step.get("matrix") is not None:
                        if not step.get("detail_latex"):
                            step["detail_latex"] = matrix_to_latex(step["matrix"])
                        step.pop("matrix", None)
            
            return json.dumps(res, cls=MatrixEncoder)
        except (AlgebraLinealError, ValueError) as e:
            return json.dumps({"status": "ERROR", "message": str(e)})
        except Exception:
            logger.exception("Error inesperado en process_linear_combination")
            return json.dumps({"status": "ERROR", "message": "Ocurrió un error inesperado al resolver la combinación lineal. Inténtalo de nuevo."})

    process_linear_combination = procesar_combinacion_lineal

