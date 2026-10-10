"""Pruebas del catálogo, las etiquetas y las tablas del reproductor compartido."""

from pathlib import Path
from fractions import Fraction
from types import SimpleNamespace

from src.backend.models.matrix import Matrix
from src.frontend.components.reproductor_pasos import (
    CATALOGO_TIPOS,
    VELOCIDADES_AUTOREPRODUCCION,
    GrupoReproductor,
    PasoReproductor,
    ReproductorPasos,
    etiqueta_variable_html,
    html_tabla_aumentada,
)
from src.frontend.components.reproductor_pasos import cuerpos
from src.frontend.components.reproductor_pasos import reproductor as modulo_reproductor
from src.frontend.views.inverse_ops._adaptador_pasos import adaptar_pasos_inversa
from src.frontend.controllers.inverse_ops.controller_inverse_ops import InverseOpsController


class _ControlPrueba:
    """Control mínimo para probar la actualización del reproductor sin UI real."""

    def __init__(self, valor=None):
        """Inicializa el valor y el contador de limpiezas del control."""
        self.value = valor
        self.limpiezas = 0

    def set_text(self, texto):
        """Guarda el texto asignado por el reproductor."""
        self.texto = texto

    def set_content(self, contenido):
        """Guarda el contenido asignado por el reproductor."""
        self.contenido = contenido

    def set_value(self, valor):
        """Guarda el valor de progreso asignado por el reproductor."""
        self.value = valor

    def clear(self):
        """Cuenta las limpiezas del contenedor de cuerpo o de Glosa."""
        self.limpiezas += 1


def _crear_reproductor_prueba():
    """Crea un reproductor mínimo con controles falsos para probar navegación."""
    pasos = (
        PasoReproductor(0, "inicial", "Inicio", "Explicación inicial", 0),
        PasoReproductor(1, "final", "Resultado", "Explicación final", 1),
    )
    reproductor = ReproductorPasos.__new__(ReproductorPasos)
    reproductor.pasos = pasos
    reproductor.grupos = (
        GrupoReproductor("Inicio", "", "inicial", (0,)),
        GrupoReproductor("Final", "", "final", (1,)),
    )
    reproductor.indice_actual = 0
    reproductor.tarjeta = SimpleNamespace(is_deleted=False)
    reproductor.etiqueta_indice = _ControlPrueba()
    reproductor.chip = _ControlPrueba()
    reproductor.fase = _ControlPrueba()
    reproductor.progreso = _ControlPrueba()
    reproductor.slider = _ControlPrueba(0)
    reproductor.explicacion = _ControlPrueba()
    reproductor.contenedor_glosa = _ControlPrueba()
    reproductor.contenedor_cuerpo = _ControlPrueba()
    reproductor.al_explicar = None
    reproductor.id_tarjeta = "step-card-prueba"
    pintados = []
    reproductor.renderizar_cuerpo = lambda paso, contenedor: pintados.append(
        (paso.indice, contenedor.limpiezas)
    )
    return reproductor, pintados


def test_etiqueta_variable_html_convierte_subindices_y_escapa_texto():
    """Convierte nombres con subíndice y escapa etiquetas HTML arbitrarias."""
    assert etiqueta_variable_html("x1") == "x<sub>1</sub>"
    assert etiqueta_variable_html("x_1") == "x<sub>1</sub>"
    assert etiqueta_variable_html("c_2") == "c<sub>2</sub>"
    assert etiqueta_variable_html("alpha") == "alpha"
    assert etiqueta_variable_html("<b>") == "&lt;b&gt;"


def test_tabla_aumentada_admite_bloque_derecho_de_una_columna():
    """Genera etiquetas separadas y un ancho derecho distinto al izquierdo."""
    matriz = Matrix(2, 3, [[1, 2, 5], [3, 4, 6]])
    esperado = (
        '<div class="inv-scroll"><table class="inv-table"><thead><tr>'
        "<th class='row-label'></th><th>x<sub>1</sub></th><th>x<sub>2</sub></th>"
        "<th class='sep-left'>b</th></tr></thead><tbody>"
        "<tr><th class='row-label'>F1</th><td>1</td><td>2</td><td class=\"sep-left\">5</td></tr>"
        "<tr><th class='row-label'>F2</th><td>3</td><td>4</td><td class=\"sep-left\">6</td></tr>"
        "</tbody></table></div>"
    )
    assert html_tabla_aumentada(
        matriz, 2, etiquetas_izq=("x1", "x_2"), etiquetas_der=("b",)
    ) == esperado


def test_catalogo_y_hoja_nueva_definen_todos_los_tipos():
    """Comprueba que cada tipo disponible tenga estilo declarado."""
    ruta_css = Path("src/frontend/assets/css/reproductor_pasos.css")
    estilos = ruta_css.read_text(encoding="utf-8")
    tipos_esperados = {
        "inicial", "intercambio", "pivote", "eliminacion", "normalizacion", "otro", "final",
        "planteamiento", "sustitucion", "verificacion", "operacion", "componente", "ajuste",
        "expansion", "division", "lectura", "decodificacion", "construccion", "resultado",
    }
    assert set(CATALOGO_TIPOS) == tipos_esperados
    assert all(f".chip-{tipo}" in estilos for tipo in tipos_esperados)


def test_assets_compartidos_se_enlazan_y_destello_deja_el_script_anterior():
    """Confirma la carga global de assets y la eliminación del nombre antiguo."""
    cabecera = Path("src/frontend/theme.py").read_text(encoding="utf-8")
    script = Path("src/frontend/assets/js/reproductor_pasos.js").read_text(encoding="utf-8")
    script_matriz = Path("src/frontend/assets/js/square_matrix.js").read_text(encoding="utf-8")
    assert "/assets/css/reproductor_pasos.css" in cabecera
    assert "/assets/js/reproductor_pasos.js" in cabecera
    assert "window.scalarisPasos =" in script
    assert "revelar(id, texto)" in script
    assert "destellar(id)" in script
    assert "flashStepCard" not in script_matriz


def test_velocidades_y_renderizado_latex_conservan_contrato(monkeypatch):
    """Comprueba los intervalos fijos y la composición segura de bloques MathJax."""
    html_renderizado = []
    llamadas_javascript = []
    monkeypatch.setattr(cuerpos.ui, "html", html_renderizado.append)
    monkeypatch.setattr(cuerpos.ui, "run_javascript", llamadas_javascript.append)
    cuerpos.render_latex("x < 1")
    assert VELOCIDADES_AUTOREPRODUCCION == {"Lenta": 1.2, "Normal": 0.6, "Rápida": 0.2}
    assert len(html_renderizado) == 1
    assert 'class="math-scroll-container math-label"' in html_renderizado[0]
    assert "$$ x &lt; 1 $$" in html_renderizado[0]
    assert len(llamadas_javascript) == 1
    assert llamadas_javascript[0].startswith('typesetMathWhenReady(["repro-math-')


def test_adaptador_inversa_preserva_grupos_datos_y_paso_final():
    """Verifica que el adaptador conserva referencias y metadatos de Glosa."""
    resultado = InverseOpsController.process_inverse('{"n":2,"data":[[1,2],[3,4]]}')
    pasos, grupos = adaptar_pasos_inversa(resultado)
    assert isinstance(pasos[0], PasoReproductor)
    assert isinstance(grupos[0], GrupoReproductor)
    assert pasos[-1].tipo == "final"
    assert pasos[-1].cuerpo.paso is resultado["steps"][-1]
    assert pasos[-1].meta_explicar == {
        "kind": resultado["steps"][-1]["kind"],
        "op": resultado["steps"][-1]["description"],
    }
    assert grupos[1].indices_pasos == (1, 2, 3)


def test_detener_elimina_timer_y_restaura_el_control():
    """Cancela el timer de una instancia sin depender de un cliente UI."""
    class TimerPrueba:
        def __init__(self):
            self.is_deleted = False
            self.active = True

        def delete(self):
            self.is_deleted = True

    reproductor = ReproductorPasos.__new__(ReproductorPasos)
    reproductor.timer = TimerPrueba()
    reproductor.boton_reproducir = SimpleNamespace(
        is_deleted=False, props=lambda valor: setattr(reproductor, "icono", valor)
    )
    timer = reproductor.timer
    reproductor.detener()
    assert timer.is_deleted
    assert not timer.active
    assert reproductor.timer is None
    assert reproductor.icono == "icon=play_arrow"


def test_tabla_aumentada_de_50_por_50_usa_formato_compacto():
    """Verifica una tabla aumentada de dimensión máxima y valores fraccionarios."""
    datos = [
        [Fraction(1, 2) if columna % 2 else fila + 1 for columna in range(100)]
        for fila in range(50)
    ]
    tabla = html_tabla_aumentada(Matrix(50, 100, datos), 50)
    assert 'class="inv-table compact"' in tabla
    assert 'class="inv-frac"' not in tabla
    assert tabla.count("<tr") == 51


def test_ir_a_actualiza_el_estado_y_limpia_el_cuerpo(monkeypatch):
    """Comprueba la navegación acotada y el contrato de renderizado del cuerpo."""
    reproductor, pintados = _crear_reproductor_prueba()
    javascript = []
    monkeypatch.setattr(modulo_reproductor.ui, "run_javascript", javascript.append)
    reproductor.ir_a(20)
    assert reproductor.indice_actual == 1
    assert reproductor.etiqueta_indice.texto == "Paso 2 de 2"
    assert reproductor.fase.texto == "Final"
    assert reproductor.progreso.value == 1
    assert reproductor.slider.value == 1
    assert pintados == [(1, 1)]
    assert len(javascript) == 2
