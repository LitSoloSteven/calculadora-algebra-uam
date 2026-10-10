"""Pruebas del reproductor interactivo de pasos para la Calculadora de Números Romanos."""

import ast
import re
from pathlib import Path

from src.backend.solvers.numeric_systems.roman_calculator import (
    RomanCalculator,
    RomanNumeralError,
)
from src.frontend.views.numeric_systems.roman_steps import (
    construir_pasos_romanos,
    desglosar_pasos_canonicos,
)
from src.frontend.views.numeric_systems.view_roman_calculator import (
    RomanCalculatorUI,
)


def test_suma_xiv_mas_ix():
    """Suma XIV + IX genera 3 grupos: decodificación, operación y construcción canónica."""
    res = RomanCalculator.sumar("XIV", "IX")
    pasos, grupos = construir_pasos_romanos(res, "suma")

    assert len(grupos) == 3
    assert grupos[0].titulo == "Decodificación de operandos a decimal"
    assert grupos[0].tipo == "decodificacion"
    assert len(grupos[0].indices_pasos) == 2

    # Paso 0: Operando A (XIV = 14)
    assert pasos[0].tipo == "decodificacion"
    assert "XIV = 14" in pasos[0].descripcion

    # Paso 1: Operando B (IX = 9)
    assert pasos[1].tipo == "decodificacion"
    assert "IX = 9" in pasos[1].descripcion

    # Grupo 1: Operación suma (1 paso)
    assert grupos[1].tipo == "operacion"
    assert len(grupos[1].indices_pasos) == 1
    idx_op = grupos[1].indices_pasos[0]
    assert pasos[idx_op].tipo == "operacion"
    assert "14 + 9 = 23" in pasos[idx_op].descripcion

    # Grupo 2: Construcción canónica (23 = XXIII: 10, 10, 1, 1, 1 -> 5 pasos + 1 resultado)
    assert grupos[2].tipo == "construccion"
    assert len(grupos[2].indices_pasos) == 6
    for idx in grupos[2].indices_pasos[:-1]:
        assert pasos[idx].tipo == "construccion"
    paso_res = pasos[grupos[2].indices_pasos[-1]]
    assert paso_res.tipo == "resultado"
    assert "XXIII" in paso_res.descripcion
    assert "23" in paso_res.descripcion

    # Metadatos Glosa
    for i, p in enumerate(pasos):
        assert p.meta_explicar["index"] == i + 1
        assert p.meta_explicar["total"] == len(pasos)


def test_resta_xx_menos_viii():
    """Resta XX − VIII incluye validación A > B, resta y construcción canónica de 12 (XII)."""
    res = RomanCalculator.restar("XX", "VIII")
    pasos, grupos = construir_pasos_romanos(res, "resta")

    assert len(grupos) == 3
    # Grupo 0: Decodificación
    assert len(grupos[0].indices_pasos) == 2

    # Grupo 1: Operación resta (validación + resta)
    assert grupos[1].tipo == "operacion"
    assert len(grupos[1].indices_pasos) == 2
    idx_val, idx_op = grupos[1].indices_pasos
    assert pasos[idx_val].tipo == "validacion"
    assert "20 > 8" in pasos[idx_val].descripcion
    assert pasos[idx_op].tipo == "operacion"
    assert "20 − 8 = 12" in pasos[idx_op].descripcion

    # Grupo 2: Construcción (12 = XII: 10, 1, 1 -> 3 pasos + 1 resultado = 4)
    assert grupos[2].tipo == "construccion"
    assert len(grupos[2].indices_pasos) == 4
    paso_final = pasos[grupos[2].indices_pasos[-1]]
    assert paso_final.tipo == "resultado"
    assert "XII" in paso_final.descripcion


def test_multiplicacion_iii_por_iv_iteraciones_exactas():
    """Multiplicación III × IV genera exactamente 4 pasos de iteración acumulada."""
    res = RomanCalculator.multiplicar_un_digito("III", "IV")
    pasos, grupos = construir_pasos_romanos(res, "mult")

    assert len(grupos) == 3
    grp_mult = grupos[1]
    assert grp_mult.tipo == "multiplicacion"
    assert grp_mult.titulo == "Multiplicación mediante sumas sucesivas"

    pasos_mult = [pasos[idx] for idx in grp_mult.indices_pasos]
    # 1 definición + 4 iteraciones + 1 producto final = 6 pasos
    assert len(pasos_mult) == 6

    # Paso de definición
    assert pasos_mult[0].tipo == "definicion"
    assert "sumar 3, 4 veces" in pasos_mult[0].descripcion

    # 4 iteraciones exactas
    iteraciones = [p for p in pasos_mult if p.tipo == "iteracion"]
    assert len(iteraciones) == 4
    assert iteraciones[0].descripcion == "Paso 1: acumulado = 3"
    assert iteraciones[1].descripcion == "Paso 2: acumulado = 6"
    assert iteraciones[2].descripcion == "Paso 3: acumulado = 9"
    assert iteraciones[3].descripcion == "Paso 4: acumulado = 12"

    # Paso de producto
    assert pasos_mult[-1].tipo == "producto"
    assert "3 × 4 = 12" in pasos_mult[-1].descripcion


def test_desglose_canonico_3999():
    """3999 (MMMCMXCIX) se desglosa vorazmente en exactamente 6 sustracciones canónicas."""
    pasos_can = desglosar_pasos_canonicos(3999)
    assert len(pasos_can) == 6

    glifos = [p["simbolo"] for p in pasos_can]
    assert glifos == ["M", "M", "M", "CM", "XC", "IX"]
    assert "".join(glifos) == "MMMCMXCIX"
    assert pasos_can[-1]["restante"] == 0


def test_clasificacion_errores_no_genera_pasos():
    """Clasificación de errores conserva compatibilidad y entradas inválidas no generan pasos."""
    # Clasificación de errores estructurados
    err_zero = RomanNumeralError("No existe el número cero en el sistema romano.", code="ZERO_NOT_REPRESENTABLE")
    assert RomanCalculatorUI.classify_roman_error(err_zero) == "err_sub_zero"

    err_neg = RomanNumeralError("No existen los números negativos en el sistema romano.", code="NEGATIVE_NOT_REPRESENTABLE")
    assert RomanCalculatorUI.classify_roman_error(err_neg) == "err_sub_neg"

    err_syntax = RomanNumeralError("No es sintaxis válida", code="INVALID_SYNTAX")
    assert RomanCalculatorUI.classify_roman_error(err_syntax) == "err_syntax"

    # Errores por fallback de mensaje
    err_msg_zero = ValueError("no existe el número cero")
    assert RomanCalculatorUI.classify_roman_error(err_msg_zero) == "err_sub_zero"

    # Resultado nulo o fallido no produce pasos
    pasos, grupos = construir_pasos_romanos(None, "suma")
    assert pasos == ()
    assert grupos == ()


def test_sin_emdash_ni_voseo_en_textos_romanos():
    """Garantiza ausencia de guion largo ('—') y de voseo en los módulos de números romanos."""
    archivos = [
        Path("src/frontend/views/numeric_systems/roman_steps.py"),
        Path("src/frontend/views/numeric_systems/roman_result_mixin.py"),
        Path("src/frontend/views/numeric_systems/view_roman_calculator.py"),
    ]

    patrones_voseo = [
        re.compile(r"\b(mirá|hacé|tenés|ingresá|probá|andá|decí|podés)\b", re.IGNORECASE),
    ]

    for archivo in archivos:
        contenido = archivo.read_text(encoding="utf-8")
        # No debe contener el guión largo '—' (U+2014)
        assert "—" not in contenido, f"Encontrado guión largo '—' en {archivo}"

        for patron in patrones_voseo:
            coincidencias = patron.findall(contenido)
            assert not coincidencias, f"Encontrado voseo {coincidencias} en {archivo}"

    # Validar que los textos generados por los pasos tampoco contengan '—' ni voseo
    res_mult = RomanCalculator.multiplicar_un_digito("III", "IV")
    pasos, grupos = construir_pasos_romanos(res_mult, "mult")
    for p in pasos:
        assert "—" not in p.descripcion
        assert "—" not in p.explicacion
        for patron in patrones_voseo:
            assert not patron.findall(p.descripcion)
            assert not patron.findall(p.explicacion)
