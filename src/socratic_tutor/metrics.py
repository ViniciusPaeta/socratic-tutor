"""
Lightweight metrics store (SQLite) for the Socratic Tutor (MVP).
"""

from __future__ import annotations

import sqlite3
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS steps (
  ts         REAL,   -- unix epoch seconds (float) when the step was recorded
  problem_id TEXT,   -- stable problem identifier (e.g., "lin-001")
  student    TEXT,   -- student identifier (nickname or account id)
  ok         INTEGER,-- 1 if the step was accepted, 0 otherwise
  error_type TEXT    -- "ok" on success; brief diagnostic label on failure
);
"""


class Metrics:
    def __init__(self, path: str = "metrics.sqlite3"):
        self.path = path
        self._ensure()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path)
        return con

    def _ensure(self) -> None:
        con = self._connect()
        try:
            con.execute(SCHEMA)
            con.commit()
        finally:
            con.close()

    def record_step(self, problem_id: str, student: str, ok: bool, error_type: str) -> None:
        con = self._connect()
        try:
            con.execute(
                "INSERT INTO steps (ts, problem_id, student, ok, error_type) "
                "VALUES (?, ?, ?, ?, ?)",
                (time.time(), problem_id, student, 1 if ok else 0, error_type),
            )
            con.commit()
        finally:
            con.close()

    def count_steps(self, problem_id: str | None = None, student: str | None = None) -> int:
        con = self._connect()
        try:
            q = "SELECT COUNT(*) FROM steps WHERE 1=1"
            params: list[object] = []
            if problem_id is not None:
                q += " AND problem_id = ?"
                params.append(problem_id)
            if student is not None:
                q += " AND student = ?"
                params.append(student)
            (n,) = con.execute(q, params).fetchone()
            return int(n)
        finally:
            con.close()

    def completion_rate(self, problem_id: str | None = None, student: str | None = None) -> float:
        """
        Approximate completion rate: fraction of accepted steps among all steps.
        """
        con = self._connect()
        try:
            q_total = "SELECT COUNT(*) FROM steps WHERE 1=1"
            q_ok = "SELECT COUNT(*) FROM steps WHERE ok = 1 AND 1=1"
            # FIX: annotate each variable on its own line
            params_total: list[object] = []
            params_ok: list[object] = []

            if problem_id is not None:
                q_total += " AND problem_id = ?"
                q_ok += " AND problem_id = ?"
                params_total.append(problem_id)
                params_ok.append(problem_id)
            if student is not None:
                q_total += " AND student = ?"
                q_ok += " AND student = ?"
                params_total.append(student)
                params_ok.append(student)

            (total,) = con.execute(q_total, params_total).fetchone()
            (ok_count,) = con.execute(q_ok, params_ok).fetchone()

            total = int(total)
            ok_count = int(ok_count)
            return (ok_count / total) if total else 0.0
        finally:
            con.close()
