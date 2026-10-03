from enum import Enum
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

class SolutionKind(str, Enum):
    EMPTY = "EMPTY"
    POINT = "POINT"
    LINE = "LINE"
    PLANE = "PLANE"
    AFFINE_SUBSPACE = "AFFINE_SUBSPACE"

@dataclass(frozen=True)
class SolutionSet:
    kind: SolutionKind
    dimension: int
    point: tuple[Fraction, ...] | None
    directions: tuple[tuple[Fraction, ...], ...]

def classify(point: tuple[Fraction, ...] | None, directions: tuple[tuple[Fraction, ...], ...]) -> SolutionKind:
    if point is None:
        return SolutionKind.EMPTY
    n_dirs = len(directions)
    if n_dirs == 0:
        return SolutionKind.POINT
    elif n_dirs == 1:
        return SolutionKind.LINE
    elif n_dirs == 2:
        return SolutionKind.PLANE
    else:
        return SolutionKind.AFFINE_SUBSPACE

def has_solution_param(result: dict[str, Any]) -> bool:
    return "solution_param" in result

def from_gauss_result(result: dict[str, Any]) -> SolutionSet | None:
    status = result.get("status")
    if status == "NO_SOLUTION":
        return SolutionSet(kind=SolutionKind.EMPTY, dimension=0, point=None, directions=())
    elif status == "UNIQUE_SOLUTION":
        # Ensure solution_exact is converted to a tuple of Fractions
        point = tuple(Fraction(x) for x in result.get("solution_exact", []))
        return SolutionSet(kind=SolutionKind.POINT, dimension=0, point=point, directions=())
    elif status == "INFINITE_SOLUTIONS":
        return None
    return None
