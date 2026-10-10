"""Controlador de Transformaciones Lineales para la capa Frontend.

Recibe el payload JSON del UI, construye la matriz A, invoca
LinearTransformationSolver y devuelve un JSON listo para renderizar.

Payload esperado (JSON string):
{
    "A": [[...], ...],          // Matriz representante de T (m×n)
    "variables": [...]          // Opcional: nombres de las variables
}
"""
import json
import logging

from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.transformations import LinearTransformationSolver
from src.backend.utils.validators import MatrixValidator

logger = logging.getLogger(__name__)


class TransformacionesController:

    @staticmethod
    def procesar(json_payload: str) -> str:
        """Punto de entrada principal: recibe JSON, devuelve JSON.

        Returns:
            JSON string con el análisis completo de la transformación lineal.
        """
        try:
            data = json.loads(json_payload)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "ERROR",
                "message": f"Payload JSON inválido: {e}",
            })

        # ── 1. Validar y construir A ──────────────────────────────────
        A_raw = data.get("A")
        if not A_raw or not isinstance(A_raw, list):
            return json.dumps({"status": "ERROR", "message": "Falta la matriz A."})

        try:
            m = len(A_raw)
            if m == 0:
                raise ValueError("La matriz A no puede estar vacía.")
            n = len(A_raw[0])
            datos_A = []
            for i, fila in enumerate(A_raw):
                if len(fila) != n:
                    raise ValueError(
                        f"Fila {i+1} de A tiene {len(fila)} columnas; se esperaban {n}."
                    )
                fila_parseada = []
                for j, raw in enumerate(fila):
                    ok, val, err = MatrixValidator.parse_number_exact(
                        str(raw).strip() if raw is not None else "0"
                    )
                    if not ok:
                        raise ValueError(f"A[{i+1},{j+1}]: {err}")
                    fila_parseada.append(val)
                datos_A.append(fila_parseada)
            matriz_A = Matrix(m, n, datos_A)
        except (ValueError, Exception) as e:
            return json.dumps({"status": "ERROR", "message": str(e)})

        variables = data.get("variables") or None

        # ── 2. Ejecutar solver ────────────────────────────────────────
        solver = LinearTransformationSolver()
        resultado = solver.resolver(matriz_A, variables)

        return json.dumps(resultado, ensure_ascii=False, default=str)

    # Alias canónico en inglés
    process = procesar
