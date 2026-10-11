"""Resolutor del Modelo de Insumo-Producto de Leontief con viabilidad de Hawkins-Simon."""

from fractions import Fraction

from src.backend.constantes import CERO_EPSILON, ERROR, EXITO, SINGULAR
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.resolutores.operaciones_matrices.inversa import ResolutorInversa
from src.backend.resolutores.operaciones_matrices.operaciones import (
    ResolutorOperacionesMatrices,
)
from src.backend.utilidades.formateadores import formatear_fraccion_str


class ResolutorModeloLeontief:
    """Modela sistemas economicos insumo-producto (I - C) x = d calculando produccion total."""

    def __init__(self, eps: float = CERO_EPSILON) -> None:
        """Inicializa el resolutor con operaciones matriciales e inversion."""
        self.eps = eps
        self._ops = ResolutorOperacionesMatrices()
        self._inv = ResolutorInversa()

    def _identidad(self, n: int) -> Matriz:
        """Genera una matriz identidad de orden n."""
        return Matriz(n, n, [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)])

    def _hawkins_simon(self, M: Matriz, n: int) -> dict:
        """Verifica la condicion de viabilidad economica calculando menores principales."""
        menores = []
        es_viable = True
        for k in range(1, n + 1):
            sub_datos = [[M.obtener(i, j) for j in range(k)] for i in range(k)]
            sub_m = Matriz(k, k, sub_datos)
            det_k = self._ops.determinante(sub_m)
            pos = det_k > 0
            if not pos:
                es_viable = False
            menores.append({
                "orden": k,
                "determinante": formatear_fraccion_str(det_k),
                "es_positivo": pos,
            })
        return {
            "es_economicamente_viable": es_viable,
            "viable": es_viable,
            "menores_principales": menores,
            "conclusion": (
                "El modelo es ECONÓMICAMENTE VIABLE: todas las menores principales son positivas."
                if es_viable else
                "El modelo NO ES VIABLE: al menos una menor principal de (I − C) no es positiva."
            ),
        }

    def _analisis_sectorial(
        self,
        matriz_c: Matriz,
        x: list[Fraction],
        d: list[Fraction],
        sectores: list[str],
    ) -> list[dict]:
        """Calcula el consumo intermedio y valor anadido para cada sector economico."""
        n = matriz_c.filas
        tabla = []
        for i in range(n):
            prod_i = x[i]
            dem_i = d[i]
            consumo_intermedio = sum(matriz_c.obtener(i, j) * x[j] for j in range(n))
            valor_anadido = prod_i - consumo_intermedio
            tabla.append({
                "sector": sectores[i],
                "produccion_total": formatear_fraccion_str(prod_i),
                "demanda_final": formatear_fraccion_str(dem_i),
                "consumo_intermedio": formatear_fraccion_str(consumo_intermedio),
                "valor_anadido": formatear_fraccion_str(valor_anadido),
            })
        return tabla

    @staticmethod
    def _validar_dimensiones(matriz_c: Matriz, vector_demanda: list[Fraction]) -> str | None:
        """Verifica que la matriz sea cuadrada y concuerde con el vector de demanda."""
        if matriz_c.filas != matriz_c.columnas:
            return "La matriz de coeficientes debe ser cuadrada (n×n)."
        if len(vector_demanda) != matriz_c.filas:
            return f"El vector de demanda debe tener {matriz_c.filas} componentes; se recibieron {len(vector_demanda)}."
        return None

    def _empaquetar_exito(
        self,
        matrices: tuple[Matriz, Matriz, Matriz, Matriz],
        datos: tuple[list[Fraction], list[Fraction], list[str], Fraction],
        pasos: list[dict],
    ) -> dict:
        """Construye el diccionario de resultado exitoso del modelo de Leontief."""
        matriz_c, identidad, M, multiplicador = matrices
        vector_produccion, vector_demanda, sectores, det_m = datos
        n = matriz_c.filas
        msg = f"Modelo de Leontief resuelto correctamente ({n} sectores)."
        return {
            "estado": EXITO,
            "status": "SUCCESS",
            "mensaje": msg,
            "message": msg,
            "n": n,
            "sectores": sectores,
            "determinante_leontief": formatear_fraccion_str(det_m),
            "matriz_leontief_latex": matriz_a_latex(M),
            "matriz_multiplicador_latex": matriz_a_latex(multiplicador),
            "matriz_identidad_latex": matriz_a_latex(identidad),
            "vector_produccion": [formatear_fraccion_str(v) for v in vector_produccion],
            "hawkins_simon": self._hawkins_simon(M, n),
            "analisis_sectorial": self._analisis_sectorial(
                matriz_c, vector_produccion, vector_demanda, sectores
            ),
            "pasos": pasos,
            "steps": pasos,
        }

    def _resultado_singular(
        self, M: Matriz, n: int, sectores: list[str], det_m: Fraction
    ) -> dict:
        """Genera la respuesta cuando la matriz de Leontief es singular."""
        msg = "det(I − C) = 0. El sistema de Leontief es singular: no existe multiplicador."
        return {
            "estado": SINGULAR,
            "status": "SINGULAR",
            "mensaje": msg,
            "message": msg,
            "n": n,
            "sectores": sectores,
            "determinante_leontief": str(det_m),
            "hawkins_simon": self._hawkins_simon(M, n),
            "pasos": [],
            "steps": [],
        }

    def _calcular_produccion(
        self, multiplicador: Matriz, vector_demanda: list[Fraction], n: int
    ) -> list[Fraction]:
        """Calcula el vector de producción x = (I - C)^-1 d."""
        d_col = Matriz(n, 1, [[Fraction(v)] for v in vector_demanda])
        x_col = self._ops.multiplicar(multiplicador, d_col)["matriz_resultado"]
        return [Fraction(x_col.obtener(i, 0)) for i in range(n)]

    def resolver(
        self,
        matriz_coeficientes: Matriz,
        vector_demanda: list[Fraction],
        nombres_sectores: list[str] | None = None,
    ) -> dict:
        """Resuelve el sistema x = (I - C)^-1 d y genera el analisis sectorial."""
        err = self._validar_dimensiones(matriz_coeficientes, vector_demanda)
        if err:
            return {"estado": ERROR, "status": "ERROR", "mensaje": err, "message": err}

        n = matriz_coeficientes.filas
        sectores = (
            nombres_sectores
            if (nombres_sectores and len(nombres_sectores) == n)
            else [f"Sector {i + 1}" for i in range(n)]
        )
        identidad = self._identidad(n)
        M = self._ops.restar(identidad, matriz_coeficientes)["matriz_resultado"]
        det_m = self._ops.determinante(M)

        if abs(det_m) < self.eps:
            return self._resultado_singular(M, n, sectores, det_m)

        res_inv = self._inv.resolver(M, construir_detalle_latex=False)
        if res_inv["estado"] != EXITO:
            msg = f"No se pudo invertir (I − C): {res_inv.get('mensaje', '')}."
            return {"estado": ERROR, "status": "ERROR", "mensaje": msg, "message": msg}
        multiplicador = res_inv["inversa"]
        vector_produccion = self._calcular_produccion(multiplicador, vector_demanda, n)

        return self._empaquetar_exito(
            (matriz_coeficientes, identidad, M, multiplicador),
            (vector_produccion, vector_demanda, sectores, det_m),
            res_inv.get("pasos", []),
        )
