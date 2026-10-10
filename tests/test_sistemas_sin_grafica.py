"""Comprueba que Sistemas conserva el traspaso al Visualizador sin gráficos propios."""

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
VISTAS_SISTEMAS = RAIZ / "src/frontend/views/linear_systems"
EXTENSIONES_FUENTE = {".py", ".js", ".css", ".html"}


def test_no_existe_el_mixin_de_graficas():
    """Confirma que el módulo de gráficos redundante fue retirado."""
    assert not (VISTAS_SISTEMAS / "graphics_mixin.py").exists()


def test_frontend_no_contiene_la_grafica_de_sistemas():
    """Busca referencias al gráfico retirado en todos los archivos del frontend."""
    terminos = ("render_graphics", "Visualización Gráfica")
    for archivo in (RAIZ / "src/frontend").rglob("*"):
        if not archivo.is_file() or archivo.suffix not in EXTENSIONES_FUENTE:
            continue
        contenido = archivo.read_text(encoding="utf-8", errors="ignore")
        assert all(termino not in contenido for termino in terminos), str(archivo)


def test_resultados_conservan_el_boton_y_su_handoff():
    """Verifica el botón existente, su condición, su tooltip y el traspaso de datos."""
    contenido = (VISTAS_SISTEMAS / "results_mixin.py").read_text(encoding="utf-8")
    assert "if n_vars in (2, 3):" in contenido
    assert "Ver en el Visualizador" in contenido
    assert "put_system('sistemas', matrix_A_vals, vector_b_vals)" in contenido
    assert ".tooltip('Visualiza el sistema en R² o R³')" in contenido
