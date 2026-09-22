from src.backend.solvers.linear_systems.gauss import GaussSolver


class GaussJordanSolver(GaussSolver):
    """Solver para el método de Gauss-Jordan.

    Hereda solve() de GaussSolver. La única diferencia es FULL_REDUCTION=True,
    que hace que _eliminate() elimine tanto arriba como abajo del pivote
    (forma escalonada reducida).
    """
    FULL_REDUCTION = True