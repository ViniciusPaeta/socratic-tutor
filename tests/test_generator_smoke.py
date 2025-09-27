from socratic_tutor.tools.generate import plan_from_errors


def test_plan_from_errors_builds_non_empty():
    plan = plan_from_errors(["one-sided operation", "bad distributive?"], n_each=2)
    assert isinstance(plan, list) and len(plan) >= 2
    assert all("type" in x and "prompt" in x for x in plan)
