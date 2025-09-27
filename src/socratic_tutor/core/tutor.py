"""
Socratic tutoring loop (MVP) with pattern-aware guiding questions and solved detection.
"""

from __future__ import annotations

from dataclasses import dataclass

from .patterns import (
    has_parentheses,
    is_linear_in,
    likely_needs_combining_like_terms,
)
from .problems import Problem
from .solved import is_problem_solved
from .step_checker import CheckResult, check_equation_step, check_expression_step


def guiding_question(prev: str, curr_attempt: str | None, problem: Problem) -> str:
    """
    Produce a Socratic prompt without giving away the answer, using simple patterns.
    """
    if problem.type == "equation":
        if is_linear_in("x", prev):
            if has_parentheses(prev):
                return "Could you expand or simplify parentheses to isolate x step by step?"
            return "What inverse operation could you apply equally to both sides to isolate x?"
        return "What transformation preserves equality on both sides of the equation?"
    else:
        if has_parentheses(prev):
            return "Try applying the distributive property before combining like terms."
        if likely_needs_combining_like_terms(prev):
            return "Can you combine like terms or simplify factors?"
        return "Can you rewrite the expression into an equivalent but simpler form?"


@dataclass
class StepFeedback:
    ok: bool
    message: str
    next_question: str
    solved: bool = False  # NEW: indicate terminal state


class TutorSession:
    def __init__(self, problem: Problem, student: str = "anonymous", metrics=None):
        self.problem = problem
        self.student = student
        self.current = problem.prompt.strip()
        self.steps = 0
        self.metrics = metrics

    def submit(self, attempt: str) -> StepFeedback:
        attempt = attempt.strip()
        self.steps += 1

        if self.problem.type == "equation":
            res: CheckResult = check_equation_step(self.current, attempt)
        else:
            res = check_expression_step(self.current, attempt)

        if res.ok:
            self.current = attempt
            message = "Good — that transformation is valid."
            ok = True
            err_type = "ok"
        else:
            message = f"That step seems invalid: {res.reason}"
            ok = False
            err_type = res.reason

        if self.metrics:
            self.metrics.record_step(
                problem_id=self.problem.id,
                student=self.student,
                ok=ok,
                error_type=err_type,
            )

        solved = ok and is_problem_solved(self.problem.target, self.current)
        next_q = (
            "Nice work — you've reached a solved form for the target. Type 'exit' to finish."
            if solved
            else guiding_question(self.current, attempt, self.problem)
        )

        return StepFeedback(
            ok=ok,
            message=message,
            next_question=next_q,
            solved=solved,
        )
