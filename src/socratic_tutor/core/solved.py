"""
Solved-state detection for Socratic Tutor (MVP+).

For targets like "solve for x": consider solved only if the line is algebraically
in a solved shape: x = <expr> or <expr> = x, and the non-symbol side doesn't
contain x. We purposely do NOT call sympy.solve here to avoid marking intermediate
lines (e.g., 2*x = 8) as solved.
"""

from __future__ import annotations

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

TRANSFORMS = standard_transformations + (implicit_multiplication_application,)


def _eq_parts(s: str):
    lhs_s, rhs_s = s.split("=", 1)
    lhs = parse_expr(lhs_s, transformations=TRANSFORMS)
    rhs = parse_expr(rhs_s, transformations=TRANSFORMS)
    return sp.simplify(lhs), sp.simplify(rhs)


def _is_symbol(expr: sp.Expr, name: str) -> bool:
    return isinstance(expr, sp.Symbol) and expr.name == name


def is_solved_equation_for(var_name: str, eq_line: str) -> bool:
    """True only for shapes x = <expr> or <expr> = x with the other side free of x."""
    if "=" not in eq_line:
        return False
    try:
        lhs, rhs = _eq_parts(eq_line.replace(" ", ""))
    except Exception:
        return False

    x = sp.Symbol(var_name)

    left_is_var = _is_symbol(lhs, var_name) and not rhs.has(x)
    right_is_var = _is_symbol(rhs, var_name) and not lhs.has(x)
    return bool(left_is_var or right_is_var)


def is_problem_solved(target: str | None, line: str) -> bool:
    if not target:
        return False
    t = target.lower().strip()
    if t.startswith("solve for "):
        var = t.replace("solve for ", "").strip()
        return is_solved_equation_for(var, line)
    return False
