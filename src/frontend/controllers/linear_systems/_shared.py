"""Utilidades compartidas entre los controllers de sistemas lineales.

Centraliza el parseo del payload JSON, la validación de forma y la
construcción de la matriz aumentada [A | b] a partir de celdas crudas.

Antes de esta extracción, `controller_gauss.py` y
`controller_gauss_jordan.py` duplicaban ~80 líneas idénticas de
validación y conversión a Fraction. Unificar aquí garantiza que
cualquier corrección de validación se aplique a ambos métodos por igual.

Este módulo NO conoce al solver ni al formato de respuesta: solo se
encarga de producir una `Matrix` aumentada y las listas de Fraction
que el controller usará para verificar la solución.
"""
import json
from fractions import Fraction

from src.backend.exceptions import MatrixDataError
from src.backend.models.matrix import Matrix
from src.backend.utils.validators import MatrixValidator


def parse_payload(json_payload: str) -> tuple[dict | None, str | None]:
    """Parsea y valida la forma básica del payload JSON.

    Args:
        json_payload: string JSON crudo con 'matrix_A' y 'vector_b'.

    Returns:
        (data, None) si el JSON es válido y es un dict.
        (None, error_json) si falla. El caller debe devolver error_json
        tal cual al frontend.
    """
    try:
        data = json.loads(json_payload)
    except json.JSONDecodeError as e:
        return None, json.dumps({
            "status": "error",
            "message": f"Payload JSON malformado: {e.msg} (línea {e.lineno}, columna {e.colno})."
        })
    if not isinstance(data, dict):
        return None, json.dumps({
            "status": "error",
            "message": "El payload debe ser un objeto JSON con 'matrix_A' y 'vector_b'."
        })
    return data, None


def validate_and_build_augmented(
    data: dict,
) -> tuple[
    Matrix | None,
    list[list[Fraction]] | None,
    list[Fraction] | None,
    int,
    int,
    str | None,
]:
    """Valida el payload y construye la matriz aumentada [A | b].

    Reglas aplicadas (idénticas para Gauss y Gauss-Jordan):
      1. A no puede estar vacía ni tener 0 columnas.
      2. A debe ser lista de filas con shape consistente.
      3. len(b) debe coincidir EXACTAMENTE con len(A). No se rellena con 0:
         hacerlo produciría la solución de un sistema distinto al ingresado.
      4. Cada celda se parsea con `parse_number_exact` (Fraction exacto).
         Los errores reportan coordenada [i,j] para A y [i] para b.

    Args:
        data: dict ya validado por `parse_payload`.

    Returns:
        (matrix, A_fractions, b_fractions, m, n, None) si OK.
        (None, None, None, 0, 0, error_json) si falla.
    """
    matrix_A_raw = data.get("matrix_A", [])
    vector_b_raw = data.get("vector_b", [])

    # --- 1. Validación de forma ---
    m = len(matrix_A_raw)
    if m == 0:
        return None, None, None, 0, 0, json.dumps({
            "status": "error",
            "message": "La matriz A está vacía."
        })

    if not isinstance(matrix_A_raw[0], list):
        return None, None, None, 0, 0, json.dumps({
            "status": "error",
            "message": "La matriz A debe ser una lista de filas."
        })

    n = len(matrix_A_raw[0])
    if n == 0:
        return None, None, None, 0, 0, json.dumps({
            "status": "error",
            "message": "La matriz A no puede tener 0 columnas."
        })

    valid_shape, msg_shape = MatrixValidator.validate_matrix_data(matrix_A_raw, m, n)
    if not valid_shape:
        return None, None, None, 0, 0, json.dumps({
            "status": "error",
            "message": msg_shape
        })

    if len(vector_b_raw) != m:
        return None, None, None, 0, 0, json.dumps({
            "status": "error",
            "message": (
                f"El vector b tiene {len(vector_b_raw)} valores; "
                f"se esperaban {m} (uno por fila de A)."
            )
        })

    # --- 2. Conversión a Fraction con coordenadas en errores ---
    A_fractions: list[list[Fraction]] = []
    for i, row in enumerate(matrix_A_raw):
        fila_frac: list[Fraction] = []
        for j, cell in enumerate(row):
            raw = str(cell).strip() if cell is not None and str(cell).strip() else '0'
            ok, val, err = MatrixValidator.parse_number_exact(raw)
            if not ok:
                return None, None, None, 0, 0, json.dumps({
                    "status": "error",
                    "message": f"Error en A[{i+1},{j+1}]: {err}"
                })
            fila_frac.append(val)
        A_fractions.append(fila_frac)

    b_fractions: list[Fraction] = []
    for i, cell in enumerate(vector_b_raw):
        raw = str(cell).strip() if cell is not None and str(cell).strip() else '0'
        ok, val, err = MatrixValidator.parse_number_exact(raw)
        if not ok:
            return None, None, None, 0, 0, json.dumps({
                "status": "error",
                "message": f"Error en b[{i+1}]: {err}"
            })
        b_fractions.append(val)

    # --- 3. Construcción de la matriz aumentada [A | b] ---
    try:
        augmented_data = [A_fractions[i] + [b_fractions[i]] for i in range(m)]
        matrix = Matrix(m, n + 1, augmented_data)
    except MatrixDataError as e:
        return None, None, None, 0, 0, json.dumps({
            "status": "error",
            "message": f"Datos inválidos: {e}"
        })

    return matrix, A_fractions, b_fractions, m, n, None