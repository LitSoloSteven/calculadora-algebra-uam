"""Solver del Modelo de Insumo-Producto de Leontief.

Dado un vector de demanda final d y una matriz de coeficientes técnicos C (n×n),
el modelo busca el vector de producción x tal que:

    (I - C) x = d   →   x = (I - C)^{-1} d

Referencia pedagógica:
  - Álgebra Lineal - Modelo de Leontief, UAM (Semana 8).
  - Hawkins-Simon: todas las menores principales de (I - C) deben ser > 0
    para que el modelo sea económicamente viable.
"""
from fractions import Fraction
from typing import Optional

from src.backend.models.matrix import Matrix
from src.backend.constants import ZERO_EPSILON
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver
from src.backend.solvers.matrix_ops.inverse import MatrixInverseSolver
from src.backend.utils.formatters import format_fraction_str


class LeontiefSolver:
    """Modelo de Leontief: análisis de insumo-producto con aritmética exacta.

    Atributos calculados en `resolver()`:
        - M = I - C            (matriz de Leontief)
        - det(M)               (determinante; 0 → sistema inviable)
        - M^{-1}               (multiplicador de Leontief)
        - x = M^{-1} d        (vector de producción total)
        - viabilidad Hawkins-Simon (todas las menores principales de M > 0)
        - análisis sectorial   (producción, consumo intermedio, valor añadido)
    """

    def __init__(self, eps: float = ZERO_EPSILON):
        self.eps = eps
        self._ops = MatrixOpsSolver()
        self._inv_solver = MatrixInverseSolver()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def resolver(
        self,
        matriz_coeficientes: Matrix,
        vector_demanda: list[Fraction],
        nombres_sectores: Optional[list[str]] = None,
    ) -> dict:
        """Resuelve el modelo x = (I - C)^{-1} d.

        Args:
            matriz_coeficientes: Matriz C de coeficientes técnicos (n×n).
            vector_demanda: Vector d de demanda final (longitud n).
            nombres_sectores: Etiquetas opcionales para cada sector.

        Returns:
            dict con claves:
                status, message, n, sectores,
                matriz_identidad_latex, matriz_leontief_latex,
                matriz_multiplicador_latex, vector_produccion,
                hawkins_simon, analisis_sectorial, pasos.
        """
        n = matriz_coeficientes.rows

        if matriz_coeficientes.rows != matriz_coeficientes.cols:
            return self._error(
                "La matriz de coeficientes debe ser cuadrada (n×n)."
            )
        if len(vector_demanda) != n:
            return self._error(
                f"El vector de demanda debe tener {n} componentes; "
                f"se recibieron {len(vector_demanda)}."
            )

        sectores = (
            nombres_sectores
            if nombres_sectores and len(nombres_sectores) == n
            else [f"Sector {i + 1}" for i in range(n)]
        )

        # ── 1. Construir I y M = I - C ─────────────────────────────────
        identidad = self._identidad(n)
        resta_res = self._ops.restar(identidad, matriz_coeficientes)
        if resta_res["status"] != "SUCCESS":
            return self._error("Error al calcular I − C.")
        M = resta_res["result_matrix"]

        # ── 2. Calcular det(M) ─────────────────────────────────────────
        det_m = self._ops.determinante(M)

        if abs(det_m) < self.eps:
            return {
                "status": "SINGULAR",
                "message": (
                    "det(I − C) = 0. El sistema de Leontief es singular: "
                    "no existe multiplicador (la economía no tiene solución única)."
                ),
                "n": n,
                "sectores": sectores,
                "determinante_leontief": str(det_m),
                "hawkins_simon": self._hawkins_simon(M, n),
                "pasos": [],
            }

        # ── 3. Calcular M^{-1} (multiplicador) ────────────────────────
        res_inv = self._inv_solver.solve(M, build_step_latex=False)
        if res_inv["status"] != "SUCCESS":
            return self._error(
                f"No se pudo invertir (I − C): {res_inv.get('message', '')}."
            )
        multiplicador = res_inv["inverse"]

        # ── 4. Calcular x = M^{-1} · d ────────────────────────────────
        d_col = Matrix(n, 1, [[Fraction(v)] for v in vector_demanda])
        prod_res = self._ops.multiplicar(multiplicador, d_col)
        if prod_res["status"] != "SUCCESS":
            return self._error("Error al calcular x = M^{-1} · d.")
        x_col = prod_res["result_matrix"]

        vector_produccion = [Fraction(x_col.get(i, 0)) for i in range(n)]

        # ── 5. Hawkins-Simon ───────────────────────────────────────────
        hs = self._hawkins_simon(M, n)

        # ── 6. Análisis sectorial ──────────────────────────────────────
        analisis = self._analisis_sectorial(
            matriz_coeficientes, vector_produccion, vector_demanda, sectores
        )

        # ── 7. Formateo LaTeX ──────────────────────────────────────────
        from src.backend.solvers.matrix_ops.formatters import matrix_to_latex

        return {
            "status": "SUCCESS",
            "message": f"Modelo de Leontief resuelto correctamente ({n} sectores).",
            "n": n,
            "sectores": sectores,
            "determinante_leontief": format_fraction_str(det_m),
            "matriz_leontief_latex": matrix_to_latex(M),
            "matriz_multiplicador_latex": matrix_to_latex(multiplicador),
            "vector_produccion": [format_fraction_str(v) for v in vector_produccion],
            "vector_demanda": [format_fraction_str(Fraction(v)) for v in vector_demanda],
            "hawkins_simon": hs,
            "analisis_sectorial": analisis,
            "pasos": [],
        }

    # Alias canónico inglés
    solve = resolver

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _identidad(self, n: int) -> Matrix:
        """Construye la matriz identidad n×n."""
        datos = [
            [Fraction(1) if i == j else Fraction(0) for j in range(n)]
            for i in range(n)
        ]
        return Matrix(n, n, datos)

    def _hawkins_simon(self, M: Matrix, n: int) -> dict:
        """Verifica la condición de Hawkins-Simon para la matriz M = I − C.

        La condición exige que todos los menores principales de M (submatrices
        cuadradas superiores izquierdas) tengan determinante positivo.
        Esto garantiza que la economía puede satisfacer cualquier demanda final.
        """
        menores = []
        viable = True
        for k in range(1, n + 1):
            datos_sub = [
                [M.get(i, j) for j in range(k)]
                for i in range(k)
            ]
            sub = Matrix(k, k, datos_sub)
            det_k = self._ops.determinante(sub)
            positivo = (det_k > 0)
            if not positivo:
                viable = False
            menores.append({
                "orden": k,
                "determinante": format_fraction_str(det_k),
                "positivo": positivo,
            })

        if viable:
            conclusion = (
                "✓ Se satisface la condición de Hawkins-Simon: todos los menores "
                "principales de (I − C) son positivos. La economía puede producir "
                "cualquier vector de demanda final positivo."
            )
        else:
            fallidos = [m["orden"] for m in menores if not m["positivo"]]
            conclusion = (
                "✗ No se satisface la condición de Hawkins-Simon: los menores de "
                f"orden {fallidos} no son positivos. El modelo puede ser inviable "
                "para ciertos vectores de demanda."
            )

        return {
            "viable": viable,
            "menores": menores,
            "conclusion": conclusion,
        }

    def _analisis_sectorial(
        self,
        C: Matrix,
        x: list[Fraction],
        d: list[Fraction],
        sectores: list[str],
    ) -> list[dict]:
        """Calcula, por sector, producción total, consumo intermedio y demanda final.

        Para cada sector i:
            - produccion_total    = x[i]
            - consumo_intermedio  = Σ_j C[j,i] · x[i]  (columna i de C · x[i])
            - demanda_final       = d[i]
            - valor_anadido       = x[i] - consumo_intermedio_fila_i
              (insumos que el sector i recibe = Σ_j C[i,j] · x[j])
        """
        n = len(x)
        resultado = []
        for i in range(n):
            prod_total = x[i]
            # insumos que el sector i consume de todos los sectores
            insumos = sum(
                Fraction(C.get(i, j)) * Fraction(x[j])
                for j in range(n)
            )
            valor_anadido = prod_total - insumos
            resultado.append({
                "sector": sectores[i],
                "produccion_total": format_fraction_str(prod_total),
                "insumos_intermedios": format_fraction_str(insumos),
                "demanda_final": format_fraction_str(Fraction(d[i])),
                "valor_anadido": format_fraction_str(valor_anadido),
            })
        return resultado

    @staticmethod
    def _error(msg: str) -> dict:
        return {"status": "ERROR", "message": msg}
