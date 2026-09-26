"""Operaciones vectoriales en R^n: suma, resta, multiplicación escalar.

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

La combinación lineal vive en `linear_combination.LinearCombinationSolver`.
Se expone vía la fachada `VectorOpsSolver.is_linear_combination`, que
delega y preserva el contrato público para los consumidores existentes.
"""

from src.backend.exceptions import InvalidVectorError
from src.backend.models.matrix import Matrix, Numeric
from src.backend.utils.formatters import format_fraction_str, number_to_latex
from src.backend.utils.validators import MatrixValidator

from ._base import _VectorOpsBase
from .formatters import format_vec_latex, vector_to_latex


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
    def is_linear_combination(
        self,
        b: Matrix,
        vectors: list[Matrix],
        *,
        variable_names: list[str] | None = None,
        vector_names: list[str] | None = None,
    ) -> dict:
        """Determina si b es combinación lineal de la lista de vectores.

        Fachada de compatibilidad hacia atrás: delega en
        `LinearCombinationSolver.solve`. La implementación real vive en
        `linear_combination.py`, junto con el planteamiento pedagógico
        (5 pasos algebraicos) y la verificación formal.

        Se mantiene este método en `VectorOpsSolver` para no romper a los
        consumidores que hoy llaman `VectorOpsSolver().is_linear_combination(...)`
        (controllers, tests, frontend).
        """
        from .linear_combination import LinearCombinationSolver

        return LinearCombinationSolver().solve(
            b,
            vectors,
            variable_names=variable_names,
            vector_names=vector_names,
        )