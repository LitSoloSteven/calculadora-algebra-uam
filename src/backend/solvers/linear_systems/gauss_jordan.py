from src.backend.solvers.linear_systems.gauss import GaussSolver
import math

class GaussJordanSolver(GaussSolver):
    def _eliminate_backward(self, pivot_cols):
        """
        Elimina los elementos por encima de cada pivote usando el 
        Mínimo Común Múltiplo (MCM) para trabajar solo con números enteros.
        """
        # Recorremos los pivotes de abajo hacia arriba
        for k in range(len(pivot_cols) - 1, -1, -1):
            pivot_row = k
            pivot_col = pivot_cols[k]
            
            pivote = self.matrix.get(pivot_row, pivot_col)
            
            # Para cada fila por encima del pivote
            for r in range(pivot_row - 1, -1, -1):
                objetivo = self.matrix.get(r, pivot_col)
                
                if abs(objetivo) > self.eps:
                    # 1. Calcular el MCM (siempre con valores enteros positivos)
                    mcm_val = math.lcm(int(abs(pivote)), int(abs(objetivo)))
                    
                    # 2. Calcular factores multiplicativos
                    mult_pivote = mcm_val // abs(pivote)
                    mult_objetivo = mcm_val // abs(objetivo)
                    
                    # 3. Determinar el signo para que la suma los anule
                    signo = -1 if (pivote * objetivo) > 0 else 1
                    
                    # 4. Modificar TODA la fila objetivo iterando columna por columna
                    for col in range(self.matrix.cols):
                        val_obj = self.matrix.get(r, col)
                        val_piv = self.matrix.get(pivot_row, col)
                        
                        nuevo_valor = (val_obj * mult_objetivo) + (val_piv * mult_pivote * signo)
                        self.matrix.set(r, col, nuevo_valor)
                        
                    # 5. Registrar el paso con notación matemática
                    signo_str = "+" if signo == 1 else "-"
                    self._log_step(
                        f"Fila {r+1} = {mult_objetivo} * Fila {r+1} {signo_str} {mult_pivote} * Fila {pivot_row+1}",
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

        # 4. Extraer la solución (Dividiendo el resultado entre la diagonal principal)
        num_vars = self.matrix.cols - 1
        solution = []
        for i in range(num_vars):
            b_val = self.matrix.get(i, num_vars)
            pivot_val = self.matrix.get(i, i)
            
            # Dividir para encontrar el valor real de la variable
            if abs(pivot_val) > self.eps:
                sol_val = b_val / pivot_val
            else:
                sol_val = 0.0
                
            solution.append(0.0 if abs(sol_val) < self.eps else round(sol_val, 6))

        # 5. Pasos de sustitución
        back_sub_steps = ["La solución se extrae dividiendo la columna de términos independientes entre los pivotes de la diagonal principal."]

        return {
            "status": status,
            "message": message,
            "echelon_matrix": self.matrix,
            "solution": solution,
            "steps": self.steps,
            "back_substitution_steps": back_sub_steps
        }