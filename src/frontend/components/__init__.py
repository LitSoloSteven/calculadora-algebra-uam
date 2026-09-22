"""Componentes reutilizables de UI de Scalaris."""
from .equation_grid import EquationGrid
from .matrix_capture import MatrixCapturePanel
from .vector_capture import VectorCapturePanel
from .ai_panel import AIPanel
from .calculator import CalculatorPanel
from .navbar import create_navbar

__all__ = [
    "EquationGrid",
    "MatrixCapturePanel",
    "VectorCapturePanel",
    "AIPanel",
    "CalculatorPanel",
    "create_navbar",
]
