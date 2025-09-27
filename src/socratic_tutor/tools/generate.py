"""
Adaptive exercise generator (MVP).

Usage:
  python -m socratic_tutor.tools.generate --student "Paeta" --out examples/adaptive_Paeta.yaml

Logic (simple rules):
- one-sided operation  -> linear equations isolating x (smaller steps)
- bad distributive?    -> equations & expressions with parentheses
- expressions not equal -> simple expression rewrites (distribute/combine like terms)

If no metrics exist for the student, fall back to a blended set.
"""

from __future__ import annotations

import argparse
import sqlite3
from collections.abc import Iterable
from pathlib import Path

import yaml

DB_PATH_DEFAULT = "metrics.sqlite3"


def top_errors_for_student(
    student: str, db_path: str = DB_PATH_DEFAULT, top_k: int = 2
) -> list[str]:
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(
            """
            SELECT error_type, COUNT(*) as c
            FROM steps
            WHERE ok = 0 AND student = ?
            GROUP BY error_type
            ORDER BY c DESC
            LIMIT ?
            """,
            (student, top_k),
        )
        rows = cur.fetchall()
        return [r[0] for r in rows]
    finally:
        con.close()


# ---- Problem templates (YAML dicts) ---------------------------------


def make_linear_isolation_set(n: int = 5) -> list[dict]:
    items: list[dict] = []
    # Make problems of the form a*x + b = rhs with solution x = 2
    for i in range(n):
        a = i + 2
        b = i
        rhs = 2 * a + b
        items.append(
            {
                "id": f"lin-auto-{i}",
                "type": "equation",
                "text": "Solve for x.",
                "prompt": f"{a}*x + {b} = {rhs}",
                "target": "solve for x",
            }
        )
    return items


def make_distributive_equations(n: int = 5) -> list[dict]:
    items: list[dict] = []
    # Generate c*(x - d) = c*k with a simple target x = d + k
    for i in range(n):
        c = i + 2
        d = i % 3 + 1
        k = (i % 3) + 2
        items.append(
            {
                "id": f"dist-eq-{i}",
                "type": "equation",
                "text": "Isolate x (distribute if needed).",
                "prompt": f"{c}*(x - {d}) = {c*(k)}",
                "target": "solve for x",
            }
        )
    return items


def make_distributive_expressions(n: int = 5) -> list[dict]:
    items: list[dict] = []
    for i in range(n):
        a = i + 2
        items.append(
            {
                "id": f"dist-expr-{i}",
                "type": "expression",
                "text": "Rewrite using the distributive property.",
                "prompt": f"{a}*(x+1)",
                "target": "simplify",
            }
        )
    return items


def blended_default(n_each: int = 3) -> list[dict]:
    return (
        make_linear_isolation_set(n_each)
        + make_distributive_equations(n_each)
        + make_distributive_expressions(n_each)
    )


def plan_from_errors(errors: Iterable[str], n_each: int = 4) -> list[dict]:
    """
    Map error labels to problem templates.
    """
    plan: list[dict] = []
    for e in errors:
        e_low = e.lower()
        if "one-sided operation" in e_low:
            plan += make_linear_isolation_set(n_each)
        elif "bad distributive" in e_low:
            plan += make_distributive_equations(n_each)
            plan += make_distributive_expressions(n_each)
        elif "expressions not equal" in e_low:
            plan += make_distributive_expressions(n_each)
        # other labels can be mapped here
    if not plan:
        plan = blended_default(3)
    return plan


def main():
    ap = argparse.ArgumentParser(description="Generate an adaptive exercise set from metrics.")
    ap.add_argument("--student", "-s", required=True, help="Student name/id (from metrics).")
    ap.add_argument("--out", "-o", required=True, help="Output YAML path.")
    ap.add_argument("--db", default=DB_PATH_DEFAULT, help="Path to metrics SQLite.")
    ap.add_argument("--each", type=int, default=4, help="Items per focused bucket.")
    args = ap.parse_args()

    errors = top_errors_for_student(args.student, args.db, top_k=3)
    problems = plan_from_errors(errors, n_each=args.each)

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8") as f:
        yaml.safe_dump(problems, f, sort_keys=False, allow_unicode=True)

    print(f"[OK] Wrote {len(problems)} problems to {outp}")


if __name__ == "__main__":
    main()
