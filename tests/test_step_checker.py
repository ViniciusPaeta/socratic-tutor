"""
Unit tests for the SymPy-backed step checker (MVP).
"""

from socratic_tutor.core.step_checker import (
    check_equation_step,
    check_expression_step,
)


def test_equation_equivalence_linear_two_steps():
    # 2*x + 3 = 11  ->  2*x = 8  ->  x = 4
    prev = "2*x + 3 = 11"
    step1 = "2*x = 8"
    step2 = "x = 4"

    res1 = check_equation_step(prev, step1)
    assert res1.ok, f"Expected valid step, got: {res1.reason}"

    res2 = check_equation_step(step1, step2)
    assert res2.ok, f"Expected valid step, got: {res2.reason}"


def test_expression_equivalence_distributive():
    # 2*(x+1) == 2*x + 2
    prev = "2*(x+1)"
    cur = "2*x + 2"

    res = check_expression_step(prev, cur)
    assert res.ok, f"Expected expressions to be equal, got: {res.reason}"


def test_equation_constant_factor_equivalence():
    # 4*x = 20  ->  x = 5 (mesmo conjunto de soluções; fator constante 4)
    prev = "4*x = 20"
    cur = "x = 5"
    res = check_equation_step(prev, cur)
    assert res.ok


def test_equation_reject_incorrect_division():
    # 2*x = 8  ->  x = 8 (erra ao dividir apenas um lado)
    prev = "2*x = 8"
    wrong = "x = 8"
    res = check_equation_step(prev, wrong)
    assert not res.ok
