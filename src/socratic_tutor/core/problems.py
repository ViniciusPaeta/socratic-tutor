"""
Problem model for the Socratic Tutor (MVP).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ProblemType = Literal["equation", "expression"]


@dataclass
class Problem:
    """
    A single problem definition consumed by the tutor session.
    """

    id: str
    type: ProblemType
    text: str  # concise display text for the UI/CLI
    prompt: str  # initial "state" handed to the student
    target: str | None = None  # high-level objective (not enforced in MVP)
