"""
FastAPI server exposing step checking endpoints and hinting.

Endpoints:
- POST /check/equation
- POST /check/expression
- POST /hint
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from ..core.problems import Problem
from ..core.step_checker import check_equation_step, check_expression_step
from ..core.tutor import guiding_question


class EquationCheckRequest(BaseModel):
    previous: str
    current: str


class ExpressionCheckRequest(BaseModel):
    previous: str
    current: str


class CheckResponse(BaseModel):
    ok: bool
    reason: str
    normalized_current: str
    normalized_previous: str


class HintRequest(BaseModel):
    prev: str
    problem_type: str  # "equation" | "expression"


class HintResponse(BaseModel):
    hint: str


app = FastAPI(title="Socratic Tutor API", version="0.1.0")


@app.post("/check/equation", response_model=CheckResponse)
def check_equation(req: EquationCheckRequest):
    res = check_equation_step(req.previous, req.current)
    return CheckResponse(
        ok=res.ok,
        reason=res.reason,
        normalized_current=res.normalized_current,
        normalized_previous=res.normalized_previous,
    )


@app.post("/check/expression", response_model=CheckResponse)
def check_expression(req: ExpressionCheckRequest):
    res = check_expression_step(req.previous, req.current)
    return CheckResponse(
        ok=res.ok,
        reason=res.reason,
        normalized_current=res.normalized_current,
        normalized_previous=res.normalized_previous,
    )


@app.post("/hint", response_model=HintResponse)
def hint(req: HintRequest):
    """Return a guiding question for the given current line and problem type."""
    # Construímos um Problem mínimo apenas para acionar a lógica do hint.
    p = Problem(id="adhoc", type=req.problem_type, text="", prompt=req.prev)
    return HintResponse(hint=guiding_question(req.prev, None, p))
