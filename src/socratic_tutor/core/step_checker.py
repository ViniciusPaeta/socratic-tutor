"""
SymPy-backed step validation for the Socratic Tutor (MVP).

Equations: accept when the new equation preserves the solution set.
Improvements:
- Accept equality up to a non-zero constant factor.
- Randomized fallback requires consistent proportionality across samples and
  rejects zero/non-zero mismatches.
- Accept implicit multiplication in parsing (e.g., 3x, 3(x-2)).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from .error_labels import classify_equation_error, classify_expression_error

TRANSFORMS = standard_transformations + (implicit_multiplication_application,)


@dataclass
class CheckResult:
    ok: bool
    reason: str
    normalized_current: str
    normalized_previous: str


def _parse_equation(s: str):
    if "=" not in s:
        raise ValueError("Equations must be of the form 'LHS = RHS'")
    lhs_s, rhs_s = s.split("=", 1)
    lhs = parse_expr(lhs_s, transformations=TRANSFORMS)
    rhs = parse_expr(rhs_s, transformations=TRANSFORMS)
    syms = {str(sym): sym for sym in lhs.free_symbols.union(rhs.free_symbols)}
    return lhs, rhs, syms


def _parse_expression(s: str):
    expr = parse_expr(s, transformations=TRANSFORMS)
    syms = {str(sym): sym for sym in expr.free_symbols}
    return expr, syms


def _is_nonzero_constant(expr: sp.Expr) -> bool:
    s = sp.simplify(expr)
    return not s.free_symbols and s.is_finite and s != 0


def _equations_equivalent(prev, curr, syms) -> bool:
    """
    Decide if two equations are equivalent (same solution set).

    Accept when:
      (a) d1 == d2 exactly; or
      (b) d1 == k*d2 for a constant k ≠ 0; or
      (c) randomized check shows:
          - no sample with zero/non-zero mismatch, and
          - consistent proportionality across >= 3 nonzero samples.
    """
    prev_lhs, prev_rhs = prev
    curr_lhs, curr_rhs = curr
    d1 = sp.simplify(prev_lhs - prev_rhs)
    d2 = sp.simplify(curr_lhs - curr_rhs)

    # (a) Exact equality
    if sp.simplify(d1 - d2) == 0:
        return True

    # (b) Constant-factor equality (symbolic)
    try:
        ratio = sp.simplify(sp.together(d1) / sp.together(d2))
        if _is_nonzero_constant(ratio):
            return True
    except Exception:
        pass

    # (c) Randomized inference with stronger conditions
    vars_ = list(syms.values())
    trials = 12
    ratios = []
    nonzero_pairs = 0

    for _ in range(trials):
        subs = {v: (random.randint(-5, 5) or 1) for v in vars_}
        try:
            v1 = sp.simplify(d1.subs(subs))
            v2 = sp.simplify(d2.subs(subs))

            zero1 = sp.simplify(v1) == 0
            zero2 = sp.simplify(v2) == 0
            if zero1 != zero2:
                return False

            if not zero1 and not zero2:
                ratios.append((sp.nsimplify(v1), sp.nsimplify(v2)))
                nonzero_pairs += 1
        except Exception:
            return False

    if nonzero_pairs >= 3:
        a0, b0 = ratios[0]
        for a, b in ratios[1:]:
            if sp.simplify(a0 * b - a * b0) != 0:
                return False
        return True

    return False


def check_equation_step(previous: str, current: str) -> CheckResult:
    try:
        prev_lhs, prev_rhs, prev_syms = _parse_equation(previous.replace(" ", ""))
        curr_lhs, curr_rhs, curr_syms = _parse_equation(current.replace(" ", ""))
    except Exception as e:
        return CheckResult(False, f"parse error: {e}", current, previous)

    syms = {**prev_syms, **curr_syms}
    ok = _equations_equivalent((prev_lhs, prev_rhs), (curr_lhs, curr_rhs), syms)
    reason = "OK" if ok else classify_equation_error(previous, current)
    return CheckResult(ok, reason, str(sp.Eq(curr_lhs, curr_rhs)), str(sp.Eq(prev_lhs, prev_rhs)))


def check_expression_step(previous: str, current: str) -> CheckResult:
    try:
        prev_e, _ = _parse_expression(previous)
        curr_e, _ = _parse_expression(current)
    except Exception as e:
        return CheckResult(False, f"parse error: {e}", current, previous)
    diff = sp.simplify(prev_e - curr_e)
    ok = diff == 0
    reason = "OK" if ok else classify_expression_error(previous, current)
    return CheckResult(ok, reason, str(curr_e), str(prev_e))
