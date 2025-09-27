"""
Unit tests for lightweight algebra pattern detectors (patterns.py).
"""

from socratic_tutor.core.patterns import (
    has_parentheses,
    is_linear_in,
    likely_needs_combining_like_terms,
)


def test_is_linear_in_true_for_linear_equation():
    # 3*(x - 2) = 9  -> linear in x
    assert is_linear_in("x", "3*(x - 2) = 9") is True


def test_is_linear_in_false_for_quadratic():
    # x^2 + 1 = 0  -> not linear
    assert is_linear_in("x", "x**2 + 1 = 0") is False


def test_has_parentheses_detects_in_equation_and_expression():
    assert has_parentheses("3*(x - 2) = 9") is True
    assert has_parentheses("2*(x+1)") is True
    assert has_parentheses("2*x + 1 = 3") is False
    assert has_parentheses("2*x + 1") is False


def test_likely_needs_combining_like_terms_expression_true():
    # expression that simplifies: 2*(x+1)  -> distributing reduces structure
    assert likely_needs_combining_like_terms("2*(x+1)") is True


def test_likely_needs_combining_like_terms_equation_true():
    # equation where distributing on one side is clearly helpful
    assert likely_needs_combining_like_terms("2*(x+1) = 2*x + 2") is True
