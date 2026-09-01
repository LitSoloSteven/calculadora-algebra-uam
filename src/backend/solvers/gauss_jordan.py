from src.backend.solvers.linear_systems import GaussSolver

class GaussJordanSolver(GaussSolver):
    def _eliminate_backward(self, pivot_cols):
        """
        Elimina los elementos por encima de cada pivote,
        dejando la matriz en forma escalonada reducida.
        """
        # Recorremos los pivotes de abajo hacia arriba
        for k in range(len(pivot_cols) - 1, -1, -1):
            pivot_row = k
            pivot_col = pivot_cols[k]
            # Para cada fila por encima del pivote
            for r in range(pivot_row - 1, -1, -1):
                factor = self.matrix.get(r, pivot_col)
                if abs(factor) > self.eps:
                    self.matrix.add_scaled_row(r, pivot_row, -factor)
                    self.matrix.set(r, pivot_col, 0.0)
                    self._log_step(
                        f"Fila {r+1} = Fila {r+1} - ({self._format_factor(factor)}) * Fila {pivot_row+1}",
                        self.matrix
                    )

    def solve(self):
        # 1. Eliminación hacia adelante (heredada)
        rank, pivot_cols = self._eliminate_forward()

        # 2. Verificar sistema
        status, message = self._check_system_status(rank)

        if status != "UNIQUE_SOLUTION":
            return {
                "status": status,
                "message": message,
                "echelon_matrix": self.matrix,
                "solution": None,
                "steps": self.steps
            }

        # 3. Eliminación hacia atrás (Gauss‑Jordan)
        self._eliminate_backward(pivot_cols)

        # 4. Extraer la solución de la última columna
        num_vars = self.matrix.cols - 1
        solution = [self.matrix.get(i, num_vars) for i in range(num_vars)]
        solution = [0.0 if abs(val) < self.eps else round(val, 6) for val in solution]

        # 5. Pasos de sustitución: en RREF no hay sustitución regresiva, 
        #    pero podemos indicar que la solución se lee directamente.
        back_sub_steps = ["La solución se lee directamente de la última columna de la matriz escalonada reducida."]

        return {
            "status": status,
            "message": message,
            "echelon_matrix": self.matrix,
            "solution": solution,
            "steps": self.steps,
            "back_substitution_steps": back_sub_steps
        }