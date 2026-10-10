"""Fija las salidas actuales del renderizador y el controlador de inversa."""

import json
from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.frontend.controllers.inverse_ops.controller_inverse_ops import InverseOpsController
from src.frontend.components.reproductor_pasos import (
    formatear_decimal,
    formatear_valor,
    html_chip_tipo,
    html_tabla_aumentada,
    html_tabla_matriz,
)


TABLA_MATRIZ = '<div class="inv-scroll"><table class="inv-table"><thead><tr><th class=\'row-label\'></th><th>C1</th><th>C2</th></tr></thead><tbody><tr><th class=\'row-label\'>F1</th><td title="≈ 0.5"><span class="inv-frac"><span>1</span><span>2</span></span></td><td>-2</td></tr><tr><th class=\'row-label\'>F2</th><td>3</td><td title="≈ -1.3333">−<span class="inv-frac"><span>4</span><span>3</span></span></td></tr></tbody></table></div>'
TABLA_AUMENTADA = '<div class="inv-scroll"><table class="inv-table"><thead><tr><th class=\'row-label\'></th><th>1</th><th>2</th><th class=\'sep-left\'>1</th><th>2</th></tr></thead><tbody><tr><th class=\'row-label\'>F1</th><td title="≈ 0.5"><span class="inv-frac"><span>1</span><span>2</span></span></td><td>-2</td><td class="sep-left">1</td><td>0</td></tr><tr><th class=\'row-label\'>F2</th><td>3</td><td title="≈ -1.3333">−<span class="inv-frac"><span>4</span><span>3</span></span></td><td class="sep-left">0</td><td>1</td></tr></tbody></table></div>'


def _html_aumentado(**opciones):
    """Renderiza la matriz fija de caracterización con las opciones indicadas."""
    matriz = Matrix(2, 4, [[Fraction(1, 2), -2, 1, 0], [3, Fraction(-4, 3), 0, 1]])
    return html_tabla_aumentada(matriz, 2, **opciones)


def _resumen_controlador(datos):
    """Extrae del resultado los campos contractuales independientes del tiempo."""
    resultado = InverseOpsController.process_inverse(
        json.dumps({"n": len(datos), "data": datos})
    )
    pasos = [
        {campo: paso[campo] for campo in ("kind", "group_index", "explanation")}
        for paso in resultado["steps"]
    ]
    return pasos, resultado["groups"], resultado["stats"]


def test_formateadores_y_tabla_matriz_conservan_su_html():
    """Fija la salida literal de valores, decimales y la tabla de matriz."""
    matriz = Matrix(2, 2, [[Fraction(1, 2), -2], [3, Fraction(-4, 3)]])
    assert formatear_valor(Fraction(-3, 4), apilada=True) == '−<span class="inv-frac"><span>3</span><span>4</span></span>'
    assert formatear_valor(Fraction(4, 1)) == "4"
    assert formatear_decimal(Fraction(1, 3)) == "0.3333"
    assert html_tabla_matriz(matriz) == TABLA_MATRIZ


def test_tabla_aumentada_conserva_resaltados_y_bloque_final():
    """Fija el HTML base y los resaltados de cambio, pivote, intercambio y resultado."""
    assert _html_aumentado() == TABLA_AUMENTADA
    assert _html_aumentado(filas_cambiadas=(1,)) == TABLA_AUMENTADA.replace(
        "<tr><th class=\'row-label\'>F2", '<tr class="row-changed"><th class=\'row-label\'>F2'
    )
    assert _html_aumentado(pivote=(0, 0)) == TABLA_AUMENTADA.replace(
        "<td title=\"≈ 0.5\">", '<td class="cell-pivot" title="≈ 0.5">', 1
    )
    tabla_intercambiada = TABLA_AUMENTADA.replace(
        "<tr><th class=\'row-label\'>F1", '<tr class="row-swap"><th class=\'row-label\'>F1'
    ).replace(
        "<tr><th class=\'row-label\'>F2", '<tr class="row-swap"><th class=\'row-label\'>F2'
    )
    assert _html_aumentado(filas_intercambio=(0, 1)) == tabla_intercambiada
    final = TABLA_AUMENTADA.replace('class="inv-table"', 'class="inv-table is-result"')
    final = final.replace('<td class="sep-left">1', '<td class="sep-left block-result">1')
    final = final.replace('<td class="sep-left">0', '<td class="sep-left block-result">0')
    final = final.replace('<td>0</td>', '<td class="block-result">0</td>')
    final = final.replace('<td>1</td>', '<td class="block-result">1</td>')
    assert _html_aumentado(bloque_resultado=True) == final


def test_chip_de_intercambio_conserva_su_html():
    """Fija el HTML del chip actual de intercambio de filas."""
    assert html_chip_tipo("intercambio") == '<span class="chip-kind chip-intercambio"><span class="material-icons">swap_vert</span>Intercambio</span>'


def test_controlador_inversa_dos_por_dos_conserva_pasos_grupos_y_estadisticas():
    """Fija la secuencia completa que devuelve el controlador para una matriz 2x2."""
    pasos, grupos, estadisticas = _resumen_controlador([[1, 2], [3, 4]])
    assert [(paso["kind"], paso["group_index"]) for paso in pasos] == [
        ("inicial", 0), ("intercambio", 1), ("pivote", 1), ("eliminacion", 1),
        ("pivote", 2), ("eliminacion", 2), ("normalizacion", 3), ("normalizacion", 3),
    ]
    assert [paso["explanation"] for paso in pasos] == [
        "Construimos la matriz aumentada [A | I]: A a la izquierda y la identidad I a la derecha. Meta: aplicar operaciones elementales de fila hasta obtener [I | A⁻¹].",
        "Intercambiamos la fila 1 con la fila 2 para que el pivote sea el elemento de mayor valor absoluto de la columna (pivoteo parcial). Intercambiar filas no altera el resultado.",
        "Pivote: fila 1, columna 1 (valor 3). Usaremos esta fila para anular el resto de la columna 1.",
        "Hacemos 0 la entrada de la fila 2 en la columna 1: Fila 2 = Fila 2 − (1/3) · Fila 1. La operación afecta la fila completa, es decir, los dos bloques a la vez.",
        "Pivote: fila 2, columna 2 (valor 2/3). Usaremos esta fila para anular el resto de la columna 2.",
        "Hacemos 0 la entrada de la fila 1 en la columna 2: Fila 1 = Fila 1 − (6) · Fila 2. La operación afecta la fila completa, es decir, los dos bloques a la vez.",
        "Dividimos la fila 1 entre 3 para que su pivote valga 1 y la diagonal del bloque izquierdo quede igual a la identidad.",
        "Resultado: el bloque izquierdo ya es I, por lo tanto el bloque derecho es A⁻¹. Dividimos la fila 2 entre 2/3 para que su pivote valga 1 y la diagonal del bloque izquierdo quede igual a la identidad.",
    ]
    assert grupos == [
        {"title": "Matriz inicial [A | I]", "summary": "1 operación", "kind": "inicial", "step_indices": [0]},
        {"title": "Columna 1 · pivote 3 en fila 1 · con intercambio", "summary": "3 operaciones", "kind": "columna", "step_indices": [1, 2, 3]},
        {"title": "Columna 2 · pivote 2/3 en fila 2", "summary": "2 operaciones", "kind": "columna", "step_indices": [4, 5]},
        {"title": "Normalización: cada pivote pasa a 1", "summary": "2 operaciones", "kind": "normalizacion", "step_indices": [6, 7]},
    ]
    assert estadisticas == {"total": 8, "pivotes": 2, "intercambios": 1, "eliminaciones": 2, "normalizaciones": 2}


def test_controlador_inversa_tres_por_tres_conserva_intercambio():
    """Fija la salida del controlador para una matriz 3x3 que requiere intercambio."""
    pasos, grupos, estadisticas = _resumen_controlador([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
    assert [(paso["kind"], paso["group_index"]) for paso in pasos] == [
        ("inicial", 0), ("intercambio", 1), ("pivote", 1), ("pivote", 2), ("pivote", 3),
    ]
    assert [paso["explanation"] for paso in pasos] == [
        "Construimos la matriz aumentada [A | I]: A a la izquierda y la identidad I a la derecha. Meta: aplicar operaciones elementales de fila hasta obtener [I | A⁻¹].",
        "Intercambiamos la fila 1 con la fila 2 para que el pivote sea el elemento de mayor valor absoluto de la columna (pivoteo parcial). Intercambiar filas no altera el resultado.",
        "Pivote: fila 1, columna 1 (valor 1). Usaremos esta fila para anular el resto de la columna 1.",
        "Pivote: fila 2, columna 2 (valor 1). Usaremos esta fila para anular el resto de la columna 2.",
        "Resultado: el bloque izquierdo ya es I, por lo tanto el bloque derecho es A⁻¹. Pivote: fila 3, columna 3 (valor 1). Usaremos esta fila para anular el resto de la columna 3.",
    ]
    assert grupos == [
        {"title": "Matriz inicial [A | I]", "summary": "1 operación", "kind": "inicial", "step_indices": [0]},
        {"title": "Columna 1 · pivote 1 en fila 1 · con intercambio", "summary": "2 operaciones", "kind": "columna", "step_indices": [1, 2]},
        {"title": "Columna 2 · pivote 1 en fila 2", "summary": "1 operación", "kind": "columna", "step_indices": [3]},
        {"title": "Columna 3 · pivote 1 en fila 3", "summary": "1 operación", "kind": "columna", "step_indices": [4]},
    ]
    assert estadisticas == {"total": 5, "pivotes": 3, "intercambios": 1, "eliminaciones": 0, "normalizaciones": 0}
