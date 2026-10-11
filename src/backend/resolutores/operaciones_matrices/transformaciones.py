"""Resolutor de transformaciones lineales T: R^n -> R^m con nucleo, imagen y rango."""

from fractions import Fraction

from src.backend.constantes import CERO_EPSILON, ERROR, EXITO
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.resolutores.sistemas_lineales.gauss_jordan import (
    ResolutorGaussJordan,
)
from src.backend.utilidades.formateadores import formatear_fraccion_str


class ResolutorTransformacionesLineales:
    """Analiza T(x) = Ax: calcula nucleo, imagen, nulidad, inyectividad y sobreyectividad."""

    def __init__(self, eps: float = CERO_EPSILON) -> None:
        """Inicializa el resolutor con la tolerancia de cero epsilon."""
        self.eps = eps

    def _base_nucleo(
        self,
        m_red: Matriz,
        columnas_pivote: list[int],
        columnas_libres: list[int],
        n: int,
        nombres: list[str],
    ) -> list[dict]:
        """Calcula la base del espacio nulo ker(T) despejando variables desde la RREF."""
        if not columnas_libres:
            return []
        m_filas = m_red.filas if m_red else 0
        base = []
        for k, libre_col in enumerate(columnas_libres):
            vector = [Fraction(0)] * n
            vector[libre_col] = Fraction(1)
            for r, piv_col in enumerate(columnas_pivote):
                if r >= m_filas:
                    break
                val = Fraction(0)
                for lc in columnas_libres:
                    val -= Fraction(m_red.obtener(r, lc)) * vector[lc]
                vector[piv_col] = val

            componentes = [formatear_fraccion_str(v) for v in vector]
            param_etiqueta = f"t_{k+1}" if len(columnas_libres) > 1 else "t"
            var_nom = nombres[libre_col] if libre_col < len(nombres) else f"x_{libre_col+1}"
            base.append({
                "parametro": param_etiqueta,
                "variable_libre": var_nom,
                "vector": componentes,
            })
        return base

    def _base_imagen(self, matriz_a: Matriz, columnas_pivote: list[int]) -> list[dict]:
        """Calcula la base del espacio columna Im(T) a partir de las columnas pivote originales."""
        base = []
        for col in columnas_pivote:
            componentes = [
                formatear_fraccion_str(Fraction(matriz_a.obtener(r, col)))
                for r in range(matriz_a.filas)
            ]
            base.append({
                "indice_columna": col + 1,
                "vector": componentes,
            })
        return base

    def _construir_conclusiones(
        self,
        es_iny: bool,
        es_sob: bool,
        nulidad: int,
        rango: int,
        m: int,
    ) -> dict[str, str | None]:
        """Genera el texto de conclusiones sobre inyectividad, sobreyectividad y biyectividad."""
        iny_txt = (
            "T es INYECTIVA: ker(T) = {0} (nulidad = 0)."
            if es_iny else f"T NO es inyectiva: ker(T) tiene dimensión {nulidad} > 0."
        )
        sob_txt = (
            f"T es SOBREYECTIVA: Im(T) = R^{m} (rango = {rango} = m)."
            if es_sob else f"T NO es sobreyectiva: Im(T) ⊊ R^{m} (rango = {rango} < {m})."
        )
        if es_iny and es_sob:
            biy_txt = "T es BIYECTIVA (isomorfismo)."
        elif not es_iny and not es_sob:
            biy_txt = "T no es inyectiva ni sobreyectiva."
        else:
            biy_txt = None

        return {
            "inyectividad": iny_txt,
            "sobreyectividad": sob_txt,
            "biyectividad": biy_txt,
        }

    def _reducir_sistema_homogeneo(self, matriz_a: Matriz, nombres: list[str]) -> dict:
        """Crea la matriz aumentada con ceros y ejecuta la reducción Gauss-Jordan."""
        m, n = matriz_a.filas, matriz_a.columnas
        datos_aug = [
            [matriz_a.obtener(i, j) for j in range(n)] + [Fraction(0)]
            for i in range(m)
        ]
        aug = Matriz(m, n + 1, datos_aug)
        resolutor_gj = ResolutorGaussJordan(aug, nombres_variables=nombres)
        return resolutor_gj.resolver_reduccion()

    def _empaquetar_resultado(
        self,
        matriz_a: Matriz,
        dimensiones: tuple[int, int, int, int],
        columnas: tuple[list[int], list[int]],
        bases: tuple[list[dict], list[dict], list[dict]],
    ) -> dict:
        """Empaqueta el diccionario completo con propiedades y conclusiones del análisis."""
        m, n, rango, nulidad = dimensiones
        columnas_pivote, columnas_libres = columnas
        base_nucleo, base_imagen, pasos_reduccion = bases
        es_inyectiva = (nulidad == 0)
        es_sobreyectiva = (rango == m)
        msg = f"Análisis de transformación lineal T: R^{n} → R^{m} completado."
        return {
            "estado": EXITO,
            "status": "SUCCESS",
            "mensaje": msg,
            "message": msg,
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
            "teorema_dimension": f"rango(T) + nulidad(T) = n  →  {rango} + {nulidad} = {n}  ✓",
            "conclusiones": self._construir_conclusiones(es_inyectiva, es_sobreyectiva, nulidad, rango, m),
            "callout_convencion": (
                "CONVENCIÓN ADOPTADA (columna estándar): la base de Im(T) está "
                "formada por las columnas pivote de A. Algunos textos usan la "
                "convención fila (vectores transpuestos); en ese caso la base "
                "visual difiere pero el espacio generado es el mismo."
            ),
            "pasos_reduccion": pasos_reduccion,
        }

    def resolver(
        self,
        matriz_a: Matriz,
        nombres_variables: list[str] | None = None,
    ) -> dict:
        """Analiza integralmente la transformacion T(x) = Ax."""
        if not isinstance(matriz_a, Matriz):
            err = "Se esperaba una instancia de Matriz."
            return {"estado": ERROR, "status": "ERROR", "mensaje": err, "message": err}

        m, n = matriz_a.filas, matriz_a.columnas
        nombres = (
            nombres_variables
            if (nombres_variables and len(nombres_variables) == n)
            else [f"x_{{{i+1}}}" for i in range(n)]
        )
        reduccion = self._reducir_sistema_homogeneo(matriz_a, nombres)

        columnas_pivote = reduccion["columnas_pivote"]
        rango = len(columnas_pivote)
        nulidad = n - rango
        columnas_libres = [c for c in range(n) if c not in columnas_pivote]
        m_red = reduccion["matriz_reducida"]

        base_nucleo = self._base_nucleo(m_red, columnas_pivote, columnas_libres, n, nombres)
        base_imagen = self._base_imagen(matriz_a, columnas_pivote)
        pasos_reduccion = _formatear_pasos_reduccion(reduccion["pasos"])

        return self._empaquetar_resultado(
            matriz_a,
            (m, n, rango, nulidad),
            (columnas_pivote, columnas_libres),
            (base_nucleo, base_imagen, pasos_reduccion),
        )


def _formatear_pasos_reduccion(pasos: list[dict]) -> list[dict]:
    """Formatea los pasos de reducción Gauss-Jordan con LaTeX y claves duales."""
    return [
        {
            "descripcion": p.get("descripcion", p.get("description", "")),
            "description": p.get("description", p.get("descripcion", "")),
            "matriz": matriz_a_latex(p.get("matriz", p.get("matrix"))),
            "matrix": matriz_a_latex(p.get("matriz", p.get("matrix"))),
        }
        for p in pasos
    ]
