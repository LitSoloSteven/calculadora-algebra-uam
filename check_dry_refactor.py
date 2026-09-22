"""Captura el comportamiento actual de GaussSolver y GaussJordanSolver.

Uso:
    py check_dry_refactor.py before   # guarda el baseline antes del refactor
    py check_dry_refactor.py after    # compara contra el baseline post-refactor

Ambos comandos deben correrse desde la raíz del proyecto. El output del
segundo debe ser idéntico al primero para dar por seguro el refactor.
"""
import json
import os
import sys
from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver


OUTPUT_DIR = "regression_output"


# Casos que cubren: solución única, infinitas, sin solución, fraccionarios,
# pivoteo, rectangular, y varios tamaños.
CASES = [
    (
        "clasico_3x3_unica",
        [
            [2, 1, -1, 8],
            [-3, -1, 2, -11],
            [-2, 1, 2, -3],
        ],
    ),
    (
        "2x2_unica",
        [
            [1, 2, 3],
            [3, 4, 7],
        ],
    ),
    (
        "infinitas_soluciones",
        [
            [1, 1, 1, 3],
            [2, 2, 2, 6],
        ],
    ),
    (
        "sin_solucion",
        [
            [1, 1, 3],
            [1, 1, 5],
        ],
    ),
    (
        "fraccionarios",
        [
            [Fraction(1, 2), Fraction(1, 3), Fraction(1)],
            [Fraction(2, 5), Fraction(3, 7), Fraction(2)],
        ],
    ),
    (
        "requiere_pivoteo",
        [
            [0, 1, 1, 2],
            [1, 0, 1, 3],
            [1, 1, 0, 3],
        ],
    ),
    (
        "4x4_unica",
        [
            [1, 1, 1, 1, 10],
            [2, 1, 0, 3, 12],
            [0, 2, 1, 1, 9],
            [1, 0, 0, 2, 7],
        ],
    ),
    (
        "rectangular_2x4",
        [
            [1, 2, 3, 4],
            [2, 4, 6, 8],
        ],
    ),
]


def _matrix_repr(matrix):
    return [
        [str(matrix.get(r, c)) for c in range(matrix.cols)]
        for r in range(matrix.rows)
    ]


def _serialize_result(result):
    return {
        "status": result.get("status"),
        "classification": result.get("classification"),
        "message": result.get("message"),
        "solution": result.get("solution"),
        "back_substitution_steps": result.get("back_substitution_steps"),
        "echelon_matrix": _matrix_repr(result["echelon_matrix"]) if result.get("echelon_matrix") else None,
        "steps": [
            {
                "description": step["description"],
                "matrix": _matrix_repr(step["matrix"]),
            }
            for step in result.get("steps", [])
        ],
    }


def run_all():
    output = {}
    for nombre, data in CASES:
        m = len(data)
        n = len(data[0])
        base_matrix = Matrix(m, n, [row[:] for row in data])

        gauss_result = GaussSolver(base_matrix.clone()).solve()
        gj_result = GaussJordanSolver(base_matrix.clone()).solve()

        output[nombre] = {
            "input": [[str(v) for v in row] for row in data],
            "gauss": _serialize_result(gauss_result),
            "gauss_jordan": _serialize_result(gj_result),
        }
    return output


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("before", "after"):
        print("Uso: py check_dry_refactor.py [before|after]")
        sys.exit(1)

    modo = sys.argv[1]
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output = run_all()
    filename = os.path.join(OUTPUT_DIR, f"dry_refactor_{modo}.json")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    total_steps = sum(
        len(c["gauss"]["steps"]) + len(c["gauss_jordan"]["steps"])
        for c in output.values()
    )
    print(f"[{modo}] Guardado {filename}")
    print(f"       {len(output)} casos, {total_steps} pasos totales")

    if modo == "after":
        before_path = os.path.join(OUTPUT_DIR, "dry_refactor_before.json")
        if not os.path.exists(before_path):
            print(f"\n✗ No existe {before_path}. Corré 'before' primero.")
            sys.exit(2)

        with open(before_path, encoding="utf-8") as f:
            before = json.load(f)

        if before == output:
            print("\n✓ Los resultados son IDÉNTICOS al baseline. Refactor seguro.")
        else:
            print("\n✗ DIFERENCIAS DETECTADAS:")
            for nombre in output:
                if before.get(nombre) != output[nombre]:
                    print(f"   - Caso con diferencias: {nombre}")
            sys.exit(3)


if __name__ == "__main__":
    main()