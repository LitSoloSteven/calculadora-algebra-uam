"""Pruebas del modelo puro del Hub de Scalaris y contrato estatico de hub.js (Fases P2a y P3)."""
from pathlib import Path
import pytest

from src.frontend.views.hub._model import (
    InitialSelection,
    PillarModel,
    TileModel,
    hub_pillars,
    initial_selection,
    matrix_cells,
)


def test_hub_pillars_structure():
    """Verifica que hub_pillars devuelva 3 pilares con 4, 3 y 2 tiles respectivamente."""
    pillars = hub_pillars()
    assert len(pillars) == 3
    assert all(isinstance(p, PillarModel) for p in pillars)

    p_algebra, p_vis, p_util = pillars

    assert p_algebra.id == "algebra"
    assert p_algebra.short_name == "Álgebra lineal"
    assert len(p_algebra.tiles) == 4
    assert [t.key for t in p_algebra.tiles] == ["sistemas", "vectores", "matrices", "inversa"]
    assert all(isinstance(t, TileModel) for t in p_algebra.tiles)

    assert p_vis.id == "visualizador"
    assert p_vis.short_name == "Visualizador"
    assert len(p_vis.tiles) == 3
    assert [t.key for t in p_vis.tiles] == ["vis:rectas-planos", "vis:vectores", "vis:combinacion"]

    assert p_util.id == "utilidades"
    assert p_util.short_name == "Utilidades"
    assert len(p_util.tiles) == 2
    assert [t.key for t in p_util.tiles] == ["bases", "romanos"]


def test_matrix_cells_dimension():
    """Verifica que matrix_cells genere la matriz identidad n x n."""
    assert matrix_cells(3) == (
        ("1", "0", "0"),
        ("0", "1", "0"),
        ("0", "0", "1"),
    )
    assert matrix_cells(1) == (("1",),)
    assert matrix_cells(2) == (
        ("1", "0"),
        ("0", "1"),
    )


def test_matrix_cells_invalid_dimension():
    """Verifica que matrix_cells rechace dimensiones menores a 1."""
    with pytest.raises(ValueError):
        matrix_cells(0)
    with pytest.raises(ValueError):
        matrix_cells(-1)


def test_initial_selection_empty_history():
    """Verifica degradacion al estado vacio orientativo (Sistemas de ecuaciones)."""
    sel = initial_selection([])
    assert isinstance(sel, InitialSelection)
    assert sel.pillar_id == "algebra"
    assert sel.tile_key == "sistemas"
    assert sel.has_history is False


def test_initial_selection_valid_history():
    """Verifica seleccion focal en base al primer elemento valido del historial."""
    sel = initial_selection(["romanos", "inversa"])
    assert sel.pillar_id == "utilidades"
    assert sel.tile_key == "romanos"
    assert sel.has_history is True


def test_initial_selection_visualizer():
    """Verifica que una herramienta de visualizador active el pilar y la escena predeterminada."""
    sel = initial_selection(["visualizador"])
    assert sel.pillar_id == "visualizador"
    assert sel.tile_key == "vis:rectas-planos"
    assert sel.has_history is True


@pytest.mark.parametrize(
    "history, expected_pillar, expected_tile",
    [
        (["romanos", "inversa"], "utilidades", "romanos"),
        (["inversa", "sistemas"], "algebra", "inversa"),
        (["vectores"], "algebra", "vectores"),
        (["matrices"], "algebra", "matrices"),
        (["bases"], "utilidades", "bases"),
        (["visualizador"], "visualizador", "vis:rectas-planos"),
        (["visualizador", "romanos"], "visualizador", "vis:rectas-planos"),
        # Duplicados
        (["romanos", "romanos"], "utilidades", "romanos"),
        (["inversa", "inversa", "sistemas"], "algebra", "inversa"),
        # Mezcla de validos e invalidos (el primer valido manda)
        (["zzz", "romanos"], "utilidades", "romanos"),
        ([None, 123, "zzz", "visualizador"], "visualizador", "vis:rectas-planos"),
        (["desconocido", None, "matrices", "inversa"], "algebra", "matrices"),
    ],
)
def test_initial_selection_parametrized_valid(history, expected_pillar, expected_tile):
    """Verifica seleccion correcta con historiales validos, duplicados y mezclas con invalidos."""
    sel = initial_selection(history)
    assert sel.pillar_id == expected_pillar
    assert sel.tile_key == expected_tile
    assert sel.has_history is True


@pytest.mark.parametrize(
    "corrupt",
    [
        [],
        None,
        "x",
        "sistemas",
        42,
        {"a": 1},
        ["zzz"],
        ["inexistente_xyz"],
        [None],
        [None, 42, False],
        [{"a": 1}, ["x"]],
        ["invalido_1", "zzz"],
    ],
)
def test_initial_selection_corrupt_data(corrupt):
    """Verifica degradacion silenciosa ante datos corruptos, no lista, vacio o solo ids desconocidos."""
    sel = initial_selection(corrupt)
    assert sel.pillar_id == "algebra"
    assert sel.tile_key == "sistemas"
    assert sel.has_history is False


def test_hub_js_static_contract():
    """Verifica el contrato estatico de assets/js/hub.js (sin scroll listeners ni estado ajeno)."""
    js_path = Path("src/frontend/assets/js/hub.js")
    assert js_path.exists()
    content = js_path.read_text(encoding="utf-8")

    # No contiene scroll listeners
    assert "addEventListener('scroll'" not in content
    assert 'addEventListener("scroll"' not in content

    # No contiene requestAnimationFrame sobre frameworks reactivos (React/Vue/useState)
    assert "useState" not in content
    assert "setState" not in content
    assert "React" not in content
    assert "Vue" not in content

    # Exporta scalarisReadRecent, scalarisRecordVisit y scalarisHubSelect
    assert "window.scalarisReadRecent =" in content
    assert "window.scalarisRecordVisit =" in content
    assert "window.scalarisHubSelect =" in content

    # Referencia al selector exacto de tiles del panel activo
    assert "'.hub-panel.is-active .hub-tile'" in content
