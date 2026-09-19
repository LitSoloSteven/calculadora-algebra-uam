from src.backend.solvers.linear_systems.gauss import GaussSolver


class GaussJordanSolver(GaussSolver):
    """
    Solver para el método de Gauss-Jordan.

    Hereda de GaussSolver y reutiliza la eliminación unificada con
    full_reduction=True, que elimina tanto por encima como por debajo
    del pivote, alcanzando la forma escalonada reducida.
    """

    def solve(self):
        rank, pivot_cols = self._eliminate(full_reduction=True)
        status, message = self._check_system_status(rank)

        if status == "NO_SOLUTION":
            return {
                "status": status,
                "classification": message,
                "message": message,
                "echelon_matrix": self.matrix,
                "solution": None,
                "steps": self.steps,
                "back_substitution_steps": []
            }

        solution, back_steps = self._back_substitute(pivot_cols)

        return {
            "status": status,
            "classification": message,
            "message": message,
            "echelon_matrix": self.matrix,
            "solution": solution,
            "steps": self.steps,
            "back_substitution_steps": back_steps
        }