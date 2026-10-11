"""Mixin de trazabilidad de pasos para resolutores algebraicos."""

from src.backend.modelos.matriz import Matriz


class TrazadorPasos:
    """Provee almacenamiento y registro de pasos intermedios de resolutores."""

    def __init__(self) -> None:
        """Inicializa la lista vacia de pasos."""
        self.pasos: list[dict] = []

    def _registrar_paso(
        self,
        descripcion: str,
        matriz_actual: Matriz | None = None,
        detalle_latex: str | None = None,
    ) -> None:
        """Registra un paso clonando defensivamente la matriz si esta presente."""
        self.pasos.append({
            "descripcion": descripcion,
            "description": descripcion,
            "matriz": matriz_actual.clonar() if matriz_actual else None,
            "matrix": matriz_actual.clonar() if matriz_actual else None,
            "detalle_latex": detalle_latex,
            "detail_latex": detalle_latex,
        })
