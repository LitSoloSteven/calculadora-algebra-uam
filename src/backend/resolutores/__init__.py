"""Paquete central de resolutores algebraicos con precision exacta."""

from src.backend.resolutores.operaciones_matrices import (
    EvaluadorExpresionesMatriciales,
    ResolutorDeterminante,
    ResolutorInversa,
    ResolutorModeloLeontief,
    ResolutorOperacionesMatrices,
    ResolutorTransformacionesLineales,
)
from src.backend.resolutores.operaciones_vectores import (
    BaseResolutorVectores,
    ResolutorCombinacionLineal,
    ResolutorOperacionesVectores,
)
from src.backend.resolutores.sistemas_lineales import (
    ResolutorGauss,
    ResolutorGaussJordan,
)
from src.backend.resolutores.sistemas_numericos import (
    CalculadoraRomana,
    ConversorBases,
    ErrorNumeroRomano,
    ResultadoOperacionRomana,
    entero_a_romano,
    romano_a_entero,
)
from src.backend.resolutores.trazado import TrazadorPasos

__all__ = [
    "TrazadorPasos",
    "ResolutorGauss",
    "ResolutorGaussJordan",
    "ResolutorOperacionesMatrices",
    "ResolutorDeterminante",
    "ResolutorInversa",
    "EvaluadorExpresionesMatriciales",
    "ResolutorTransformacionesLineales",
    "ResolutorModeloLeontief",
    "BaseResolutorVectores",
    "ResolutorOperacionesVectores",
    "ResolutorCombinacionLineal",
    "ConversorBases",
    "CalculadoraRomana",
    "ErrorNumeroRomano",
    "ResultadoOperacionRomana",
    "entero_a_romano",
    "romano_a_entero",
]
