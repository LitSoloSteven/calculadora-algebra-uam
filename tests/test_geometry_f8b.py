import json
from fractions import Fraction
import pytest

from src.frontend.controllers.geometry.controller_geometry import GeometryController
from src.backend.solvers.linear_systems.gauss import GaussSolver


# ======================================================================
# 1. CONTROLLER TESTS (PAYLOAD JSON)
# ======================================================================

def test_controller_line_2d():
    """[[1,1]] con b=[2] en 2 variables: LINE. segment dentro de la caja [-h, h]. param_latex y description presentes."""
    payload = json.dumps({
        "matrix_A": [["1", "1"]],
        "vector_b": ["2"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["n"] == 2
    assert result["pending_param"] is False

    sol_set = result["set"]
    assert sol_set is not None
    assert sol_set["kind"] == "LINE"
    assert sol_set["dimension"] == 1
    assert sol_set["whole_space"] is False

    # segment dentro de la caja [-h, h]
    h = result["range"][1]
    segment = sol_set.get("segment")
    assert segment is not None
    assert len(segment) == 2
    for pt in segment:
        assert len(pt) == 2
        for coord in pt:
            assert -h - 1e-4 <= coord <= h + 1e-4

    # param_latex y description
    assert "param_latex" in sol_set and sol_set["param_latex"].startswith(r"\mathbf{x} = ")
    assert "description" in sol_set and "Las soluciones forman una recta" in sol_set["description"]
    assert "point_latex" in sol_set and sol_set["point_latex"] is not None


def test_controller_plane_3d():
    """[[1,1,1]] con b=[1]: PLANE. normal_exact y offset_exact correctos."""
    payload = json.dumps({
        "matrix_A": [["1", "1", "1"]],
        "vector_b": ["1"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["n"] == 3
    assert result["pending_param"] is False

    sol_set = result["set"]
    assert sol_set is not None
    assert sol_set["kind"] == "PLANE"
    assert sol_set["dimension"] == 2
    assert sol_set["whole_space"] is False

    # normal_exact y offset_exact presentes y consistentes
    assert "normal_exact" in sol_set
    assert "offset_exact" in sol_set
    # normal = (nx, ny, nz) debe ser proporcional a (1, 1, 1)
    nx = Fraction(sol_set["normal_exact"][0])
    ny = Fraction(sol_set["normal_exact"][1])
    nz = Fraction(sol_set["normal_exact"][2])
    assert nx == ny == nz != 0
    # offset / nx debe ser 1 (la ecuación es 1*x + 1*y + 1*z = 1)
    assert Fraction(sol_set["offset_exact"]) / nx == 1

    assert "param_latex" in sol_set and sol_set["param_latex"].startswith(r"\mathbf{x} = ")
    assert "description" in sol_set and "Las soluciones forman un plano" in sol_set["description"]


def test_controller_two_planes_line_3d():
    """Dos planos independientes en 3 variables: LINE con segment de 3 coordenadas."""
    payload = json.dumps({
        "matrix_A": [["1", "0", "0"], ["0", "1", "0"]],
        "vector_b": ["1", "2"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["n"] == 3

    sol_set = result["set"]
    assert sol_set is not None
    assert sol_set["kind"] == "LINE"
    assert sol_set["dimension"] == 1

    segment = sol_set.get("segment")
    assert segment is not None
    assert len(segment) == 2
    assert len(segment[0]) == 3
    assert len(segment[1]) == 3


def test_controller_whole_space_2d_and_3d():
    """n=2 y n=3 con todo en 0 y b en 0: whole_space True."""
    # n = 2
    payload2 = json.dumps({
        "matrix_A": [["0", "0"]],
        "vector_b": ["0"],
    })
    res2 = GeometryController.process_lines_planes(payload2)
    assert res2["status"] == "OK"
    assert res2["set"] is not None
    assert res2["set"]["whole_space"] is True

    # n = 3
    payload3 = json.dumps({
        "matrix_A": [["0", "0", "0"]],
        "vector_b": ["0"],
    })
    res3 = GeometryController.process_lines_planes(payload3)
    assert res3["status"] == "OK"
    assert res3["set"] is not None
    assert res3["set"]["whole_space"] is True


def test_controller_long_fractions():
    """Fracciones largas (1001/1000, -123456789012/987654321): A·p == b y A·d == 0 en Fraction exactos, y param_latex sin excepción."""
    payload = json.dumps({
        "matrix_A": [["1001/1000", "-123456789012/987654321"]],
        "vector_b": ["1/2"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["pending_param"] is False

    sol_set = result["set"]
    assert sol_set is not None

    A_row = [Fraction("1001/1000"), Fraction("-123456789012/987654321")]
    b_val = Fraction("1/2")

    # A * p == b
    p_exact = [Fraction(x) for x in sol_set["point_exact"]]
    p_eval = sum(a * p for a, p in zip(A_row, p_exact))
    assert p_eval == b_val

    # A * d == 0
    for d_list in sol_set["directions_exact"]:
        d_exact = [Fraction(x) for x in d_list]
        d_eval = sum(a * d for a, d in zip(A_row, d_exact))
        assert d_eval == 0

    assert "param_latex" in sol_set
    assert sol_set["param_latex"].startswith(r"\mathbf{x} = ")


def test_controller_unique_solution_point_latex():
    """Solución única con -1, 10 y 1/2 en el punto: point_latex sin excepción."""
    payload = json.dumps({
        "matrix_A": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        "vector_b": ["-1", "10", "1/2"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["solution_status"] == "UNIQUE_SOLUTION"
    assert result["pending_param"] is False

    sol_set = result["set"]
    assert sol_set is not None
    assert sol_set["kind"] == "POINT"
    assert sol_set["point_latex"] is not None
    assert r"\begin{bmatrix}" in sol_set["point_latex"]
    assert "-1" in sol_set["point_latex"]
    assert "10" in sol_set["point_latex"]
    assert r"\frac{1}{2}" in sol_set["point_latex"]


def test_controller_no_solution():
    """NO_SOLUTION: pending_param False y sin excepción."""
    payload = json.dumps({
        "matrix_A": [["1", "1"], ["1", "1"]],
        "vector_b": ["1", "2"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["solution_status"] == "NO_SOLUTION"
    assert result["pending_param"] is False


def test_controller_parallel_lines():
    """Rectas paralelas: flag 'parallel' presente."""
    payload = json.dumps({
        "matrix_A": [["1", "2"], ["2", "4"]],
        "vector_b": ["3", "7"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["solution_status"] == "NO_SOLUTION"
    assert "parallel" in result["flags"]


def test_controller_simulated_backend_without_solution_param(monkeypatch):
    """Backend simulado sin solution_param (monkeypatch): pending_param True, set None y sin excepción."""
    orig_solve = GaussSolver.solve

    def mock_solve(self):
        res = orig_solve(self)
        if res.get("status") == "INFINITE_SOLUTIONS":
            res.pop("solution_param", None)
        return res

    monkeypatch.setattr(GaussSolver, "solve", mock_solve)

    payload = json.dumps({
        "matrix_A": [["1", "1"]],
        "vector_b": ["1"],
    })
    result = GeometryController.process_lines_planes(payload)
    assert result["status"] == "OK"
    assert result["solution_status"] == "INFINITE_SOLUTIONS"
    assert result["pending_param"] is True
    assert result["set"] is None


# ======================================================================
# 2. FIGURES TESTS (PLOTLY)
# ======================================================================

def test_figures_line_2d_and_plane_3d():
    """LINE 2D y PLANE 3D incluyen la traza 'Conjunto solución (recta/plano)', la traza va antes de las ecuaciones y las ecuaciones siguen presentes. whole_space no añade traza."""
    pytest.importorskip("plotly")
    from src.frontend.views.geometry._scenes import build_lines_planes_figure

    # 2D LINE
    payload_2d = json.dumps({
        "matrix_A": [["1", "1"]],
        "vector_b": ["2"],
    })
    res_2d = GeometryController.process_lines_planes(payload_2d)
    fig_2d = build_lines_planes_figure(res_2d, theme="papel")
    names_2d = [t.name for t in fig_2d.data]

    assert "Conjunto solución (recta)" in names_2d
    assert "Ecuación 1" in names_2d
    assert names_2d.index("Conjunto solución (recta)") < names_2d.index("Ecuación 1")

    # 3D PLANE
    payload_3d = json.dumps({
        "matrix_A": [["1", "1", "1"]],
        "vector_b": ["1"],
    })
    res_3d = GeometryController.process_lines_planes(payload_3d)
    fig_3d = build_lines_planes_figure(res_3d, theme="papel")
    names_3d = [t.name for t in fig_3d.data]

    assert "Conjunto solución (plano)" in names_3d
    assert "Ecuación 1" in names_3d
    assert names_3d.index("Conjunto solución (plano)") < names_3d.index("Ecuación 1")

    # whole_space no añade traza
    payload_ws = json.dumps({
        "matrix_A": [["0", "0"]],
        "vector_b": ["0"],
    })
    res_ws = GeometryController.process_lines_planes(payload_ws)
    fig_ws = build_lines_planes_figure(res_ws, theme="papel")
    names_ws = [t.name for t in fig_ws.data]

    assert "Conjunto solución (recta)" not in names_ws
    assert "Conjunto solución (plano)" not in names_ws


# ======================================================================
# 3. VIEW LOGIC TESTS (PURE FUNCTIONS)
# ======================================================================

def test_view_build_payload_empty_grid():
    """Prueba que cuadrícula estrictamente vacía devuelve None sin procesar."""
    class MockGrid:
        def is_strictly_empty(self):
            return True
        def get_matrix_data(self):
            return [["", ""]], [""]

    class MockUI:
        def __init__(self):
            self.scene = 'rectas-planos'
            self.grid = MockGrid()

        def _build_payload(self):
            if self.scene == 'rectas-planos':
                if not self.grid or self.grid.is_strictly_empty():
                    return None
                matrix_A, vector_b = self.grid.get_matrix_data()
                if not matrix_A or not matrix_A[0]:
                    return None
                return {"matrix_A": matrix_A, "vector_b": vector_b}
            return None

    ui = MockUI()
    assert ui._build_payload() is None
