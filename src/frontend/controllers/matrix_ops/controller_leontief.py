"""Controlador del Modelo de Leontief para la capa Frontend.

Recibe el payload JSON del UI, construye las estructuras del backend,
invoca LeontiefSolver y devuelve un JSON listo para renderizar.

Payload esperado (JSON string):
{
    "C": [[...], ...],          // Matriz de coeficientes técnicos n×n
    "d": [...],                  // Vector de demanda final (longitud n)
    "sectores": [...]            // Opcional: nombres de sectores
}
"""
import json
import logging
from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.leontief import LeontiefSolver
from src.backend.utils.validators import MatrixValidator

logger = logging.getLogger(__name__)


class LeontiefController:

    @staticmethod
    def procesar(json_payload: str) -> str:
        """Punto de entrada principal: recibe JSON, devuelve JSON.

        Returns:
            JSON string con el resultado del modelo de Leontief.
        """
        try:
            data = json.loads(json_payload)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "ERROR",
                "message": f"Payload JSON inválido: {e}",
            })

        # ── 1. Validar y construir C ──────────────────────────────────
        C_raw = data.get("C")
        if not C_raw or not isinstance(C_raw, list):
            return json.dumps({"status": "ERROR", "message": "Falta la matriz C."})

        try:
            n = len(C_raw)
            datos_C = []
            for i, fila in enumerate(C_raw):
                if len(fila) != n:
                    raise ValueError(
                        f"Fila {i+1} de C tiene {len(fila)} columnas; se esperaban {n}."
                    )
                fila_parseada = []
                for j, raw in enumerate(fila):
                    ok, val, err = MatrixValidator.parse_number_exact(
                        str(raw).strip() if raw is not None else "0"
                    )
                    if not ok:
                        raise ValueError(f"C[{i+1},{j+1}]: {err}")
                    fila_parseada.append(val)
                datos_C.append(fila_parseada)
            matriz_C = Matrix(n, n, datos_C)
        except (ValueError, Exception) as e:
            return json.dumps({"status": "ERROR", "message": str(e)})

        # ── 2. Validar y construir d ──────────────────────────────────
        d_raw = data.get("d")
        if not d_raw or not isinstance(d_raw, list):
            return json.dumps({"status": "ERROR", "message": "Falta el vector d."})

        try:
            vector_d = []
            for i, raw in enumerate(d_raw):
                ok, val, err = MatrixValidator.parse_number_exact(
                    str(raw).strip() if raw is not None else "0"
                )
                if not ok:
                    raise ValueError(f"d[{i+1}]: {err}")
                vector_d.append(val)
        except (ValueError, Exception) as e:
            return json.dumps({"status": "ERROR", "message": str(e)})

        sectores = data.get("sectores") or None

        # ── 3. Ejecutar solver ────────────────────────────────────────
        solver = LeontiefSolver()
        resultado = solver.resolver(matriz_C, vector_d, sectores)

        return json.dumps(resultado, ensure_ascii=False, default=str)

    # Alias canónico en castellano
    process = procesar
