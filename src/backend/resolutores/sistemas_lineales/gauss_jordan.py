"""Resolutor de Gauss-Jordan con forma escalonada reducida y aritmetica exacta."""

from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss


class ResolutorGaussJordan(ResolutorGauss):
    """Resuelve sistemas lineales reduciendo tanto arriba como abajo de cada pivote."""

    REDUCCION_COMPLETA: bool = True
