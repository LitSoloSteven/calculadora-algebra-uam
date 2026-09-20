"""Tests del helper compartido de controllers de sistemas lineales.

Verifica que `_shared.parse_payload` y `_shared.validate_and_build_augmented`
produzcan los errores esperados en los casos borde, con el formato y las
coordenadas exactas que el frontend consume.

Estos tests son de regresión: si se cambia el helper, deben seguir pasando
(o actualizarse de forma consciente), porque ambos controllers dependen de él.
"""
import json
from fractions import Fraction

from src.frontend.controllers.linear_systems._shared import (
    parse_payload,
    validate_and_build_augmented,
)


class TestParsePayload:
    def test_malformed_json_reports_line_and_column(self):
        data, err = parse_payload('{"a": }')
        assert data is None
        parsed = json.loads(err)
        assert parsed["status"] == "error"
        assert "malformado" in parsed["message"].lower()

    def test_non_dict_json_rejected(self):
        # JSON válido pero es una lista, no un objeto.
        data, err = parse_payload("[1, 2, 3]")
        assert data is None
        parsed = json.loads(err)
        assert parsed["status"] == "error"
        assert "objeto JSON" in parsed["message"]

    def test_valid_dict_accepted(self):
        payload = json.dumps({"matrix_A": [[1]], "vector_b": [2]})
        data, err = parse_payload(payload)
        assert err is None
        assert data == {"matrix_A": [[1]], "vector_b": [2]}


class TestValidateAndBuildAugmented:
    def test_empty_matrix_rejected(self):
        matrix, A, b, m, n, err = validate_and_build_augmented(
            {"matrix_A": [], "vector_b": []}
        )
        assert matrix is None and A is None and b is None
        parsed = json.loads(err)
        assert "vacía" in parsed["message"]

    def test_non_list_row_rejected(self):
        matrix, A, b, m, n, err = validate_and_build_augmented(
            {"matrix_A": ["no es lista"], "vector_b": [1]}
        )
        assert matrix is None
        parsed = json.loads(err)
        assert "lista de filas" in parsed["message"]

    def test_zero_columns_rejected(self):
        matrix, A, b, m, n, err = validate_and_build_augmented(
            {"matrix_A": [[]], "vector_b": [1]}
        )
        assert matrix is None
        parsed = json.loads(err)
        assert "0 columnas" in parsed["message"]

    def test_mismatched_b_length_rejected(self):
        matrix, A, b, m, n, err = validate_and_build_augmented({
            "matrix_A": [[1, 2], [3, 4]],
            "vector_b": [5],  # falta uno
        })
        assert matrix is None
        parsed = json.loads(err)
        assert "vector b tiene 1" in parsed["message"]
        assert "se esperaban 2" in parsed["message"]

    def test_cell_error_reports_coordinates(self):
        matrix, A, b, m, n, err = validate_and_build_augmented({
            "matrix_A": [[1, "no_numerico"], [3, 4]],
            "vector_b": [5, 6],
        })
        assert matrix is None
        parsed = json.loads(err)
        assert "A[1,2]" in parsed["message"]

    def test_b_error_reports_index(self):
        matrix, A, b, m, n, err = validate_and_build_augmented({
            "matrix_A": [[1, 2]],
            "vector_b": ["no_numerico"],
        })
        assert matrix is None
        parsed = json.loads(err)
        assert "b[1]" in parsed["message"]

    def test_fraction_denominator_1001_preserved(self):
        """Regresión de B1: denominadores > 1000 no se truncan."""
        matrix, A, b, m, n, err = validate_and_build_augmented({
            "matrix_A": [["1/1001"]],
            "vector_b": ["1"],
        })
        assert err is None
        assert A[0][0] == Fraction(1, 1001)
        assert b[0] == Fraction(1, 1)
        assert matrix.get(0, 0) == Fraction(1, 1001)
        assert matrix.get(0, 1) == Fraction(1, 1)

    def test_returns_m_and_n_correctly(self):
        matrix, A, b, m, n, err = validate_and_build_augmented({
            "matrix_A": [[1, 2, 3], [4, 5, 6]],
            "vector_b": [7, 8],
        })
        assert err is None
        assert m == 2
        assert n == 3
        assert matrix.rows == 2
        assert matrix.cols == 4  # n + 1 por la columna b

    def test_empty_cell_treated_as_zero(self):
        """Celdas None o strings vacíos se tratan como 0 (comportamiento del frontend)."""
        matrix, A, b, m, n, err = validate_and_build_augmented({
            "matrix_A": [[None, ""]],
            "vector_b": [5],
        })
        assert err is None
        assert A[0][0] == Fraction(0)
        assert A[0][1] == Fraction(0)