from fractions import Fraction

def matrix_to_latex(matrix, eps: float = 1e-6) -> str:
    rows_str = []
    
    for r in range(matrix.rows):
        row_vals = []
        for c in range(matrix.cols):
            val = matrix.get(r, c)
            
            if abs(val) < eps:
                row_vals.append("0")
            else:
                frac = Fraction(val).limit_denominator(100)
                if abs(float(frac) - val) < 1e-4:
                    if frac.denominator == 1:
                        row_vals.append(str(frac.numerator))
                    else:
                        row_vals.append(f"\\frac{{{frac.numerator}}}{{{frac.denominator}}}")
                else:
                    row_vals.append(f"{val:.4f}".rstrip('0').rstrip('.'))
                    
        rows_str.append(" & ".join(row_vals))
    
    body = " \\\\\n".join(rows_str)
    return f"\\begin{{bmatrix}}\n{body}\n\\end{{bmatrix}}"