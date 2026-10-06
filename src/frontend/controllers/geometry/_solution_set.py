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
    return result.get("solution_param") is not None

def get_solution_param(result: dict[str, Any]) -> dict | None:
    sp = result.get("solution_param")
    if sp is None:
        return None
    try:
        num_vars = sp["num_vars"]
        particular = sp["particular"]
        directions = sp["directions"]
        free_cols = sp["free_cols"]
        param_names = sp["param_names"]
        if num_vars != len(particular) or len(directions) != len(free_cols) or len(free_cols) != len(param_names):
            return None
        # Ensure all are Fraction
        for p in particular:
            if not isinstance(p, Fraction): return None
        for d in directions:
            for v in d:
                if not isinstance(v, Fraction): return None
        return sp
    except (KeyError, TypeError, ValueError):
        return None

def from_solution_param(sp: dict[str, Any]) -> SolutionSet | None:
    if sp is None:
        return None
    point = tuple(sp["particular"])
    directions = tuple(tuple(d) for d in sp["directions"])
    k = classify(point, directions)
    return SolutionSet(kind=k, dimension=len(directions), point=point, directions=directions)

def from_gauss_result(result: dict[str, Any]) -> SolutionSet | None:
    status = result.get("status")
    if status == "NO_SOLUTION":
        return SolutionSet(kind=SolutionKind.EMPTY, dimension=0, point=None, directions=())
    elif status == "UNIQUE_SOLUTION":
        # Ensure solution_exact is converted to a tuple of Fractions
        point = tuple(Fraction(x) for x in result.get("solution_exact", []))
        return SolutionSet(kind=SolutionKind.POINT, dimension=0, point=point, directions=())
    elif status == "INFINITE_SOLUTIONS":
        sp = get_solution_param(result)
        if sp is not None:
            return from_solution_param(sp)
        return None
    return None
