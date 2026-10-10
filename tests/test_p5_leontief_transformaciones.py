"""Tests de P5 — Modelo de Leontief y Transformaciones Lineales (LIT-8).

Cobertura:
  Backend:
    - LeontiefSolver: M=I−C, multiplicador, Hawkins-Simon (viable e inviable),
      vector de producción, análisis sectorial.
    - LinearTransformationSolver: ker(T), Im(T), rango, nulidad, inyectividad,
      sobreyectividad, Teorema de la Dimensión.
  Controladores:
    - LeontiefController.procesar: payload válido, payload inválido.
    - TransformacionesController.procesar: payload válido, matriz no cuadrada,
      payload vacío.
"""
import json
import pytest
from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.leontief import LeontiefSolver
from src.backend.solvers.matrix_ops.transformations import LinearTransformationSolver
from src.frontend.controllers.matrix_ops.controller_leontief import LeontiefController
from src.frontend.controllers.matrix_ops.controller_transformaciones import TransformacionesController


# ══════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════

def _mat(data: list[list]) -> Matrix:
    """Construye una Matrix desde listas de valores."""
    m = len(data)
    n = len(data[0])
    return Matrix(m, n, [[Fraction(v) for v in row] for row in data])


# ══════════════════════════════════════════════════════════════════════════
# LeontiefSolver — Tests de backend
# ══════════════════════════════════════════════════════════════════════════

class TestLeontiefSolverBasic:
    """Modelo de 2 sectores simple con solución exacta."""

    @pytest.fixture
    def solver(self):
        return LeontiefSolver()

    @pytest.fixture
    def modelo_2_sectores(self, solver):
        # C = [[0.2, 0.3], [0.4, 0.1]]  =>  M = I - C = [[0.8, -0.3], [-0.4, 0.9]]
        C = _mat([[Fraction(1, 5), Fraction(3, 10)],
                  [Fraction(2, 5), Fraction(1, 10)]])
        d = [Fraction(120), Fraction(80)]
        return solver.resolver(C, d, ["Agricultura", "Industria"])

    def test_status_success(self, modelo_2_sectores):
        assert modelo_2_sectores["status"] == "SUCCESS"

    def test_n_sectores(self, modelo_2_sectores):
        assert modelo_2_sectores["n"] == 2

    def test_sectores_nombres(self, modelo_2_sectores):
        assert modelo_2_sectores["sectores"] == ["Agricultura", "Industria"]

    def test_hawkins_simon_viable(self, modelo_2_sectores):
        hs = modelo_2_sectores["hawkins_simon"]
        assert hs["viable"] is True

    def test_hawkins_simon_menores(self, modelo_2_sectores):
        hs = modelo_2_sectores["hawkins_simon"]
        menores = hs["menores"]
        assert len(menores) == 2
        # Δ₁ = 0.8 > 0
        assert menores[0]["positivo"] is True
        # Δ₂ = det(M) = 0.8*0.9 - (-0.3)*(-0.4) = 0.72 - 0.12 = 0.6 > 0
        assert menores[1]["positivo"] is True

    def test_vector_produccion_existente(self, modelo_2_sectores):
        prods = modelo_2_sectores["vector_produccion"]
        assert len(prods) == 2
        # Ambos valores deben ser fracciones no vacías
        for p in prods:
            assert p != "0"

    def test_analisis_sectorial_estructura(self, modelo_2_sectores):
        analisis = modelo_2_sectores["analisis_sectorial"]
        assert len(analisis) == 2
        for fila in analisis:
            assert "sector" in fila
            assert "produccion_total" in fila
            assert "insumos_intermedios" in fila
            assert "demanda_final" in fila
            assert "valor_anadido" in fila

    def test_matrices_latex_presentes(self, modelo_2_sectores):
        assert "matriz_leontief_latex" in modelo_2_sectores
        assert "matriz_multiplicador_latex" in modelo_2_sectores
        assert "\\begin{bmatrix}" in modelo_2_sectores["matriz_leontief_latex"]

    def test_sectores_default_sin_nombres(self, solver):
        C = _mat([[Fraction(1, 5), Fraction(3, 10)],
                  [Fraction(2, 5), Fraction(1, 10)]])
        d = [Fraction(120), Fraction(80)]
        r = solver.resolver(C, d)  # Sin nombres
        assert r["sectores"] == ["Sector 1", "Sector 2"]


class TestLeontiefSolverInviable:
    """Modelo con Hawkins-Simon que falla."""

    @pytest.fixture
    def solver(self):
        return LeontiefSolver()

    @pytest.fixture
    def modelo_inviable(self, solver):
        # Coeficientes > 1 en suma de columnas → economía no viable
        C = _mat([[Fraction(4, 5), Fraction(1, 2)],
                  [Fraction(3, 5), Fraction(9, 10)]])
        d = [Fraction(50), Fraction(50)]
        return solver.resolver(C, d)

    def test_hawkins_simon_no_viable(self, modelo_inviable):
        # Puede ser SINGULAR o SUCCESS con H-S fallando
        r = modelo_inviable
        if r["status"] == "SUCCESS":
            hs = r["hawkins_simon"]
            assert hs["viable"] is False
        else:
            # SINGULAR también es válido
            assert r["status"] in ("SINGULAR", "SUCCESS")

    def test_mensaje_singular_o_hs_negativo(self, modelo_inviable):
        r = modelo_inviable
        if r["status"] == "SINGULAR":
            assert "singular" in r["message"].lower() or "viab" in r["message"].lower()


class TestLeontiefSolverErrores:
    """Casos de error en LeontiefSolver."""

    def test_matriz_no_cuadrada(self):
        solver = LeontiefSolver()
        C = _mat([[1, 0, 0], [0, 1, 0]])  # 2×3
        d = [Fraction(10), Fraction(10)]
        r = solver.resolver(C, d)
        assert r["status"] == "ERROR"
        assert "cuadrada" in r["message"].lower()

    def test_vector_dimension_incorrecta(self):
        solver = LeontiefSolver()
        C = _mat([[Fraction(1, 5), 0], [0, Fraction(1, 5)]])
        d = [Fraction(10)]  # Solo 1 elemento, se esperan 2
        r = solver.resolver(C, d)
        assert r["status"] == "ERROR"

    def test_3_sectores_viables(self):
        solver = LeontiefSolver()
        C = _mat([
            [Fraction(1, 10), Fraction(2, 10), Fraction(1, 10)],
            [Fraction(2, 10), Fraction(3, 10), Fraction(2, 10)],
            [Fraction(1, 10), Fraction(1, 10), Fraction(3, 10)],
        ])
        d = [Fraction(100), Fraction(200), Fraction(150)]
        r = solver.resolver(C, d, ["Agro", "Industria", "Servicios"])
        assert r["status"] == "SUCCESS"
        assert r["hawkins_simon"]["viable"] is True
        assert len(r["analisis_sectorial"]) == 3


# ══════════════════════════════════════════════════════════════════════════
# LinearTransformationSolver — Tests de backend
# ══════════════════════════════════════════════════════════════════════════

class TestTransformacionesIdentidad:
    """T = Id: R² → R² — biyectiva."""

    @pytest.fixture
    def resultado(self):
        solver = LinearTransformationSolver()
        A = _mat([[1, 0], [0, 1]])
        return solver.resolver(A)

    def test_status_success(self, resultado):
        assert resultado["status"] == "SUCCESS"

    def test_rango_2(self, resultado):
        assert resultado["rango"] == 2

    def test_nulidad_0(self, resultado):
        assert resultado["nulidad"] == 0

    def test_inyectiva(self, resultado):
        assert resultado["es_inyectiva"] is True

    def test_sobreyectiva(self, resultado):
        assert resultado["es_sobreyectiva"] is True

    def test_nucleo_trivial(self, resultado):
        assert resultado["base_nucleo"] == []

    def test_imagen_2_vectores(self, resultado):
        assert len(resultado["base_imagen"]) == 2

    def test_teorema_dimension(self, resultado):
        assert "2 + 0 = 2" in resultado["teorema_dimension"]


class TestTransformacionesProyeccion:
    """T = proyección sobre eje x: R² → R² — ni inyectiva ni sobreyectiva en rango."""

    @pytest.fixture
    def resultado(self):
        solver = LinearTransformationSolver()
        A = _mat([[1, 0], [0, 0]])
        return solver.resolver(A)

    def test_rango_1(self, resultado):
        assert resultado["rango"] == 1

    def test_nulidad_1(self, resultado):
        assert resultado["nulidad"] == 1

    def test_no_inyectiva(self, resultado):
        assert resultado["es_inyectiva"] is False

    def test_nucleo_dimension_1(self, resultado):
        assert len(resultado["base_nucleo"]) == 1

    def test_teorema_dimension(self, resultado):
        assert "1 + 1 = 2" in resultado["teorema_dimension"]

    def test_nucleo_vector_correcto(self, resultado):
        # ker(T) = span{(0,1)^T}: el vector debe tener 0 en pos 0 y 1 en pos 1
        vec = resultado["base_nucleo"][0]["vector"]
        assert vec[0] == "0"
        assert vec[1] == "1"


class TestTransformacionesR2aR3:
    """Embedding R² → R³: inyectiva, no sobreyectiva."""

    @pytest.fixture
    def resultado(self):
        solver = LinearTransformationSolver()
        A = _mat([[1, 0], [0, 1], [0, 0]])
        return solver.resolver(A)

    def test_rango_2(self, resultado):
        assert resultado["rango"] == 2

    def test_nulidad_0(self, resultado):
        assert resultado["nulidad"] == 0

    def test_inyectiva(self, resultado):
        assert resultado["es_inyectiva"] is True

    def test_no_sobreyectiva(self, resultado):
        assert resultado["es_sobreyectiva"] is False

    def test_m_n(self, resultado):
        assert resultado["m"] == 3
        assert resultado["n"] == 2

    def test_teorema_dimension(self, resultado):
        assert "2 + 0 = 2" in resultado["teorema_dimension"]


class TestTransformacionesR3aR2:
    """Proyección R³ → R²: sobreyectiva, no inyectiva."""

    @pytest.fixture
    def resultado(self):
        solver = LinearTransformationSolver()
        A = _mat([[1, 0, 0], [0, 1, 0]])
        return solver.resolver(A)

    def test_rango_2(self, resultado):
        assert resultado["rango"] == 2

    def test_nulidad_1(self, resultado):
        assert resultado["nulidad"] == 1

    def test_no_inyectiva(self, resultado):
        assert resultado["es_inyectiva"] is False

    def test_sobreyectiva(self, resultado):
        assert resultado["es_sobreyectiva"] is True

    def test_teorema_dimension(self, resultado):
        assert "2 + 1 = 3" in resultado["teorema_dimension"]

    def test_nucleo_vector_e3(self, resultado):
        vec = resultado["base_nucleo"][0]["vector"]
        # ker: span{e3} = (0, 0, 1)^T
        assert vec[0] == "0"
        assert vec[1] == "0"
        assert vec[2] == "1"


class TestTransformacionesNulaBiyectiva:
    """Transformación nula 2×2 — rango 0."""

    def test_transformacion_nula(self):
        solver = LinearTransformationSolver()
        A = _mat([[0, 0], [0, 0]])
        r = solver.resolver(A)
        assert r["status"] == "SUCCESS"
        assert r["rango"] == 0
        assert r["nulidad"] == 2
        assert r["es_inyectiva"] is False
        assert r["es_sobreyectiva"] is False

    def test_callout_convencion_presente(self):
        solver = LinearTransformationSolver()
        A = _mat([[1, 0], [0, 1]])
        r = solver.resolver(A)
        assert "callout_convencion" in r
        assert len(r["callout_convencion"]) > 20


# ══════════════════════════════════════════════════════════════════════════
# LeontiefController — Tests de controlador
# ══════════════════════════════════════════════════════════════════════════

class TestLeontiefController:

    def test_payload_valido_2_sectores(self):
        payload = json.dumps({
            "C": [["0.2", "0.3"], ["0.4", "0.1"]],
            "d": ["120", "80"],
            "sectores": ["Agricultura", "Industria"],
        })
        respuesta_str = LeontiefController.procesar(payload)
        respuesta = json.loads(respuesta_str)
        assert respuesta["status"] == "SUCCESS"
        assert respuesta["n"] == 2

    def test_payload_sin_C(self):
        payload = json.dumps({"d": ["100", "200"]})
        r = json.loads(LeontiefController.procesar(payload))
        assert r["status"] == "ERROR"

    def test_payload_sin_d(self):
        payload = json.dumps({"C": [["0.2", "0.3"], ["0.4", "0.1"]]})
        r = json.loads(LeontiefController.procesar(payload))
        assert r["status"] == "ERROR"

    def test_json_invalido(self):
        r = json.loads(LeontiefController.procesar("{broken json"))
        assert r["status"] == "ERROR"

    def test_celda_invalida(self):
        payload = json.dumps({
            "C": [["abc", "0"], ["0", "0.1"]],
            "d": ["100", "100"],
        })
        r = json.loads(LeontiefController.procesar(payload))
        assert r["status"] == "ERROR"

    def test_alias_process(self):
        # El alias en inglés debe funcionar igual
        payload = json.dumps({
            "C": [["0.2", "0.3"], ["0.4", "0.1"]],
            "d": ["120", "80"],
        })
        r = json.loads(LeontiefController.process(payload))
        assert r["status"] == "SUCCESS"

    def test_hawkins_simon_en_respuesta(self):
        payload = json.dumps({
            "C": [["0.2", "0.3"], ["0.4", "0.1"]],
            "d": ["120", "80"],
        })
        r = json.loads(LeontiefController.procesar(payload))
        assert "hawkins_simon" in r
        assert "viable" in r["hawkins_simon"]

    def test_analisis_sectorial_en_respuesta(self):
        payload = json.dumps({
            "C": [["0.2", "0.3"], ["0.4", "0.1"]],
            "d": ["120", "80"],
            "sectores": ["A", "B"],
        })
        r = json.loads(LeontiefController.procesar(payload))
        analisis = r.get("analisis_sectorial", [])
        assert len(analisis) == 2
        assert analisis[0]["sector"] == "A"


# ══════════════════════════════════════════════════════════════════════════
# TransformacionesController — Tests de controlador
# ══════════════════════════════════════════════════════════════════════════

class TestTransformacionesController:

    def test_identidad_2x2(self):
        payload = json.dumps({"A": [["1", "0"], ["0", "1"]]})
        r = json.loads(TransformacionesController.procesar(payload))
        assert r["status"] == "SUCCESS"
        assert r["rango"] == 2
        assert r["nulidad"] == 0

    def test_proyeccion(self):
        payload = json.dumps({"A": [["1", "0"], ["0", "0"]]})
        r = json.loads(TransformacionesController.procesar(payload))
        assert r["status"] == "SUCCESS"
        assert r["rango"] == 1
        assert r["nulidad"] == 1

    def test_payload_sin_A(self):
        r = json.loads(TransformacionesController.procesar(json.dumps({})))
        assert r["status"] == "ERROR"

    def test_json_invalido(self):
        r = json.loads(TransformacionesController.procesar("{bad"))
        assert r["status"] == "ERROR"

    def test_celda_invalida(self):
        payload = json.dumps({"A": [["xyz", "0"], ["0", "1"]]})
        r = json.loads(TransformacionesController.procesar(payload))
        assert r["status"] == "ERROR"

    def test_alias_process(self):
        payload = json.dumps({"A": [["1", "0"], ["0", "1"]]})
        r = json.loads(TransformacionesController.process(payload))
        assert r["status"] == "SUCCESS"

    def test_nombres_variables_propagados(self):
        payload = json.dumps({
            "A": [["1", "0"], ["0", "1"]],
            "variables": ["u", "v"],
        })
        r = json.loads(TransformacionesController.procesar(payload))
        assert r["status"] == "SUCCESS"

    def test_m_distinto_n(self):
        # R² → R³
        payload = json.dumps({"A": [["1", "0"], ["0", "1"], ["0", "0"]]})
        r = json.loads(TransformacionesController.procesar(payload))
        assert r["status"] == "SUCCESS"
        assert r["m"] == 3
        assert r["n"] == 2

    def test_callout_presente_en_respuesta(self):
        payload = json.dumps({"A": [["1", "0"], ["0", "1"]]})
        r = json.loads(TransformacionesController.procesar(payload))
        assert "callout_convencion" in r

    def test_conclusiones_biyectividad(self):
        payload = json.dumps({"A": [["1", "0"], ["0", "1"]]})
        r = json.loads(TransformacionesController.procesar(payload))
        conclusiones = r.get("conclusiones", {})
        assert "biyectividad" in conclusiones
        assert conclusiones["biyectividad"] is not None
        assert "BIYECTIVA" in conclusiones["biyectividad"]

    def test_base_nucleo_correcto(self):
        # Proyección: ker debería tener span{e2}
        payload = json.dumps({"A": [["1", "0"], ["0", "0"]]})
        r = json.loads(TransformacionesController.procesar(payload))
        nucleo = r.get("base_nucleo", [])
        assert len(nucleo) == 1
        vec = nucleo[0]["vector"]
        assert vec[0] == "0"
        assert vec[1] == "1"

    def test_rotacion_90(self):
        # Rotación 90°: biyectiva
        payload = json.dumps({"A": [["0", "-1"], ["1", "0"]]})
        r = json.loads(TransformacionesController.procesar(payload))
        assert r["status"] == "SUCCESS"
        assert r["rango"] == 2
        assert r["nulidad"] == 0
        assert r["es_inyectiva"] is True
        assert r["es_sobreyectiva"] is True
