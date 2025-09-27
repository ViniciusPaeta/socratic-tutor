"""
Heuristic error classifiers to produce more actionable `error_type` labels.

Additions:
- "sign error?" — sign flipped on one side only (likely + ↔ - mistake).
- "moved term without operation?" — term appears to move across '=' without the
  matching inverse operation.
- "division-by-zero risk?" — division by an expression containing variables
  (domain restriction).
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


def _eq_parts(s: str):
    lhs_s, rhs_s = s.split("=", 1)
    lhs = parse_expr(lhs_s, transformations=TRANSFORMS)
    rhs = parse_expr(rhs_s, transformations=TRANSFORMS)
    return sp.simplify(lhs), sp.simplify(rhs)


def _has_symbolic_denominator(expr: sp.Expr) -> bool:
    """
    Return True if expr contains a denominator that depends on any symbol.
    This flags potential division-by-zero pitfalls.
    """
    try:
        num, den = sp.together(expr).as_numer_denom()
        return bool(den.free_symbols)
    except Exception:
        return False


def _side_changed_sign(prev_side: str, curr_side: str) -> bool:
    """
    Quick detector for a sign flip of an integer constant (+k <-> -k) on the same side.
    This is a lightweight string heuristic; symbolic confirmation happens elsewhere.
    """
    p = re.sub(r"\s+", "", prev_side)
    c = re.sub(r"\s+", "", curr_side)

    # Look for "-k" in previous and "+k" in current.
    m = re.search(r"-(\d+)", p)
    if m and re.search(rf"\+{m.group(1)}", c):
        return True

    # Look for "+k" in previous and "-k" in current.
    m = re.search(r"\+(\d+)", p)
    if m and re.search(rf"-{m.group(1)}", c):
        return True

    return False


def _moved_term_string_heuristic(prev_eq: str, curr_eq: str) -> bool:
    """
    Crude heuristic: a small integer term seems to have crossed '=' without the
    correct inverse operation/sign.

    Examples flagged:
        prev: x - 3 = 5     ->  curr: x = 5 - 3     (should be 5 + 3)
        prev: x + 4 = 1     ->  curr: x = 1 + 4     (OK — not flagged)
        prev: x + 4 = 1     ->  curr: x = 1 - 4     (should be 1 - 4? actually wrong)
    """
    p = prev_eq.replace(" ", "")
    c = curr_eq.replace(" ", "")
    if "=" not in p or "=" not in c:
        return False

    pl, pr = p.split("=", 1)
    cl, cr = c.split("=", 1)

    # Search for small integer constants hopping sides.
    for k in range(1, 10):
        plus, minus = f"+{k}", f"-{k}"

        # Case A: "-k" on LHS before; appears on RHS after with SAME sign (should flip).
        if minus in pl and minus in cr:
            return True
        # Case B: "+k" on LHS before; appears on RHS after with SAME sign (should flip).
        if plus in pl and plus in cr:
            return True

        # Case C: "-k" on RHS before; appears on LHS after with SAME sign (should flip).
        if minus in pr and minus in cl:
            return True
        # Case D: "+k" on RHS before; appears on LHS after with SAME sign (should flip).
        if plus in pr and plus in cl:
            return True

        # Optional: classic “correct” moves (not errors) — document but do not flag.
        # pl has -k and cr has +k  -> OK (not an error)
        # pr has -k and cl has +k  -> OK (not an error)
        # pl has +k and cr has -k  -> OK (not an error)
        # pr has +k and cl has -k  -> OK (not an error)

    return False


def classify_equation_error(previous: str, current: str) -> str:
    """
    Try to pinpoint why an equation step is not equivalent.

    Order of checks:
    - parse errors
    - one-sided change
    - division-by-zero risk
    - sign error? (string & structural hints)
    - moved term without operation? (string-level heuristic)
    - bad distributive?
    - fallback: nonlinear transform?
    """
    try:
        pl, pr = _eq_parts(previous.replace(" ", ""))
        cl, cr = _eq_parts(current.replace(" ", ""))
    except Exception as e:
        return f"parse error: {e}"

    # (1) One-sided change: exactly one side unchanged.
    same_left = sp.simplify(pl - cl) == 0
    same_right = sp.simplify(pr - cr) == 0
    if same_left ^ same_right:
        # (1a) Division-by-zero risk? Check denominators after together().
        if _has_symbolic_denominator(cl) or _has_symbolic_denominator(cr):
            return "division-by-zero risk?"

        # (1b) Sign error? — string-level hint on the side that changed.
        if not same_left and _side_changed_sign(str(pl), str(cl)):
            return "sign error?"
        if not same_right and _side_changed_sign(str(pr), str(cr)):
            return "sign error?"

        # (1c) Moved term without operation? — looks like a jump across '='.
        if _moved_term_string_heuristic(previous, current):
            return "moved term without operation?"

        return "one-sided operation"

    # (2) Even if both sides changed, we may still detect moved/sign issues.
    if _moved_term_string_heuristic(previous, current):
        return "moved term without operation?"
    if _side_changed_sign(str(pl), str(cl)) or _side_changed_sign(str(pr), str(cr)):
        return "sign error?"

    # (3) Division-by-zero risk across both sides
    # (e.g., dividing by x on both sides but step remains invalid).
    if _has_symbolic_denominator(cl) or _has_symbolic_denominator(cr):
        return "division-by-zero risk?"

    # (4) Bad distributive?
    # If expanding both sides fixes equality but the step is otherwise not equivalent.
    try:
        pe = sp.expand(pl - pr)
        ce = sp.expand(cl - cr)
        if (sp.simplify(pe - ce) == 0) and (sp.simplify((pl - pr) - (cl - cr)) != 0):
            return "bad distributive?"
    except Exception:
        pass

    # (5) Fallback
    return "nonlinear transform?"


def classify_expression_error(previous: str, current: str) -> str:
    """
    Expression mismatch: suggest a likely cause.

    Heuristics:
    - parse error
    - if expand makes them equal -> "bad distributive?"
    - otherwise -> "expressions not equal"
    """
    try:
        p = parse_expr(previous, transformations=TRANSFORMS)
        c = parse_expr(current, transformations=TRANSFORMS)
    except Exception as e:
        return f"parse error: {e}"

    if sp.simplify(p - c) == 0:
        return "ok"
    try:
        if sp.simplify(sp.expand(p) - sp.expand(c)) == 0:
            return "bad distributive?"
    except Exception:
        pass
    return "expressions not equal"
