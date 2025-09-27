"""
Tests for new pedagogical error labels:
- sign error?
- moved term without operation?
- division-by-zero risk?
"""

from socratic_tutor.core.step_checker import check_equation_step


def test_label_sign_error():
    prev = "x - 3 = 5"
    wrong = "x + 3 = 5"  # flipped sign on LHS only (invalid)
    res = check_equation_step(prev, wrong)
    assert not res.ok
    assert "sign error" in res.reason.lower(), f"Reason: {res.reason}"


def test_label_moved_term_without_operation():
    prev = "x - 3 = 5"
    wrong = "x = 5 - 3"  # moved '-3' to RHS but kept the wrong sign (invalid)
    res = check_equation_step(prev, wrong)
    assert not res.ok
    # Either heuristic may trigger depending on string/structure:
    assert (
        "moved term without operation" in res.reason.lower() or "sign error" in res.reason.lower()
    ), f"Reason: {res.reason}"


def test_label_division_by_zero_risk():
    prev = "x = 2"
    wrong = "x/(x - 2) = 1"  # division by expression containing variable (domain risk)
    res = check_equation_step(prev, wrong)
    assert not res.ok
    assert "division-by-zero risk" in res.reason.lower(), f"Reason: {res.reason}"
