import asyncio
import pytest
from src.frontend.views.numeric_systems.view_numeric_systems import NumericSystemsUI
from src.backend.solvers.numeric_systems.conversor_bases import ConversorBases

def test_numeric_systems_ui_init():
    ui_inst = NumericSystemsUI()
    assert ui_inst.base_activa == 'decimal'
    assert ui_inst.base_destino == 'todas'
    assert ui_inst.btn_convertir is None
    assert ui_inst.tiene_resultado is False
    assert 'binario' in ui_inst.regex_bases
    assert 'octal' in ui_inst.regex_bases
    assert 'decimal' in ui_inst.regex_bases
    assert 'hexadecimal' in ui_inst.regex_bases

def test_agrupar():
    ui_inst = NumericSystemsUI()
    assert ui_inst._agrupar("11111111", 4) == "1111 1111"
    assert ui_inst._agrupar("101010", 4) == "10 1010"
    assert ui_inst._agrupar("FF", 2) == "FF"
    assert ui_inst._agrupar("1A3F", 2) == "1A 3F"
    assert ui_inst._agrupar("-11111111", 4) == "-1111 1111"

def test_conversor_pasos_decimal_to_all():
    conversor = ConversorBases()
    res = conversor.decimal_a_todo("42", "todas")
    assert "pasos" in res
    pasos = res["pasos"]
    # From decimal, no expansion posicional; divisiones hacia 2, 8, 16
    assert len(pasos) == 3
    for p in pasos:
        assert p["tipo"] == "division_sucesiva"
    destinos = [p["base_destino"] for p in pasos]
    assert destinos == [2, 8, 16]

def test_conversor_pasos_hex_to_all():
    conversor = ConversorBases()
    res = conversor.hexadecimal_a_todo("2A", "todas")
    assert "pasos" in res
    pasos = res["pasos"]
    # From hex, first step is expansion posicional
    assert pasos[0]["tipo"] == "expansion_posicional"
    assert pasos[0]["base_origen"] == 16
    # Followed by divisiones hacia 2, 8
    destinos = [p["base_destino"] for p in pasos[1:]]
    assert destinos == [2, 8]


def test_conversor_limpiar_y_desincronizar():
    ui_inst = NumericSystemsUI()
    ui_inst.tiene_resultado = True

    class DummyElement:
        def __init__(self):
            self.styles = []
            self.cleared = False
            self.text = ""
        def style(self, s):
            self.styles.append(s)
        def clear(self):
            self.cleared = True
        def classes(self, *args, **kwargs):
            pass

    dummy_card = DummyElement()
    ui_inst.ui_cards = {'decimal': dummy_card}
    ui_inst.lbl_info_bits = DummyElement()
    ui_inst.bits_container = DummyElement()
    ui_inst.pasos_container = DummyElement()

    ui_inst._marcar_resultado_desincronizado()
    assert 'opacity: 0.45;' in dummy_card.styles
    assert 'opacity: 0.45;' in ui_inst.bits_container.styles

    ui_inst._limpiar_resultados()
    assert ui_inst.tiene_resultado is False
    assert ui_inst.resultados['decimal'] == '0'
    assert 'opacity: 0; transform: translateY(16px);' in dummy_card.styles
    assert 'opacity: 0;' in ui_inst.bits_container.styles


@pytest.mark.anyio
async def test_cambiar_base_destino_permite_decimal():
    ui_inst = NumericSystemsUI()
    assert ui_inst.base_activa == 'decimal'

    class DummyEvent:
        def __init__(self, val):
            self.value = val

    class DummyTabs:
        def __init__(self, val):
            self.value = val
        def set_value(self, val):
            self.value = val

    ui_inst.tabs_destino = DummyTabs('todas')
    ui_inst._cambiar_base_destino(DummyEvent('decimal'))
    assert ui_inst.base_destino == 'decimal'
    assert ui_inst.tabs_destino.value == 'todas'
    await asyncio.sleep(0.01)



