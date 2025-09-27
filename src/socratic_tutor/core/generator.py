"""
Tiny exercise generator (stub) for future adaptive sets.
"""

from __future__ import annotations


def generate_linear_isolation(n: int = 5) -> list[dict]:
    """
    Make toy linear problems: (i+2)*x + i = 2*(i+2) + i  -> solution x = 2.
    """
    items: list[dict] = []
    for i in range(n):
        a = i + 2
        b = i
        rhs = 2 * a + b
        items.append(
            {
                "id": f"lin-auto-{i}",
                "type": "equation",
                "text": "Solve for x",
                "prompt": f"{a}*x+{b} = {rhs}",
                "target": "solve for x",
            }
        )
    return items
