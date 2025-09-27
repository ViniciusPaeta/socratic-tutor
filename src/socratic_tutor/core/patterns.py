"""
Lightweight algebra pattern detectors to improve guiding questions (MVP).

Deterministic rule for likely_needs_combining_like_terms:
- If input text shows multiplicative parentheses (e.g., "2*(x+1)" or "2(x+1)"),
  return True immediately.
- Else, if expand() changes the structure, return True.
- Else, fall back to complexity reduction heuristic.
"""

from __future__ import annotations

import re

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

TRANSFORMS = standard_transformations + (implicit_multiplication_application,)


def _complexity(expr: sp.Expr) -> int:
    """Proxy for structural complexity."""
    try:
        ops = int(sp.count_ops(expr, visual=False))
    except Exception:
        ops = 0
    return ops if ops > 0 else len(str(expr))


def _structurally_diff(a: sp.Expr, b: sp.Expr) -> bool:
    """Return True if expression trees differ (using srepr)."""
    try:
        return sp.srepr(a) != sp.srepr(b)
    except Exception:
        return str(a) != str(b)


def _has_multiplicative_parentheses(text: str) -> bool:
    """
    Detect parentheses that are being multiplied:
    - explicit: "*("
    - implicit: "<digit or word><whitespace optional>("  e.g., "2(x+1)", "x(y+1)"
    """
    if "*(" in text:
        return True
    return re.search(r"(\d|\w)\s*\(", text) is not None


def is_linear_in(symbol: str, eq_str: str) -> bool:
    """Return True if the equation is linear in the given symbol."""
    if "=" not in eq_str:
        return False
    lhs_s, rhs_s = eq_str.split("=", 1)
    x = sp.Symbol(symbol)
    lhs = parse_expr(lhs_s, transformations=TRANSFORMS)
    rhs = parse_expr(rhs_s, transformations=TRANSFORMS)
    poly = sp.Poly(sp.simplify(lhs - rhs), x)
    try:
        deg = poly.total_degree()
    except Exception:
        return False
    return deg <= 1


def has_parentheses(expr_or_eq: str) -> bool:
    """Cheap heuristic: presence of parentheses."""
    return "(" in expr_or_eq and ")" in expr_or_eq


def likely_needs_combining_like_terms(expr_or_eq: str) -> bool:
    """
    True if the input suggests distribution/combining like terms will help.
    Priority:
      1) String-level multiplicative parentheses → True
      2) expand() changes structure → True
      3) complexity fallback (count_ops reduction)
    """
    try:
        if "=" in expr_or_eq:
            lhs_s, rhs_s = expr_or_eq.split("=", 1)

            # (1) Deterministic by string: multiplicative parentheses on either side
            if _has_multiplicative_parentheses(lhs_s) or _has_multiplicative_parentheses(rhs_s):
                return True

            lhs = parse_expr(lhs_s, transformations=TRANSFORMS)
            rhs = parse_expr(rhs_s, transformations=TRANSFORMS)

            lhs_e = sp.expand(lhs)
            rhs_e = sp.expand(rhs)

            # (2) Structural-change rule
            if _structurally_diff(lhs, lhs_e) or _structurally_diff(rhs, rhs_e):
                return True

            # (3) Complexity fallback (sides and difference)
            diff = sp.simplify(lhs - rhs)
            base = min(_complexity(lhs) + _complexity(rhs), _complexity(diff))
            improved = min(
                _complexity(lhs_e) + _complexity(rhs_e),
                _complexity(sp.expand(diff)),
                _complexity(sp.simplify(diff)),
            )
            return improved < base
        else:
            # (1) Deterministic by string: multiplicative parentheses in expression
            if _has_multiplicative_parentheses(expr_or_eq):
                return True

            e = parse_expr(expr_or_eq, transformations=TRANSFORMS)
            e_e = sp.expand(e)

            # (2) Structural-change rule
            if _structurally_diff(e, e_e):
                return True

            # (3) Complexity fallback
            base = _complexity(e)
            improved = min(_complexity(e_e), _complexity(sp.simplify(e)))
            return improved < base
    except Exception:
        return False
