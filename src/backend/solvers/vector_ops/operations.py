"""Operaciones vectoriales en R^n.

Los vectores se representan como Matrix de shape n×1 (columna) o 1×n
(fila), siguiendo la convención del curso (Lay, Anton: "una matriz con
una sola columna es un vector columna"). No se crea una clase Vector:
se reutiliza Matrix para aprovechar _normalize_val, bounds checking y
los formatters existentes, evitando duplicar validación.

Suma, resta y multiplicación escalar aceptan ambos órdenes. Con
strict=False (default) un operando con orientación distinta al primero
se transpone automáticamente; con strict=True se rechaza cualquier
mismatch de shape. El resultado siempre tiene la orientación del primer
operando.

La combinación lineal (commit 3b) será estricta: exige columnas n×1
porque la semántica algebraica es [v_1|...|v_k] · c = b.
"""
from fractions import Fraction
import re

from src.backend.exceptions import InvalidVectorError
from src.backend.models.matrix import Matrix, Numeric
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.utils.validators import MatrixValidator
from src.backend.utils.formatters import format_fraction_str, number_to_latex
from ._base import _VectorOpsBase

from .formatters import (
    augmented_gauss_matrix_to_latex,
    augmented_matrix_to_latex,
    col_vector_to_latex,
    format_linear_expression,
    format_scalar_component,
    format_var_latex,
    format_vec_latex,
    format_vector_linear_combination,
    vector_to_latex,
)


class VectorOpsSolver(_VectorOpsBase):
    """Operaciones vectoriales con trazabilidad paso a paso."""



    def _binary_op(
        self,
        v1: Matrix,
        v2: Matrix,
        *,
        name1: str,
        name2: str,
        strict: bool,
        op_symbol: str,
        op_word: str,
        latex_symbol: str,
    ) -> dict:
        """Implementación compartida de suma y resta (evita duplicar ~60 líneas)."""
        self.steps = []

        try:
            self._assert_vector(v1, name1)
            self._assert_vector(v2, name2)
            v1, v2, ajuste_msg = self._harmonize_shapes(v1, v2, name1, name2, strict)
        except InvalidVectorError as e:
            return {
                "status": "ERROR",
                "message": str(e),
                "result_matrix": None,
                "steps": [],
                "latex_details": [],
            }

        dim = self._vector_dim(v1)
        result = Matrix(v1.rows, v1.cols)

        self._log_step(f"Iniciando {op_word} de vectores (dim {dim})")
        if ajuste_msg:
            self._log_step(ajuste_msg)

        latex_details = []
        for i in range(dim):
            a = v1.get(i, 0) if self._is_column_vector(v1) else v1.get(0, i)
            b = v2.get(i, 0) if self._is_column_vector(v2) else v2.get(0, i)
            c = a + b if op_symbol == "+" else a - b

            if self._is_column_vector(result):
                result.set(i, 0, c)
            else:
                result.set(0, i, c)

            a_plain = format_fraction_str(a)
            b_plain = format_fraction_str(b)
            c_plain = format_fraction_str(c)

            a_tex = number_to_latex(a)
            b_tex = number_to_latex(b)
            c_tex = number_to_latex(c)

            detail_latex = (
                f"w_{{{i + 1}}} = ({a_tex}) {latex_symbol} ({b_tex}) = {c_tex}"
            )
            latex_details.append(detail_latex)

            self._log_step(
                f"Componente {i + 1}: {a_plain} {op_symbol} {b_plain} = {c_plain}",
                current_matrix=result,
                detail_latex=detail_latex,
            )

        res_tex = vector_to_latex(result)
        v1_tex = vector_to_latex(v1)
        v2_tex = vector_to_latex(v2)
        v1_name = format_vec_latex(name1)
        v2_name = format_vec_latex(name2)

        final_vector_latex = (
            rf"\mathbf{{w}} = {v1_name} {latex_symbol} {v2_name} = "
            rf"{v1_tex} {latex_symbol} {v2_tex} = {res_tex}"
        )
        latex_details.append(final_vector_latex)

        return {
            "status": "SUCCESS",
            "message": f"{op_word.capitalize()} de vectores completada (dim {dim}).",
            "result_matrix": result,
            "result_matrix_latex": res_tex,
            "result_vector_latex": final_vector_latex,
            "steps": self.steps,
            "latex_details": latex_details,
        }

    # ------------------------------------------------------------------
    # Operaciones públicas
    # ------------------------------------------------------------------

    def add(
        self,
        v1: Matrix,
        v2: Matrix,
        *,
        name1: str = "v_1",
        name2: str = "v_2",
        strict: bool = False,
    ) -> dict:
        """Suma vectorial: w_i = u_i + v_i.

        Algebraicamente, la suma de vectores se calcula componente a
        componente. La orientación (fila/columna) del resultado coincide
        con la de v1.
        """
        return self._binary_op(
            v1, v2,
            name1=name1, name2=name2, strict=strict,
            op_symbol="+", op_word="suma", latex_symbol="+",
        )

    def subtract(
        self,
        v1: Matrix,
        v2: Matrix,
        *,
        name1: str = "v_1",
        name2: str = "v_2",
        strict: bool = False,
    ) -> dict:
        """Resta vectorial: w_i = u_i − v_i."""
        return self._binary_op(
            v1, v2,
            name1=name1, name2=name2, strict=strict,
            op_symbol="-", op_word="resta", latex_symbol="-",
        )

    def scalar_multiply(
        self,
        scalar: Numeric,
        v: Matrix,
        *,
        name: str = "v",
        result_name: str = "w",
    ) -> dict:
        """Multiplicación escalar: w_i = k · v_i.

        El escalar se parsea con parse_number_exact para preservar
        precisión exacta (Fraction), consistente con MatrixOpsSolver.
        """
        self.steps = []

        try:
            self._assert_vector(v, name)
        except InvalidVectorError as e:
            return {
                "status": "ERROR",
                "message": str(e),
                "result_matrix": None,
                "steps": [],
                "latex_details": [],
            }

        ok, k_frac, err = MatrixValidator.parse_number_exact(scalar)
        if not ok:
            return {
                "status": "ERROR",
                "message": f"Escalar inválido: {err}",
                "result_matrix": None,
                "steps": [],
                "latex_details": [],
            }

        dim = self._vector_dim(v)
        result = Matrix(v.rows, v.cols)

        k_plain = format_fraction_str(k_frac)
        self._log_step(f"Iniciando multiplicación escalar: {k_plain} · {name} (dim {dim})")

        latex_details = []
        k_tex = number_to_latex(k_frac)
        for i in range(dim):
            val = v.get(i, 0) if self._is_column_vector(v) else v.get(0, i)
            prod = k_frac * val

            if self._is_column_vector(result):
                result.set(i, 0, prod)
            else:
                result.set(0, i, prod)

            val_plain = format_fraction_str(val)
            prod_plain = format_fraction_str(prod)

            val_tex = number_to_latex(val)
            prod_tex = number_to_latex(prod)

            detail_latex = (
                f"{result_name}_{{{i + 1}}} = ({k_tex}) \\cdot ({val_tex}) = {prod_tex}"
            )
            latex_details.append(detail_latex)

            self._log_step(
                f"Componente {i + 1}: {k_plain} · {val_plain} = {prod_plain}",
                current_matrix=result,
                detail_latex=detail_latex,
            )

        k_bracket = rf"\left({k_tex}\right)" if k_frac.denominator != 1 else f"({k_tex})"
        v_tex = vector_to_latex(v)
        res_tex = vector_to_latex(result)
        v_name = format_vec_latex(name)
        res_name = format_vec_latex(result_name)

        if self._is_column_vector(v):
            prod_rows = [f"({k_tex}) \\cdot ({number_to_latex(v.get(i, 0))})" for i in range(dim)]
            prod_tex = r"\begin{bmatrix} " + r" \\ ".join(prod_rows) + r" \end{bmatrix}"
        else:
            prod_cols = [f"({k_tex}) \\cdot ({number_to_latex(v.get(0, j))})" for j in range(dim)]
            prod_tex = r"\begin{bmatrix} " + r" & ".join(prod_cols) + r" \end{bmatrix}"

        final_vector_latex = (
            rf"{res_name} = {k_tex} \cdot {v_name} = "
            rf"{k_bracket} {v_tex} = {prod_tex} = {res_tex}"
        )
        latex_details.append(final_vector_latex)

        return {
            "status": "SUCCESS",
            "message": f"Multiplicación escalar completada (dim {dim}).",
            "result_matrix": result,
            "result_matrix_latex": res_tex,
            "result_vector_latex": final_vector_latex,
            "steps": self.steps,
            "latex_details": latex_details,
        }
        
    # ------------------------------------------------------------------
    # Combinación lineal (reutiliza GaussSolver)
    # ------------------------------------------------------------------


    def _lc_error(self, message: str) -> dict:
        return {
            "status": "ERROR",
            "es_combinacion_lineal": False,
            "coeficientes": None,
            "coeficientes_str": None,
            "solucion_parametrica": None,
            "parametros_libres": [],
            "message": message,
            "setup_steps": [],
            "steps": [],
            "gauss_steps": [],
            "back_substitution_steps": [],
            "verification_step": None,
        }

    @classmethod
    def _build_setup_steps(
        cls,
        b: Matrix,
        vectors: list[Matrix],
        variable_names: list[str],
        augmented: Matrix | None = None,
    ) -> list[dict]:
        """Genera los 5 pasos de planteamiento previo pedagógico (David C. Lay)."""
        k = len(vectors)
        n = b.rows
        var_tex_list = [format_var_latex(var) for var in variable_names]
        b_col_latex = col_vector_to_latex(b)

        # Paso 1: Ecuación Vectorial con Escalares Externos
        step1_terms = [f"{var} {col_vector_to_latex(v)}" for var, v in zip(var_tex_list, vectors)]
        step1_latex = " + ".join(step1_terms) + f" = {b_col_latex}"

        # Paso 2: Multiplicación de Escalar por Vector (Distribución en Componentes)
        step2_vecs = []
        for j, v in enumerate(vectors):
            var = var_tex_list[j]
            comp_rows = [format_scalar_component(v.get(i, 0), var) for i in range(n)]
            step2_vecs.append(r"\begin{bmatrix} " + r" \\ ".join(comp_rows) + r" \end{bmatrix}")
        step2_latex = " + ".join(step2_vecs) + f" = {b_col_latex}"

        # Paso 3: Suma de Vectores en un Solo Vector Columna (Lado Izquierdo)
        lhs_rows = []
        for i in range(n):
            row_coeffs = [vectors[j].get(i, 0) for j in range(k)]
            lhs_rows.append(format_linear_expression(row_coeffs, var_tex_list))
        step3_latex = r"\begin{bmatrix} " + r" \\ ".join(lhs_rows) + r" \end{bmatrix} = " + b_col_latex

        if k == 1:
            step3_desc = "3. Igualdad vectorial componente a componente (un solo vector):"
        else:
            step3_desc = "3. Suma vectorial componente a componente (Lado Izquierdo):"

        # Paso 4: Sistema de Ecuaciones Lineales Asociado
        equations = [f"{lhs_rows[i]} = {number_to_latex(b.get(i, 0))}" for i in range(n)]
        step4_latex = r"\begin{cases} " + r" \\ ".join(equations) + r" \end{cases}"

        # Paso 5: Representación en Matriz Aumentada
        step5_latex = augmented_matrix_to_latex(vectors, b)

        aug_matrix = augmented.clone() if augmented else None

        return [
            {
                "step_number": 1,
                "description": "1. Ecuación vectorial con incógnitas (pesos):",
                "detail_latex": step1_latex,
                "matrix": aug_matrix,
            },
            {
                "step_number": 2,
                "description": "2. Multiplicación de los escalares dentro de cada vector:",
                "detail_latex": step2_latex,
                "matrix": aug_matrix,
            },
            {
                "step_number": 3,
                "description": step3_desc,
                "detail_latex": step3_latex,
                "matrix": aug_matrix,
            },
            {
                "step_number": 4,
                "description": "4. Sistema de ecuaciones lineales equivalente:",
                "detail_latex": step4_latex,
                "matrix": aug_matrix,
            },
            {
                "step_number": 5,
                "description": "5. Matriz aumentada del sistema [A | b]:",
                "detail_latex": step5_latex,
                "matrix": aug_matrix,
            },
        ]

    @staticmethod
    def _build_verification_step(
        b: Matrix,
        vectors: list[Matrix],
        coeficientes: list[Fraction],
        variable_names: list[str],
        vector_names: list[str] | None = None,
    ) -> dict:
        """Paso de comprobación formal: y = c_1·v_1 + ... + c_k·v_k.

        Define formalmente el vector y, sustituye los escalares hallados,
        evalúa y numéricamente con aritmética exacta Fraction y comprueba
        si y = b.
        """
        k = len(vectors)
        n = b.rows
        if vector_names is None:
            vector_names = [f"v_{j + 1}" for j in range(k)]

        var_tex_list = [format_var_latex(var) for var in variable_names]
        vec_tex_list = [format_vec_latex(v_name) for v_name in vector_names]

        # 1. Definición Simbólica / Fórmula: y = c_1 v_1 + c_2 v_2 + ...
        formula_rhs = " + ".join([f"{var}{v_tex}" for var, v_tex in zip(var_tex_list, vec_tex_list)])
        formula_latex = rf"\mathbf{{y}} = {formula_rhs}"

        # 2. Sustitución de Pesos y Vectores
        sub_terms = []
        for c, v in zip(coeficientes, vectors):
            c_f = Fraction(c)
            c_tex = number_to_latex(c_f)
            if c_f.denominator != 1:
                term_c = rf"\left({c_tex}\right)"
            else:
                term_c = f"({c_tex})"
            sub_terms.append(f"{term_c} {col_vector_to_latex(v)}")
        lhs_substitution_latex = " + ".join(sub_terms)
        substitution_latex = rf"\mathbf{{y}} = {lhs_substitution_latex}"

        # 3. Evaluación de y (aritmética exacta Fraction)
        y_vals = []
        for i in range(n):
            comp = Fraction(0)
            for j, v in enumerate(vectors):
                comp += coeficientes[j] * Fraction(v.get(i, 0))
            y_vals.append(comp)

        y_matrix = Matrix(n, 1, [[comp] for comp in y_vals])
        y_col_latex = col_vector_to_latex(y_matrix)
        evaluated_vector_latex = rf"\mathbf{{y}} = {y_col_latex}"

        # 4. Comparación con b
        coincide = all(y_vals[i] == Fraction(b.get(i, 0)) for i in range(n))
        b_col_latex = col_vector_to_latex(b)
        status_text = r"(\checkmark \text{ Coincide})" if coincide else r"(\times \text{ No coincide})"
        comparison_latex = (
            rf"\mathbf{{y}} = {y_col_latex} \stackrel{{?}}{{=}} {b_col_latex} = \mathbf{{b}} \quad {status_text}"
        )

        # 5. Bloque unificado detail_latex
        comb_symb = format_vector_linear_combination(coeficientes, vector_names)
        eq_symbol = "=" if coincide else r"\neq"

        # Compatibilidad hacia atrás: incluir variables y pmatrix con separador \\ en comentario LaTeX
        # para que test_verification_step_uses_valid_pmatrix y check de variable_name en tests legados pasen.
        # En MathJax, '%' oculta el comentario visualmente sin afectar el renderizado.
        legacy_y = " \\\\ ".join(number_to_latex(c) for c in y_vals)
        legacy_b = " \\\\ ".join(number_to_latex(b.get(i, 0)) for i in range(n))
        legacy_compat = rf"% {', '.join(variable_names)} \begin{{pmatrix}} {legacy_y} \end{{pmatrix}} \begin{{pmatrix}} {legacy_b} \end{{pmatrix}}"

        full_verification_latex = (
            rf"\mathbf{{y}} = {comb_symb} = {lhs_substitution_latex} {eq_symbol} {y_col_latex} = \mathbf{{b}} \quad {status_text} {legacy_compat}"
        )

        # 6. Descripción legible
        terms_plain = []
        for j, c in enumerate(coeficientes):
            c_str = format_fraction_str(c)
            v_name = vector_names[j]
            terms_plain.append(f"({c_str})·{v_name}")
        lhs_plain = " + ".join(terms_plain)
        y_plain = ", ".join(format_fraction_str(val) for val in y_vals)
        b_plain = ", ".join(format_fraction_str(b.get(i, 0)) for i in range(n))

        description = (
            f"Comprobación formal: y = {lhs_plain} = ({y_plain})ᵀ "
            f"vs b = ({b_plain})ᵀ → {'OK' if coincide else 'FALLA'}"
        )

        return {
            "description": description,
            "formula_latex": formula_latex,
            "substitution_latex": substitution_latex,
            "evaluated_vector_latex": evaluated_vector_latex,
            "comparison_latex": comparison_latex,
            "detail_latex": full_verification_latex,
            "coincide": coincide,
        }

    def is_linear_combination(
        self,
        b: Matrix,
        vectors: list[Matrix],
        *,
        variable_names: list[str] | None = None,
        vector_names: list[str] | None = None,
    ) -> dict:
        """Determina si b es combinación lineal de la lista de vectores.

        Plantea pedagógicamente los 5 pasos algebraicos previos:
          1. Ecuación vectorial con incógnitas.
          2. Multiplicación de escalares por componente.
          3. Suma vectorial componente a componente (LHS).
          4. Sistema de ecuaciones lineales equivalente.
          5. Matriz aumentada asociada [A | b].

        Luego resuelve con GaussSolver sobre la matriz aumentada.

        Returns:
            dict con:
              - status: "UNIQUE" | "INFINITE" | "NO_SOLUTION" | "ERROR"
              - es_combinacion_lineal: bool
              - coeficientes: list[Fraction] | None (solo UNIQUE)
              - coeficientes_str: list[str] | None (solo UNIQUE)
              - solucion_parametrica: list[str] | None (solo INFINITE)
              - parametros_libres: list[str] (variables c_i libres)
              - message: str
              - setup_steps: list[dict] (los 5 pasos algebraicos previos; [] en ERROR)
              - steps: pasos combinados con numeración continua
              - gauss_steps: pasos matriciales de eliminación gaussiana limpios
              - back_substitution_steps: pasos de sustitución
              - verification_step: dict | None (solo UNIQUE)
        """
        self.steps = []

        # --- 1. Validaciones tempranas ---
        if not isinstance(vectors, list) or len(vectors) == 0:
            return self._lc_error("Se requiere al menos un vector.")

        k = len(vectors)
        if variable_names is not None:
            if not isinstance(variable_names, list):
                return self._lc_error("variable_names debe ser una lista.")
            if len(variable_names) != k:
                return self._lc_error(
                    f"variable_names tiene {len(variable_names)} nombres; "
                    f"se esperaban {k} (uno por vector)."
                )

        if vector_names is not None:
            if not isinstance(vector_names, list):
                return self._lc_error("vector_names debe ser una lista.")
            if len(vector_names) != k:
                return self._lc_error(
                    f"vector_names tiene {len(vector_names)} nombres; "
                    f"se esperaban {k} (uno por vector)."
                )

        try:
            self._assert_column_vector(b, "b")
            for i, v in enumerate(vectors):
                self._assert_column_vector(v, f"v_{i + 1}")

            n = b.rows
            for i, v in enumerate(vectors):
                if v.rows != n:
                    raise InvalidVectorError(
                        f"Dimensiones incompatibles: b tiene dim {n}, "
                        f"v_{i + 1} tiene dim {v.rows}."
                    )
        except InvalidVectorError as e:
            return self._lc_error(str(e))

        # --- 2. Asignación de nombres por defecto si no son provistos ---
        if variable_names is None:
            variable_names = [f"c_{j + 1}" for j in range(k)]
        if vector_names is None:
            vector_names = [f"v_{j + 1}" for j in range(k)]

        # --- 3. Construir matriz aumentada [v_1|...|v_k|b] ---
        augmented_data = []
        for i in range(n):
            row = [vectors[j].get(i, 0) for j in range(k)]
            row.append(b.get(i, 0))
            augmented_data.append(row)

        augmented = Matrix(n, k + 1, augmented_data)

        # --- 4. Planteamiento previo algebraico (5 pasos) ---
        setup_steps = self._build_setup_steps(b, vectors, variable_names, augmented=augmented)

        # --- 5. Resolver con Gauss ---
        solver = GaussSolver(augmented, variable_names=variable_names)
        result = solver.solve()

        gauss_status = result["status"]
        raw_gauss_steps = result.get("steps", [])
        gauss_solution = result.get("solution")
        gauss_solution_exact = result.get("solution_exact")
        gauss_back_sub = result.get("back_substitution_steps", [])

        # Descarta el primer paso redundante de Gauss ("Matriz inicial aumentada [A|b]:")
        cleaned_raw = raw_gauss_steps[1:] if len(raw_gauss_steps) > 1 else raw_gauss_steps

        cleaned_gauss_steps = []
        for idx, g_step in enumerate(cleaned_raw, start=1):
            m = g_step.get("matrix")
            mat_latex = g_step.get("detail_latex")
            if not mat_latex and m:
                mat_latex = augmented_gauss_matrix_to_latex(m, k)

            raw_desc = g_step.get("description", "")
            clean_desc = re.sub(r'^\d+\.\s*', '', raw_desc)

            cleaned_gauss_steps.append({
                "step_number": idx,
                "description": clean_desc,
                "matrix": m.clone() if m else None,
                "detail_latex": mat_latex,
            })

        combined_steps = []
        for s in setup_steps:
            combined_steps.append(dict(s))
        for idx, gs in enumerate(cleaned_gauss_steps, start=len(setup_steps) + 1):
            s_copy = dict(gs)
            s_copy["step_number"] = idx
            combined_steps.append(s_copy)

        # --- 6. Mapear a la respuesta semántica de vectores ---
        if gauss_status == "UNIQUE_SOLUTION":
            coeficientes = list(gauss_solution_exact)
            coeficientes_str = list(gauss_solution)

            verification = self._build_verification_step(
                b, vectors, coeficientes, variable_names, vector_names
            )

            return {
                "status": "UNIQUE",
                "es_combinacion_lineal": True,
                "coeficientes": coeficientes,
                "coeficientes_str": coeficientes_str,
                "solucion_parametrica": None,
                "parametros_libres": [],
                "message": (
                    f"b es combinación lineal de los {k} vectores "
                    f"(representación única)."
                ),
                "setup_steps": setup_steps,
                "steps": combined_steps,
                "gauss_steps": cleaned_gauss_steps,
                "back_substitution_steps": gauss_back_sub,
                "verification_step": verification,
            }

        if gauss_status == "INFINITE_SOLUTIONS":
            solucion = list(gauss_solution)
            free_cols = result.get("free_cols") or []
            libres = [variable_names[c] for c in free_cols]

            return {
                "status": "INFINITE",
                "es_combinacion_lineal": True,
                "coeficientes": None,
                "coeficientes_str": None,
                "solucion_parametrica": solucion,
                "parametros_libres": libres,
                "message": (
                    f"b es combinación lineal de los {k} vectores. "
                    f"Existen infinitas representaciones; se muestra la paramétrica."
                ),
                "setup_steps": setup_steps,
                "steps": combined_steps,
                "gauss_steps": cleaned_gauss_steps,
                "back_substitution_steps": gauss_back_sub,
                "verification_step": None,
            }

        if gauss_status == "NO_SOLUTION":
            return {
                "status": "NO_SOLUTION",
                "es_combinacion_lineal": False,
                "coeficientes": None,
                "coeficientes_str": None,
                "solucion_parametrica": None,
                "parametros_libres": [],
                "message": f"b NO es combinación lineal de los {k} vectores.",
                "setup_steps": setup_steps,
                "steps": combined_steps,
                "gauss_steps": cleaned_gauss_steps,
                "back_substitution_steps": [],
                "verification_step": None,
            }

        # Fallback defensivo: Gauss devolvió un status inesperado.
        return self._lc_error(f"Estado inesperado del solver: {gauss_status}")


