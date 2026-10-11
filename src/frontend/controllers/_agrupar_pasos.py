"""Agrupación y clasificación didáctica de pasos de eliminación por filas."""

from __future__ import annotations

from typing import Any

from src.backend.utils.formatters import format_fraction_str
from src.frontend.controllers._step_classifier import classify_step


def agrupar_pasos_eliminacion(
    pasos_crudos: list[dict],
    n_izq: int,
    estado: str | None,
    *,
    contexto: str,
    metodo: str | None = None,
) -> tuple[list[dict], list[dict], dict]:
    """Clasifica los pasos de eliminación, asigna explicaciones y los agrupa por fases.

    Args:
        pasos_crudos: Lista de pasos del solver con descripción y matriz.
        n_izq: Número de columnas del bloque izquierdo (n en inversa, n_vars en sistemas).
        estado: Estado del solver ('SUCCESS', 'UNIQUE_SOLUTION', etc.).
        contexto: Ámbito pedagógico ('inversa' o 'sistema').
        metodo: Método de resolución ('gauss', 'gauss-jordan', etc.).

    Returns:
        Tupla con (pasos, grupos, estadisticas).
    """
    steps: list[dict] = []
    raw_groups: list[dict] = []
    current_col_group: dict | None = None
    current_norm_group: dict | None = None
    current_other_group: dict | None = None

    es_gauss = str(metodo).lower() == "gauss"

    for idx, step in enumerate(pasos_crudos):
        desc = step.get("description", "")
        mat = step.get("matrix")

        parsed = classify_step(desc)
        kind = parsed["kind"]
        pivot: tuple[int, int] | None = None
        rows_changed: list[int] = []
        swap_rows: tuple[int, int] | None = None
        explanation = desc

        if kind == "inicial":
            if contexto == "inversa":
                explanation = (
                    "Construimos la matriz aumentada [A | I]: A a la izquierda y la "
                    "identidad I a la derecha. Meta: aplicar operaciones elementales "
                    "de fila hasta obtener [I | A⁻¹]."
                )
                title = "Matriz inicial [A | I]"
            else:
                if es_gauss:
                    explanation = (
                        "Escribimos la matriz aumentada [A | b]: los coeficientes a la izquierda "
                        "y el vector b a la derecha. Meta: aplicar operaciones elementales de fila "
                        "hasta obtener la forma escalonada."
                    )
                else:
                    explanation = (
                        "Escribimos la matriz aumentada [A | b]: los coeficientes a la izquierda "
                        "y el vector b a la derecha. Meta: aplicar operaciones elementales de fila "
                        "hasta obtener la forma escalonada reducida."
                    )
                title = "Matriz inicial [A | b]"

            current_col_group = None
            current_norm_group = None
            current_other_group = None
            group = {
                "kind": "inicial",
                "title": title,
                "step_indices": [idx],
            }
            raw_groups.append(group)
            group_idx = len(raw_groups) - 1

        elif kind == "intercambio":
            a = parsed["row1"] + 1
            b = parsed["row2"] + 1
            swap_rows = (a - 1, b - 1)
            rows_changed = [a - 1, b - 1]
            explanation = (
                f"Intercambiamos la fila {a} con la fila {b} para que el pivote "
                f"sea el elemento de mayor valor absoluto de la columna (pivoteo parcial). "
                f"Intercambiar filas no altera el resultado."
            )
            current_norm_group = None
            current_other_group = None
            current_col_group = {
                "kind": "columna",
                "title": "",
                "step_indices": [idx],
                "has_swap": True,
                "pivot_row": None,
                "pivot_col": None,
                "pivot_val": None,
            }
            raw_groups.append(current_col_group)
            group_idx = len(raw_groups) - 1

        elif kind == "pivote":
            r = parsed["row1"] + 1
            c = parsed["col"] + 1
            pivot = (r - 1, c - 1)
            rows_changed = []
            p_val = (
                format_fraction_str(mat.obtener(r - 1, c - 1) if hasattr(mat, "obtener") else mat.get(r - 1, c - 1))
                if mat is not None
                else ""
            )
            if contexto == "inversa":
                explanation = (
                    f"Pivote: fila {r}, columna {c} (valor {p_val}). "
                    f"Usaremos esta fila para anular el resto de la columna {c}."
                )
            else:
                if es_gauss:
                    explanation = (
                        f"Pivote: fila {r}, columna {c} (valor {p_val}). "
                        f"Usaremos esta fila para eliminar las entradas debajo del pivote en la columna {c}."
                    )
                else:
                    explanation = (
                        f"Pivote: fila {r}, columna {c} (valor {p_val}). "
                        f"Usaremos esta fila para anular las entradas por encima y por debajo del pivote en la columna {c}."
                    )

            current_norm_group = None
            current_other_group = None

            if (
                current_col_group is not None
                and current_col_group.get("pivot_row") is None
            ):
                current_col_group["pivot_row"] = r - 1
                current_col_group["pivot_col"] = c - 1
                current_col_group["pivot_val"] = p_val
                current_col_group["step_indices"].append(idx)
                group_idx = raw_groups.index(current_col_group)
            else:
                current_col_group = {
                    "kind": "columna",
                    "title": "",
                    "step_indices": [idx],
                    "has_swap": False,
                    "pivot_row": r - 1,
                    "pivot_col": c - 1,
                    "pivot_val": p_val,
                }
                raw_groups.append(current_col_group)
                group_idx = len(raw_groups) - 1

        elif kind == "eliminacion":
            t = parsed["row1"] + 1
            f = parsed["val_str"]
            p = parsed["row2"] + 1
            rows_changed = [t - 1]
            pivot_col = (
                current_col_group["pivot_col"]
                if (
                    current_col_group is not None
                    and current_col_group.get("pivot_col") is not None
                )
                else (p - 1)
            )
            pivot = (p - 1, pivot_col)
            if contexto == "inversa":
                explanation = (
                    f"Hacemos 0 la entrada de la fila {t} en la columna {pivot_col + 1}: "
                    f"Fila {t} = Fila {t} − ({f}) · Fila {p}. La operación afecta la "
                    f"fila completa, es decir, los dos bloques a la vez."
                )
            else:
                explanation = (
                    f"Hacemos 0 la entrada de la fila {t} en la columna {pivot_col + 1}: "
                    f"Fila {t} = Fila {t} − ({f}) · Fila {p}. La operación afecta a toda la fila de [A | b]."
                )

            current_norm_group = None
            current_other_group = None
            if current_col_group is not None:
                current_col_group["step_indices"].append(idx)
                group_idx = raw_groups.index(current_col_group)
            else:
                if current_other_group is None:
                    current_other_group = {
                        "kind": "otros",
                        "title": "Otras operaciones",
                        "step_indices": [idx],
                    }
                    raw_groups.append(current_other_group)
                    group_idx = len(raw_groups) - 1
                else:
                    current_other_group["step_indices"].append(idx)
                    group_idx = raw_groups.index(current_other_group)

        elif kind == "normalizacion":
            r = parsed["row1"] + 1
            v = parsed["val_str"]
            rows_changed = [r - 1]
            pivot = (r - 1, r - 1) if (r - 1 < n_izq) else None
            if contexto == "inversa":
                explanation = (
                    f"Dividimos la fila {r} entre {v} para que su pivote valga 1 "
                    f"y la diagonal del bloque izquierdo quede igual a la identidad."
                )
            else:
                explanation = (
                    f"Dividimos la fila {r} entre {v} para que su pivote valga 1."
                )

            current_col_group = None
            current_other_group = None
            if current_norm_group is None:
                current_norm_group = {
                    "kind": "normalizacion",
                    "title": "Normalización: cada pivote pasa a 1",
                    "step_indices": [idx],
                }
                raw_groups.append(current_norm_group)
                group_idx = len(raw_groups) - 1
            else:
                current_norm_group["step_indices"].append(idx)
                group_idx = raw_groups.index(current_norm_group)

        else:
            kind = "otro"
            explanation = desc
            if current_col_group is not None:
                current_col_group["step_indices"].append(idx)
                group_idx = raw_groups.index(current_col_group)
            elif current_norm_group is not None:
                current_norm_group["step_indices"].append(idx)
                group_idx = raw_groups.index(current_norm_group)
            else:
                if current_other_group is None:
                    current_other_group = {
                        "kind": "otros",
                        "title": "Otras operaciones",
                        "step_indices": [idx],
                    }
                    raw_groups.append(current_other_group)
                    group_idx = len(raw_groups) - 1
                else:
                    current_other_group["step_indices"].append(idx)
                    group_idx = raw_groups.index(current_other_group)

        # Si el paso es el ÚLTIMO de la lista y status == SUCCESS solo en contexto inversa
        if contexto == "inversa" and idx == len(pasos_crudos) - 1 and estado == "SUCCESS":
            explanation = (
                "Resultado: el bloque izquierdo ya es I, por lo tanto el bloque "
                "derecho es A⁻¹. " + explanation
            )

        steps.append({
            "index": idx,
            "description": desc,
            "kind": kind,
            "group_index": group_idx,
            "pivot": pivot,
            "rows_changed": rows_changed,
            "swap_rows": swap_rows,
            "explanation": explanation,
            "matrix": mat,
        })

    # Formatear grupos finales
    groups: list[dict] = []
    for g in raw_groups:
        k = len(g["step_indices"])
        summary = "1 operación" if k == 1 else f"{k} operaciones"
        g_kind = g.get("kind", "otro")
        if g_kind == "columna":
            c = g.get("pivot_col")
            r = g.get("pivot_row")
            val = g.get("pivot_val")
            has_swap = g.get("has_swap", False)
            if c is not None and r is not None and val is not None:
                title = f"Columna {c + 1} · pivote {val} en fila {r + 1}"
                if has_swap:
                    title += " · con intercambio"
            elif c is not None:
                title = f"Columna {c + 1}"
            else:
                title = "Columna"
        else:
            title = g.get("title", "")

        groups.append({
            "title": title,
            "summary": summary,
            "kind": g_kind,
            "step_indices": g["step_indices"],
        })

    stats = {
        "total": len(steps),
        "pivotes": sum(1 for s in steps if s["kind"] == "pivote"),
        "intercambios": sum(1 for s in steps if s["kind"] == "intercambio"),
        "eliminaciones": sum(1 for s in steps if s["kind"] == "eliminacion"),
        "normalizaciones": sum(1 for s in steps if s["kind"] == "normalizacion"),
    }

    return steps, groups, stats
