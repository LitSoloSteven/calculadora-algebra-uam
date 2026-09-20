import pytest
import json
from fractions import Fraction
from src.backend.utils.parsers import SystemParser
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator
from src.backend.models.matrix import Matrix
from src.backend.utils.formatters import format_fraction_str, number_to_latex
from src.frontend.controllers.linear_systems.controller_gauss import MatrixController
from src.frontend.controllers.linear_systems.controller_gauss_jordan import GaussJordanController

def test_parser_implicit_mul_and_disjoint():
    # "2*x + y = 3\nx - y = 0" parsea bien
    ok, mat, vars, msg = SystemParser.parse_system("2*x + y = 3\nx - y = 0")
    assert ok is True
    
    # "x*y = 3" y "2x*y = 3" fallan
    ok, mat, vars, msg = SystemParser.parse_system("x*y = 3")
    assert ok is False
    ok, mat, vars, msg = SystemParser.parse_system("2x*y = 3")
    assert ok is False
    
    # "x + y = 1\n0 = 5" parsea bien
    ok, mat, vars, msg = SystemParser.parse_system("x + y = 1\n0 = 5")
    assert ok is True

def test_evaluator_ab_equivale_a_por_b():
    evaluator = MatrixExpressionEvaluator()
    matrices = {
        "A": Matrix(2, 2, [[1, 2], [3, 4]]),
        "B": Matrix(2, 2, [[5, 6], [7, 8]])
    }
    # AB equivale a A*B
    res1 = evaluator.evaluate("AB", matrices)
    res2 = evaluator.evaluate("A*B", matrices)
    assert res1["result_matrix"].data == res2["result_matrix"].data
    
    # evaluate("A+B") devuelve final_variable == "T_{1}"
    res3 = evaluator.evaluate("A+B", matrices)
    assert res3["final_variable"] == "T_{1}"

def test_formatters_precision_2_1001():
    assert format_fraction_str(Fraction(1, 1001)) == "1/1001"
    assert number_to_latex(Fraction(2, 1001)) == r"\frac{2}{1001}"

def test_controllers_error_on_non_numeric():
    payload = json.dumps({
        "matrix_A": [["1", "no_es_numero"], ["3", "4"]],
        "vector_b": ["1", "2"],
        "variables": ["x", "y"]
    })
    
    res_gauss = json.loads(MatrixController.process_system(payload))
    assert res_gauss["status"] == "ERROR"
    
    res_jordan = json.loads(GaussJordanController.process_system(payload))
    assert res_jordan["status"] == "ERROR"
