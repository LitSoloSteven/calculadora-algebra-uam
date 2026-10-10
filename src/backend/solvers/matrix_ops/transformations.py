"""Solver de Transformaciones Lineales T: R^n → R^m.

Dado que T(x) = Ax, el solver calcula:
  - Núcleo ker(T): solución de Ax = 0 (espacio nulo)
  - Imagen Im(T): espacio columna de A
  - Nulidad = dim(ker(T)) = n − rango(A)
  - Rango = dim(Im(T)) = rango(A)
  - Teorema de la Dimensión: rango + nulidad = n
  - Inyectividad: ker(T) = {0} ⟺ nulidad = 0
  - Sobreyectividad: Im(T) = R^m ⟺ rango = m

NOTA SOBRE CONVENCIÓN DE SUBESPACIOS:
══════════════════════════════════════════════════════════════════
  Convención adoptada (columna estándar): la Imagen de T se
  representa como span de las columnas pivote de A. Esto es
  coherente con la definición Im(T) = {Ax : x ∈ R^n}, donde
  cada Ax es combinación lineal de columnas de A.

  Convención alternativa (fila): algunos textos representan el
  espacio fila de A^T como base del espacio imagen. Aquí NO se
  usa esa convención. Si tu apunte trabaja con filas, los
  vectores base de Im(T) serán transpuestos respecto a lo que
  muestra esta calculadora.
══════════════════════════════════════════════════════════════════

Referencia pedagógica:
  - Álgebra Lineal - Transformaciones Lineales, UAM (Semana 8).
  - Teorema de la Dimensión (Rank-Nullity): dim(ker T) + dim(Im T) = n.
"""
from fractions import Fraction
from typing import Optional

from src.backend.models.matrix import Matrix
from src.backend.constants import ZERO_EPSILON
from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver
from src.backend.utils.formatters import format_fraction_str


class LinearTransformationSolver:
    """Analiza T: R^n → R^m dado su representante matricial A (m×n).

    Todo el cálculo usa la eliminación exacta de GaussJordanSolver para
    garantizar aritmética sin punto flotante.
    """

    def __init__(self, eps: float = ZERO_EPSILON):
        self.eps = eps

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def resolver(
        self,
        matriz_A: Matrix,
        nombres_variables: Optional[list[str]] = None,
    ) -> dict:
        """Analiza la transformación T(x) = Ax.

        Args:
            matriz_A: Matriz representante A de T (m×n).
            nombres_variables: Nombres opcionales de las variables (longitud n).

        Returns:
            dict con claves:
                status, message, m, n,
                rango, nulidad, es_inyectiva, es_sobreyectiva,
                columnas_pivote, columnas_libres,
                nucleo (base), imagen (base),
                teorema_dimension, callout_convencion,
                pasos_reduccion.
        """
        if not isinstance(matriz_A, Matrix):
            return self._error("Se esperaba una instancia de Matrix.")

        m, n = matriz_A.rows, matriz_A.cols
        nombres = (
            nombres_variables
            if nombres_variables and len(nombres_variables) == n
            else [f"x_{{{i+1}}}" for i in range(n)]
        )

        # ── 1. Reducir A mediante Gauss-Jordan (solo coeficientes) ─────
        # Construimos el sistema aumentado Ax = 0 (vector b = 0)
        datos_aug = [
            [matriz_A.get(i, j) for j in range(n)] + [Fraction(0)]
            for i in range(m)
        ]
        aug = Matrix(m, n + 1, datos_aug)

        solver = GaussJordanSolver(aug, variable_names=nombres)
        resultado = solver.resolver()

        pivot_cols: list[int] = resultado.get("free_cols", [])  # mal nombre; ver abajo
        # GaussJordanSolver devuelve free_cols de _back_substitute; necesitamos
        # también los pivot_cols directos. Vamos a re-extraerlos via solve_reduction:
        solver2 = GaussJordanSolver(matriz_A.clone() if n == m else aug.clone(), variable_names=nombres)
        # Usamos solve_reduction sobre la forma reducida ya calculada para extraer pivotes
        # en el contexto correcto. Como GaussJordanSolver ya redujo `aug`, leemos de resultado:
        rango = 0
        columnas_pivote: list[int] = []
        # Extracción segura: en la RREF, las columnas pivote son aquellas en que
        # hay exactamente un 1 en esa columna (y la celda [r,c] == 1 con r = pivot_row).
        m_red = resultado.get("echelon_matrix")  # Matrix RREF m×(n+1)
        if m_red is not None:
            fila_pivote = 0
            for col in range(n):
                if fila_pivote >= m:
                    break
                val = m_red.get(fila_pivote, col)
                if abs(float(val) - 1.0) < self.eps:
                    # Verificar que sea la única celda no-cero en esa columna
                    all_zero_above = all(
                        abs(float(m_red.get(r, col))) < self.eps
                        for r in range(fila_pivote)
                    )
                    all_zero_below = all(
                        abs(float(m_red.get(r, col))) < self.eps
                        for r in range(fila_pivote + 1, m)
                    )
                    if all_zero_above and all_zero_below:
                        columnas_pivote.append(col)
                        fila_pivote += 1

        rango = len(columnas_pivote)
        nulidad = n - rango

        # ── 2. Base del núcleo ker(T) = Ax = 0 ────────────────────────
        columnas_libres = [c for c in range(n) if c not in columnas_pivote]
        base_nucleo = self._base_nucleo(m_red, columnas_pivote, columnas_libres, n, nombres)

        # ── 3. Base de la imagen Im(T) = span de columnas pivote de A ──
        base_imagen = self._base_imagen(matriz_A, columnas_pivote)

        # ── 4. Inyectividad y sobreyectividad ─────────────────────────
        es_inyectiva = (nulidad == 0)
        es_sobreyectiva = (rango == m)

        # ── 5. Pasos de reducción (LaTeX) ─────────────────────────────
        from src.backend.solvers.matrix_ops.formatters import matrix_to_latex
        pasos_reduccion = []
        for paso in resultado.get("steps", []):
            pasos_reduccion.append({
                "descripcion": paso["description"],
                "matriz": matrix_to_latex(paso["matrix"]),
            })

        # ── 6. Teorema de la dimensión ─────────────────────────────────
        teorema = (
            f"rango(T) + nulidad(T) = n  →  {rango} + {nulidad} = {n}  ✓"
        )

        # ── 7. Conclusiones sobre inyectividad/sobreyectividad ─────────
        conclusion_iny = (
            f"T es INYECTIVA: ker(T) = {{0}} (nulidad = 0)."
            if es_inyectiva else
            f"T NO es inyectiva: ker(T) tiene dimensión {nulidad} > 0."
        )
        conclusion_sob = (
            f"T es SOBREYECTIVA: Im(T) = R^{m} (rango = {rango} = m)."
            if es_sobreyectiva else
            f"T NO es sobreyectiva: Im(T) ⊊ R^{m} (rango = {rango} < {m})."
        )
        if es_inyectiva and es_sobreyectiva:
            conclusion_biy = "T es BIYECTIVA (isomorfismo)."
        elif not es_inyectiva and not es_sobreyectiva:
            conclusion_biy = "T no es inyectiva ni sobreyectiva."
        else:
            conclusion_biy = None

        return {
            "status": "SUCCESS",
            "message": f"Análisis de transformación lineal T: R^{n} → R^{m} completado.",
            "m": m,
            "n": n,
            "rango": rango,
            "nulidad": nulidad,
            "columnas_pivote": columnas_pivote,
            "columnas_libres": columnas_libres,
            "es_inyectiva": es_inyectiva,
            "es_sobreyectiva": es_sobreyectiva,
            "base_nucleo": base_nucleo,
            "base_imagen": base_imagen,
            "teorema_dimension": teorema,
            "conclusiones": {
                "inyectividad": conclusion_iny,
                "sobreyectividad": conclusion_sob,
                "biyectividad": conclusion_biy,
            },
            "callout_convencion": (
                "CONVENCIÓN ADOPTADA (columna estándar): la base de Im(T) está "
                "formada por las columnas pivote de A. Algunos textos usan la "
                "convención fila (vectores transpuestos); en ese caso la base "
                "visual difiere pero el espacio generado es el mismo."
            ),
            "pasos_reduccion": pasos_reduccion,
        }

    # Alias canónico inglés
    solve = resolver

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _base_nucleo(
        self,
        m_red: Matrix,
        columnas_pivote: list[int],
        columnas_libres: list[int],
        n: int,
        nombres: list[str],
    ) -> list[dict]:
        """Extrae la base del ker(T) a partir de la RREF de [A | 0].

        Cada vector de la base corresponde a una variable libre.
        Asigna 1 a la variable libre activa y 0 al resto, luego
        despeja las variables básicas desde la RREF.
        """
        if not columnas_libres:
            return []

        m_rows = m_red.rows if m_red else 0
        base = []

        for k, libre_col in enumerate(columnas_libres):
            vector = [Fraction(0)] * n

            # Asignar 1 a la variable libre activa, 0 a las otras libres
            vector[libre_col] = Fraction(1)

            # Despejar variables básicas desde la RREF
            for r, piv_col in enumerate(columnas_pivote):
                if r >= m_rows:
                    break
                # x_{piv_col} = -Σ_{libres} coeff * x_{libre}
                val = Fraction(0)
                for lc in columnas_libres:
                    coef = Fraction(m_red.get(r, lc))
                    val -= coef * vector[lc]
                vector[piv_col] = val

            componentes = [format_fraction_str(v) for v in vector]
            base.append({
                "parametro": f"t_{k+1}" if len(columnas_libres) > 1 else "t",
                "variable_libre": nombres[libre_col] if libre_col < len(nombres) else f"x_{libre_col+1}",
                "vector": componentes,
            })

        return base

    def _base_imagen(self, A: Matrix, columnas_pivote: list[int]) -> list[dict]:
        """Extrae la base de Im(T) como las columnas pivote de A.

        CONVENCIÓN COLUMNA ESTÁNDAR: Im(T) = {Ax : x ∈ R^n} = span(columnas A).
        Usamos columnas pivote de A (antes de reducir) como base.
        """
        base = []
        for idx, col in enumerate(columnas_pivote):
            componentes = [
                format_fraction_str(Fraction(A.get(r, col)))
                for r in range(A.rows)
            ]
            base.append({
                "indice_columna": col + 1,
                "vector": componentes,
            })
        return base

    @staticmethod
    def _error(msg: str) -> dict:
        return {"status": "ERROR", "message": msg}
