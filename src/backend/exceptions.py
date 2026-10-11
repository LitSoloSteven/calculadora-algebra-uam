"""Puente de excepciones heredadas para compatibilidad con pruebas."""

from src.backend.excepciones import (
    AlgebraLinealError,
    ErrorDatosMatriz,
    ErrorDiscrepanciaDimension,
    ErrorNumeroInvalido,
    ErrorSistemaSingular,
    ErrorVectorInvalido,
)

MatrixDataError = ErrorDatosMatriz
DimensionMismatchError = ErrorDiscrepanciaDimension
InvalidNumberError = ErrorNumeroInvalido
SingularSystemError = ErrorSistemaSingular
InvalidVectorError = ErrorVectorInvalido