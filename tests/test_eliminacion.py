import sys
import os
import unittest

# 1. Forzamos a Python a reconocer la carpeta raíz del proyecto
ruta_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ruta_raiz)

# 2. Ahora sí importamos las clases de tu compañero de forma segura
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems import GaussSolver

class TestGaussSolverOOP(unittest.TestCase):

    def test_caso_solucion_unica(self):
        """Evalúa el Caso 1: Sistema con Solución Única[cite: 2]."""
        # Sistema: 
        # 2x + y = 5
        # x - y = 1
        data = [
            [2.0, 1.0, 5.0],
            [1.0, -1.0, 1.0]
        ]
        # Se instancia el objeto Matrix requerido por el solver
        matriz_aumentada = Matrix(rows=2, cols=3, data=data)
        solver = GaussSolver(matriz_aumentada)
        resultado = solver.solve()
        
        self.assertEqual(resultado["status"], "UNIQUE_SOLUTION")
        self.assertIsNotNone(resultado["solution"])
        # Verifica que la solución calculada sea correcta (x=2, y=1)
        self.assertEqual(resultado["solution"], [2.0, 1.0])

    def test_caso_infinitas_soluciones(self):
        """Evalúa el Caso 2: Sistema con Infinitas Soluciones[cite: 2]."""
        # Sistema (fila 2 es múltiplo de la fila 1):
        # x + y = 2
        # 2x + 2y = 4
        data = [
            [1.0, 1.0, 2.0],
            [2.0, 2.0, 4.0]
        ]
        matriz_aumentada = Matrix(rows=2, cols=3, data=data)
        solver = GaussSolver(matriz_aumentada)
        resultado = solver.solve()
        
        self.assertEqual(resultado["status"], "INFINITE_SOLUTIONS")
        self.assertIsNone(resultado["solution"])

    def test_caso_inconsistente(self):
        """Evalúa el Caso 3: Sistema Sin Solución (Inconsistente)[cite: 2]."""
        # Sistema (rectas paralelas):
        # x + y = 2
        # x + y = 3
        data = [
            [1.0, 1.0, 2.0],
            [1.0, 1.0, 3.0]
        ]
        matriz_aumentada = Matrix(rows=2, cols=3, data=data)
        solver = GaussSolver(matriz_aumentada)
        resultado = solver.solve()
        
        self.assertEqual(resultado["status"], "NO_SOLUTION")
        self.assertIsNone(resultado["solution"])

if __name__ == '__main__':
    unittest.main()