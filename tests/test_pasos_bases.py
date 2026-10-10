"""Pruebas del reproductor interactivo de pasos para el Conversor de Bases."""

import ast
import re
import time
from pathlib import Path
import pytest

from src.backend.solvers.numeric_systems.conversor_bases import ConversorBases
from src.frontend.views.numeric_systems._pasos_bases import construir_pasos_bases


def test_decimal_255_generates_expected_groups_and_steps():
    """Decimal 255 genera 3 conversiones por división con len(filas) + 1 pasos cada una."""
    conversor = ConversorBases()
    res = conversor.decimal_a_todo("255", "todas")
    pasos, grupos = construir_pasos_bases(res)

    assert len(grupos) == 3
    assert [g.tipo for g in grupos] == ["division", "division", "division"]

    pasos_raw = res["pasos"]
    total_esperado = 0
    for k, g in enumerate(grupos):
        conv = pasos_raw[k]
        filas = conv["filas"]
        esperado_grupo = len(filas) + 1
        assert len(g.indices_pasos) == esperado_grupo
        total_esperado += esperado_grupo

        # Los pasos intermedios son de tipo division y el último es lectura
        for idx in g.indices_pasos[:-1]:
            assert pasos[idx].tipo == "division"
            assert pasos[idx].etiqueta_tipo == "División"
        ultimo_idx = g.indices_pasos[-1]
        assert pasos[ultimo_idx].tipo == "lectura"
        assert pasos[ultimo_idx].etiqueta_tipo == "Lectura"

    assert len(pasos) == total_esperado
    assert len(pasos) == 16  # 9 (bin) + 4 (oct) + 3 (hex)


def test_hex_2a_first_group_is_expansion():
    """Hexadecimal 2A genera primer grupo expansion con len(terminos) + 1 pasos."""
    conversor = ConversorBases()
    res = conversor.hexadecimal_a_todo("2A", "todas")
    pasos, grupos = construir_pasos_bases(res)

    assert len(grupos) == 3
    g_exp = grupos[0]
    assert g_exp.tipo == "expansion"
    assert "Expansión Posicional desde Hexadecimal" in g_exp.titulo

    terminos = res["pasos"][0]["terminos"]
    assert len(terminos) == 2
    assert len(g_exp.indices_pasos) == 3  # 2 terminos + 1 resultado

    for idx in g_exp.indices_pasos[:-1]:
        assert pasos[idx].tipo == "expansion"
        assert pasos[idx].etiqueta_tipo == "Expansión"

    idx_res = g_exp.indices_pasos[-1]
    assert pasos[idx_res].tipo == "resultado"
    assert pasos[idx_res].etiqueta_tipo == "Resultado"

    # Los siguientes grupos son divisiones
    assert [g.tipo for g in grupos[1:]] == ["division", "division"]


def test_negative_conversion_preserves_sign():
    """Valores negativos contemplan el signo en explicaciones y resultados."""
    conversor = ConversorBases()
    res_dec = conversor.decimal_a_todo("-42", "todas")
    pasos_dec, grupos_dec = construir_pasos_bases(res_dec)
    assert len(grupos_dec) == 3
    assert len(pasos_dec) > 0

    res_hex = conversor.hexadecimal_a_todo("-2A", "todas")
    pasos_hex, grupos_hex = construir_pasos_bases(res_hex)
    assert len(grupos_hex) == 3

    paso_res = pasos_hex[grupos_hex[0].indices_pasos[-1]]
    assert paso_res.tipo == "resultado"
    assert "-42" in paso_res.descripcion
    assert "negativo" in paso_res.explicacion


def test_200_bit_number_generates_steps_fast():
    """Un número de 200 bits genera pasos sin error y en menos de 2 segundos."""
    conversor = ConversorBases()
    bin_200 = "1" * 200

    start = time.perf_counter()
    res = conversor.binario_a_todo(bin_200, "todas")
    pasos, grupos = construir_pasos_bases(res)
    duracion = time.perf_counter() - start

    assert duracion < 2.0
    assert len(grupos) == 3
    assert len(pasos) > 200


def test_input_zero_generates_steps():
    """Entrada con valor 0 genera pasos y grupos válidos sin fallar."""
    conversor = ConversorBases()
    res = conversor.decimal_a_todo("0", "todas")
    pasos, grupos = construir_pasos_bases(res)

    assert len(grupos) == 3
    assert len(pasos) == 6  # 2 pasos por cada una de las 3 bases destino


def test_values_are_escaped():
    """Verifica que los valores insertados en HTML se escapan contra inyecciones."""
    paso_malicioso = {
        "tipo": "expansion_posicional",
        "base_origen": 16,
        "terminos": [
            {
                "digito": "<script>alert(1)</script>",
                "valor": 10,
                "potencia": 1,
                "peso": 16,
                "producto": 160,
            }
        ],
        "total": "160",
        "es_negativo": False,
    }
    pasos, grupos = construir_pasos_bases([paso_malicioso])
    assert len(pasos) == 2

    cuerpo_html = str(pasos[0].cuerpo)
    assert "<script>" not in cuerpo_html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in cuerpo_html


def test_no_forbidden_strings_nor_voseo():
    """Verifica que los archivos de la fase F7 no contienen —, Oops ni voseo."""
    files_to_check = [
        Path("src/frontend/views/numeric_systems/_pasos_bases.py"),
        Path("src/frontend/views/numeric_systems/procedure_mixin.py"),
        Path("src/frontend/views/numeric_systems/rendering_mixin.py"),
    ]

    voseo_pattern = re.compile(
        r"\b(ingresá|añadí|escribí|presioná|pegá|sumá|calculá|mostrá|revisá)\b",
        re.IGNORECASE,
    )

    for p in files_to_check:
        assert p.exists()
        text = p.read_text(encoding="utf-8")
        assert "—" not in text, f"Em-dash encontrado en {p}"
        assert "Oops" not in text, f"Oops encontrado en {p}"

        tree = ast.parse(text, filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value
                match = voseo_pattern.search(s)
                assert match is None, f"Voseo '{match.group(0)}' en {p}: {s}"
