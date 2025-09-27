"""
Tests for:
- Implicit multiplication acceptance (e.g., 3x, 3(x-2), 2(x+1)).
- Error labels returned by the step checker (equations & expressions).
"""

from socratic_tutor.core.step_checker import (
    check_equation_step,
    check_expression_step,
)

# ------------------------- Implicit multiplication -------------------------


def test_equation_accepts_implicit_multiplication():
    """
    3*(x-2) = 9  ->  3x - 6 = 9
    The second form uses implicit multiplication ("3x"), which our parser
    is configured to accept. This step should be valid.
    """
    prev = "3*(x - 2) = 9"
    cur = "3x - 6 = 9"
    res = check_equation_step(prev, cur)
    assert res.ok, f"Expected valid step with implicit multiplication, got: {res.reason}"


def test_expression_accepts_implicit_multiplication():
    """
    2(x+1)  ->  2x + 2
    Implicit multiplication in an expression should also be accepted.
    """
    prev = "2(x+1)"
    cur = "2x + 2"
    res = check_expression_step(prev, cur)
    assert res.ok, f"Expected valid expression step, got: {res.reason}"


# ------------------------------ Error labels ------------------------------


def test_equation_label_one_sided_operation():
    """
    2*x = 8  ->  x = 8
    Only the LHS was divided by 2; RHS stayed the same.
    Should be rejected and labeled as a one-sided operation.
    """
    prev = "2*x = 8"
    wrong = "x = 8"
    res = check_equation_step(prev, wrong)
    assert not res.ok, "Expected rejection for one-sided operation"
    assert "one-sided operation" in res.reason, f"Unexpected reason: {res.reason}"


def test_equation_label_parse_error():
    """
    A non-parsable target should yield a parse error label.
    """
    prev = "2*x = 8"
    wrong = "x = ?"
    res = check_equation_step(prev, wrong)
    assert not res.ok
    assert "parse error" in res.reason.lower(), f"Expected parse error, got: {res.reason}"


def test_expression_label_not_equal():
    """
    2(x+1)  ->  2x + 3
    Incorrect simplification; should be rejected with 'expressions not equal'.
    """
    prev = "2(x+1)"
    wrong = "2x + 3"
    res = check_expression_step(prev, wrong)
    assert not res.ok
    assert "expressions not equal" in res.reason.lower(), f"Unexpected reason: {res.reason}"
