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

from src.backend.exceptions import InvalidVectorError
from src.backend.models.matrix import Matrix, Numeric
from src.backend.utils.formatters import format_fraction_str, number_to_latex
from src.backend.utils.validators import MatrixValidator


class VectorOpsSolver:
    """Operaciones vectoriales con trazabilidad paso a paso."""

    def __init__(self):
        self.steps = []

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _log_step(self, description: str, current_matrix: Matrix = None, detail_latex: str = None) -> None:
        self.steps.append({
            "description": description,
            "matrix": current_matrix.clone() if current_matrix else None,
            "detail_latex": detail_latex,
        })

    @staticmethod
    def _is_column_vector(m: Matrix) -> bool:
        return m.cols == 1

    @staticmethod
    def _is_row_vector(m: Matrix) -> bool:
        return m.rows == 1

    @classmethod
    def _is_vector(cls, m: Matrix) -> bool:
        return cls._is_column_vector(m) or cls._is_row_vector(m)

    @classmethod
    def _vector_dim(cls, m: Matrix) -> int:
        """Dimensión (n) del vector. Asume que m es vector."""
        return m.rows if cls._is_column_vector(m) else m.cols

    @classmethod
    def _assert_vector(cls, m: Matrix, name: str) -> None:
        if not cls._is_vector(m):
            raise InvalidVectorError(
                f"{name}: se esperaba un vector (n×1 o 1×n), "
                f"recibido {m.rows}×{m.cols}."
            )

    @staticmethod
    def _transpose(m: Matrix) -> Matrix:
        new_data = [[m.get(i, j) for i in range(m.rows)] for j in range(m.cols)]
        return Matrix(m.cols, m.rows, new_data)

    def _harmonize_shapes(
        self,
        v1: Matrix,
        v2: Matrix,
        name1: str,
        name2: str,
        strict: bool,
    ) -> tuple[Matrix, Matrix, str | None]:
        """Alinea orientaciones de v1 y v2.

        Retorna (v1_orientado, v2_orientado, msg_ajuste_o_None).
        Lanza InvalidVectorError si las dimensiones no coinciden o si
        strict=True y las orientaciones difieren.
        """
        if v1.rows == v2.rows and v1.cols == v2.cols:
            return v1, v2, None

        dim1 = self._vector_dim(v1)
        dim2 = self._vector_dim(v2)

        if dim1 != dim2:
            raise InvalidVectorError(
                f"Dimensiones incompatibles: {name1} tiene dim {dim1}, "
                f"{name2} tiene dim {dim2}."
            )

        # Misma dim, distinta orientación (uno n×1, otro 1×n).
        if strict:
            raise InvalidVectorError(
                f"{name2}: se esperaba shape {v1.rows}×{v1.cols} para coincidir "
                f"con {name1}; recibido {v2.rows}×{v2.cols} (strict=True)."
            )

        v2_t = self._transpose(v2)
        orient_orig = "fila" if self._is_row_vector(v2) else "columna"
        msg = (
            f"Ajuste de orientación: {name2} era {orient_orig} "
            f"y se transpone a {v2_t.rows}×{v2_t.cols} para coincidir con {name1}."
        )
        return v1, v2_t, msg

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

        return {
            "status": "SUCCESS",
            "message": f"{op_word.capitalize()} de vectores completada (dim {dim}).",
            "result_matrix": result,
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

        return {
            "status": "SUCCESS",
            "message": f"Multiplicación escalar completada (dim {dim}).",
            "result_matrix": result,
            "steps": self.steps,
            "latex_details": latex_details,
        }