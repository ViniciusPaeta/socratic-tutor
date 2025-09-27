"""
Heuristic error classifiers to produce more actionable `error_type` labels.

Goal (MVP+):
- Move beyond "Not equivalent" by tagging common mistakes:
  * "one-sided operation"     — only LHS or RHS changed
  * "parse error: ..."        — parsing failed (already caught upstream)
  * "bad distributive?"       — distributive likely misapplied
  * "nonlinear transform?"    — change suggests a non-equivalent transform
- Keep it cheap & explainable; perfect accuracy is not required at MVP time.
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
    """Return (lhs_expr, rhs_expr) for 'LHS = RHS', using forgiving parsing."""
    lhs_s, rhs_s = s.split("=", 1)
    lhs = parse_expr(lhs_s, transformations=TRANSFORMS)
    rhs = parse_expr(rhs_s, transformations=TRANSFORMS)
    return sp.simplify(lhs), sp.simplify(rhs)


def classify_equation_error(previous: str, current: str) -> str:
    """
    Try to pinpoint why an equation step is not equivalent.

    Heuristics (order matters):
    - One-sided change? -> "one-sided operation"
    - Parentheses changed suspiciously? -> "bad distributive?"
    - Otherwise -> "nonlinear transform?" (generic)
    """
    try:
        pl, pr = _eq_parts(previous.replace(" ", ""))
        cl, cr = _eq_parts(current.replace(" ", ""))
    except Exception as e:
        return f"parse error: {e}"

    # (1) One-sided operation: exactly one side unchanged
    same_left = sp.simplify(pl - cl) == 0
    same_right = sp.simplify(pr - cr) == 0
    if same_left ^ same_right:  # XOR -> mudou só um lado
        return "one-sided operation"

    # (2) Bad distributive? if expanding one or both helps equality but the step failed
    try:
        pe = sp.expand(pl - pr)
        ce = sp.expand(cl - cr)
        if (sp.simplify(pe - ce) == 0) and (sp.simplify((pl - pr) - (cl - cr)) != 0):
            return "bad distributive?"
    except Exception:
        pass

    # (3) Fallback
    return "nonlinear transform?"


def classify_expression_error(previous: str, current: str) -> str:
    """
    Expression mismatch: suggest likely cause.

    Heuristics:
    - If expand makes them equal -> "bad distributive?"
    - Otherwise -> "expressions not equal"
    """
    try:
        p = parse_expr(previous, transformations=TRANSFORMS)
        c = parse_expr(current, transformations=TRANSFORMS)
    except Exception as e:
        return f"parse error: {e}"

    if sp.simplify(p - c) == 0:
        return "ok"  # caller shouldn't ask classify on ok path
    try:
        if sp.simplify(sp.expand(p) - sp.expand(c)) == 0:
            return "bad distributive?"
    except Exception:
        pass
    return "expressions not equal"
