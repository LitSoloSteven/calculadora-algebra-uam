import json
import logging
from src.backend.exceptions import AlgebraLinealError
from src.backend.models.matrix import Matrix
from src.backend.solvers.vector_ops.operations import VectorOpsSolver
from src.backend.solvers.vector_ops.linear_combination import LinearCombinationSolver
from src.backend.utils.validators import MatrixValidator
from src.frontend.controllers.vector_ops._shared import parse_payload

logger = logging.getLogger(__name__)

def build_vector_from_dict(vec_dict: dict) -> Matrix:
    orientation = vec_dict.get("orientation", "column")
    raw_data = vec_dict.get("data", [])
    
    parsed_vals = []
    for val_str in raw_data:
        success, val, err = MatrixValidator.parse_number_exact(str(val_str))
        if not success:
            raise ValueError(f"Valor inválido: {val_str}. {err}")
        parsed_vals.append(val)
        
    if orientation == 'column':
        return Matrix(len(parsed_vals), 1, [[v] for v in parsed_vals])
    else:
        return Matrix(1, len(parsed_vals), [parsed_vals])

class VectorOpsController:
    @staticmethod
    def process_add_subtract(payload_str: str) -> str:
        from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixEncoder
        data, err = parse_payload(payload_str)
        if err: return err
        
        try:
            op = data.get("operation")
            v1 = build_vector_from_dict(data.get("v1", {}))
            v2 = build_vector_from_dict(data.get("v2", {}))
            strict = data.get("strict", False)
            
            solver = VectorOpsSolver()
            if op == "add":
                res = solver.add(v1, v2, name1="v_1", name2="v_2", strict=strict)
            else:
                res = solver.subtract(v1, v2, name1="v_1", name2="v_2", strict=strict)
                
            for step in res.get("steps", []):
                step.pop("matrix", None)
            res.pop("result_matrix", None)
                
            return json.dumps(res, cls=MatrixEncoder)
        except (AlgebraLinealError, ValueError) as e:
            return json.dumps({"status": "ERROR", "message": str(e)})
        except Exception:
            logger.exception("Error inesperado en process_add_subtract")
            return json.dumps({"status": "ERROR", "message": "Ocurrió un error inesperado al procesar la operación. Inténtalo de nuevo."})

    @staticmethod
    def process_scalar_multiply(payload_str: str) -> str:
        from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixEncoder
        data, err = parse_payload(payload_str)
        if err: return err
        
        try:
            scalar_str = str(data.get("scalar", "0"))
            success, k, msg = MatrixValidator.parse_number_exact(scalar_str)
            if not success:
                return json.dumps({"status": "ERROR", "message": f"Escalar inválido: {msg}"})
                
            v = build_vector_from_dict(data.get("v", {}))
            
            solver = VectorOpsSolver()
            res = solver.scalar_multiply(k, v, name="v", result_name="w")
            
            for step in res.get("steps", []):
                step.pop("matrix", None)
            res.pop("result_matrix", None)
            
            return json.dumps(res, cls=MatrixEncoder)
        except (AlgebraLinealError, ValueError) as e:
            return json.dumps({"status": "ERROR", "message": str(e)})
        except Exception:
            logger.exception("Error inesperado en process_scalar_multiply")
            return json.dumps({"status": "ERROR", "message": "Ocurrió un error inesperado al procesar la multiplicación por escalar. Inténtalo de nuevo."})

    @classmethod
    def _enrich_linear_combination_response(cls, res: dict, vectors: list[Matrix]) -> None:
        from src.backend.solvers.matrix_ops.formatters import matrix_to_latex
        from src.frontend.controllers._agrupar_pasos import agrupar_pasos_eliminacion
        from src.frontend.controllers.linear_systems._shared import (
            build_steps_meta,
            serialize_matrix,
        )

        setup_steps = res.get("setup_steps", [])
        gauss_steps = res.get("gauss_steps", [])
        initial_mat = setup_steps[-1].get("matrix") if setup_steps else None

        if gauss_steps:
            res["steps_meta"] = build_steps_meta(gauss_steps, initial=initial_mat)
        elif "steps" in res:
            res["steps_meta"] = build_steps_meta(res["steps"])

        n_vars = len(vectors)
        variables = [f"c_{i+1}" for i in range(n_vars)]
        res["n_vars"] = n_vars
        res["variables"] = variables

        pasos_clasificados, groups, stats = agrupar_pasos_eliminacion(
            gauss_steps, n_vars, res.get("status"), contexto="sistema", metodo="gauss"
        )
        res["steps_view"] = [
            {
                "index": s["index"],
                "kind": s["kind"],
                "description": s["description"],
                "explanation": s["explanation"],
                "group_index": s["group_index"],
                "pivot": list(s["pivot"]) if s["pivot"] is not None else None,
                "rows_changed": list(s["rows_changed"]),
                "swap_rows": list(s["swap_rows"]) if s["swap_rows"] is not None else None,
                "matrix": serialize_matrix(s["matrix"]) if s.get("matrix") is not None else None,
            }
            for s in pasos_clasificados
        ]
        res["groups"] = groups
        res["stats"] = stats

        for s_list in (setup_steps, gauss_steps, res.get("steps", [])):
            for step in s_list:
                if step.get("matrix") is not None:
                    if not step.get("detail_latex"):
                        step["detail_latex"] = matrix_to_latex(step["matrix"])
                    step.pop("matrix", None)

    @classmethod
    def process_linear_combination(cls, payload_str: str) -> str:
        from src.frontend.controllers.matrix_ops.controller_matrix_ops import MatrixEncoder
        data, err = parse_payload(payload_str)
        if err: return err
        
        try:
            b_data = data.get("b", {})
            b = build_vector_from_dict(b_data)
            
            vectors_raw = data.get("vectors", [])
            vectors = [build_vector_from_dict(v_data) for v_data in vectors_raw]
            
            solver = LinearCombinationSolver()
            res = solver.solve(b, vectors)
            cls._enrich_linear_combination_response(res, vectors)
            
            return json.dumps(res, cls=MatrixEncoder)
        except (AlgebraLinealError, ValueError) as e:
            return json.dumps({"status": "ERROR", "message": str(e)})
        except Exception:
            logger.exception("Error inesperado en process_linear_combination")
            return json.dumps({"status": "ERROR", "message": "Ocurrió un error inesperado al resolver la combinación lineal. Inténtalo de nuevo."})

