from fractions import Fraction

class Matrix:    
    def __init__(self, rows: int, cols: int, data: list[list[float]] | None = None):
        self.rows = rows
        self.cols = cols
        
        if data is not None:
            self.data = data
        else:
            self.data = [[0.0 for _ in range(cols)] for _ in range(rows)]

    def get(self, row: int, col: int) -> float:
        return self.data[row][col]

    def set(self, row: int, col: int, value: float) -> None:
        self.data[row][col] = float(value)

    def clone(self) -> 'Matrix':
        new_data = [row[:] for row in self.data]
        return Matrix(self.rows, self.cols, new_data)

    def swap_rows(self, r1: int, r2: int) -> None:
        if r1 != r2:
            self.data[r1], self.data[r2] = self.data[r2], self.data[r1]

    def add_scaled_row(self, target_r: int, source_r: int, scalar: float) -> None:
        for c in range(self.cols):
            self.data[target_r][c] += scalar * self.data[source_r][c]

    def __str__(self) -> str:
        res = []
        for row in self.data:
            formatted_row = []
            for val in row:
                if abs(val) < 1e-9:
                    formatted_row.append(f"{'0':>6}")
                else:
                    frac = Fraction(val).limit_denominator(100)
                    if abs(float(frac) - val) < 1e-4:
                        if frac.denominator == 1:
                            formatted_row.append(f"{frac.numerator:>6}")
                        else:
                            formatted_row.append(f"{f'{frac.numerator}/{frac.denominator}':>6}")
                    else:
                        formatted_row.append(f"{val:6.2f}")
            res.append("[ " + " ".join(formatted_row) + " ]")
        return "\n".join(res)