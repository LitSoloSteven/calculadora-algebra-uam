"""Mixin de trazabilidad de pasos para solvers.

Centraliza el contrato de `_log_step` que comparten MatrixOpsSolver,
VectorOpsSolver y LinearCombinationSolver.

GaussSolver queda fuera a propósito: sus steps son {description, matrix}
sin `detail_latex`, y forzarlo al mixin cambiaría el JSON de retorno
(rompería check_dry_refactor y el contrato de Gauss).

Contrato:
  - `self.steps` es list[dict] con claves {description, matrix, detail_latex}.
  - `matrix` se clona defensivamente; `None` se preserva como `None`.
  - `detail_latex` es opcional (default None).
"""
from src.backend.models.matrix import Matrix


class StepTraceMixin:
    """Helpers de trazabilidad compartidos por los solvers modernos."""

    def __init__(self):
        self.steps: list[dict] = []

    def _log_step(
        self,
        description: str,
        current_matrix: Matrix = None,
        detail_latex: str = None,
    ) -> None:
        self.steps.append({
            "description": description,
            "matrix": current_matrix.clone() if current_matrix else None,
            "detail_latex": detail_latex,
        })