"""Módulo de utilidades matemáticas, formateadores, validadores y reglas."""

from .analizadores import AnalizadorSistema
from .formateadores import (
    formatear_expresion_parametrica,
    formatear_fraccion_str,
    formatear_variable_para_latex,
    numero_a_latex,
)
from .reglas_dominio import (
    validar_datos_transferencia_matriz,
    validar_datos_transferencia_vectores,
    validar_entrada_base,
)
from .utilidades_matematicas import mcd, mcd_lista, mcm, simplificar_fila
from .validadores import (
    ValidadorMatriz,
    validar_dimensiones_multiplicacion,
    validar_mismas_dimensiones,
)
from .verificacion import verificar_solucion

__all__ = [
    "AnalizadorSistema",
    "ValidadorMatriz",
    "formatear_expresion_parametrica",
    "formatear_fraccion_str",
    "formatear_variable_para_latex",
    "mcd",
    "mcd_lista",
    "mcm",
    "numero_a_latex",
    "simplificar_fila",
    "validar_datos_transferencia_matriz",
    "validar_datos_transferencia_vectores",
    "validar_dimensiones_multiplicacion",
    "validar_entrada_base",
    "validar_mismas_dimensiones",
    "verificar_solucion",
]
