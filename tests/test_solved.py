from socratic_tutor.core.solved import is_problem_solved


def test_is_problem_solved_linear():
    target = "solve for x"
    assert is_problem_solved(target, "x = 5") is True
    assert is_problem_solved(target, "5 = x") is True
    assert is_problem_solved(target, "2*x = 8") is False  # not isolated yet
