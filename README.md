
socratic-tutor — A Socratic, Step-by-Step Algebra Tutor (MVP)
=============================================================

Abstract
--------
`socratic-tutor` is a minimal yet rigorous tutoring system for introductory Algebra and Functions.
The tutor engages the learner in a Socratic dialogue: it **never reveals solutions**, and instead
validates each step that the student proposes, responding only with **guiding questions**.
Correctness is checked symbolically using SymPy, and interaction data is recorded for analysis.
The project includes a command-line interface (CLI), a lightweight FastAPI service, a Streamlit
dashboard for metrics exploration, and an adaptive item generator that produces practice sets
targeted to a learner’s weaknesses.

Motivation
----------
High-quality formative feedback requires timely, actionable signals without shortcutting the
learner’s cognitive work. By validating algebraic steps rather than full solutions, this MVP
pursues four goals:
1) provide immediate, principled feedback; 2) avoid over-scaffolding (no answers given);
3) collect process data for research (error profiles, completion dynamics); and 4) support
data-driven adaptation of practice sets.

Key Capabilities (MVP)
----------------------
- **Socratic loop**: accepts a student’s next step and responds with a guiding question only.
- **Symbolic validation** (SymPy):
  - Expressions: `prev` and `current` are equal iff their difference simplifies to zero.
  - Equations: equivalence up to a non-zero constant factor is accepted (e.g., `2*x=8` ↔ `x=4`).
  - Robust randomized check (no zero/non-zero mismatches; requires consistent proportionality).
- **Lenient parsing**: supports *implicit multiplication* (e.g., `3x`, `2(x+1)`).
- **Error classification**: heuristic labels for invalid steps (e.g., `"one-sided operation"`, `"bad distributive?"`, `"expressions not equal"`, `"parse error: ..."`) to power analytics and hints.
- **Pattern-aware hints**: guiding questions driven by simple algebraic patterns (linearity, presence of parentheses, likely need to combine like terms).
- **Solved-state detection**: for targets like *solve for x*, recognizes `x = <expr>` / `<expr> = x` without printing the solution.
- **Metrics**: SQLite logger capturing per-step outcomes and error types.
- **Dashboard**: Streamlit app that summarizes totals, completion rates, and top error labels.
- **API**: FastAPI endpoints for step checking and hint generation.
- **Adaptive generator**: creates targeted problem sets from a learner’s error profile.

System Overview
---------------
### Architecture
- **CLI** (`socratic_tutor/cli.py`): interactive loop; renders problems; records metrics.
- **Core** (`socratic_tutor/core`):
  - `step_checker.py` — parsing & equivalence; classification integration.
  - `patterns.py` — lightweight pattern detectors for hints (linear, parentheses, complexity).
  - `error_labels.py` — heuristics that map invalid steps to concise, actionable labels.
  - `solved.py` — conservative solved-state detection (shape-based).
  - `problems.py` — problem model and YAML loader.
  - `tutor.py` — session orchestration and question generation.
  - `generator.py` — simple item templates for adaptive practice.
- **Analytics & UX**
  - `metrics.py` — SQLite schema and helper methods.
  - `app/dashboard.py` — Streamlit dashboard for exploration.
- **Service Layer**
  - `api/main.py` — FastAPI endpoints (`/check/equation`, `/check/expression`, `/hint`).

### Algorithms & Design Notes
- **Equation equivalence** (`A = B` ↔ `C = D`):
  - Let `d1 = simplify(A-B)`, `d2 = simplify(C-D)`.
  - Accept if `d1 == d2`, or `d1 == k*d2` for constant `k ≠ 0`.
  - Otherwise, sample assignments; reject on any zero/non-zero mismatch; accept only if ratios
    are consistent across multiple non-zero samples (cross-multiplication check).
- **Implicit multiplication parsing**: `parse_expr` with `implicit_multiplication_application`.
- **Error classification** examples:
  - *one-sided operation* — only LHS or RHS changed.
  - *bad distributive?* — expansion fixes equality but the student’s step was invalid.
  - *expressions not equal* — expression rewrite not equivalence-preserving.
  - *parse error* — non-parsable input (surface-form feedback).
- **Solved detection**: purely shape-based for *solve for x* targets; no `solve()` shortcut.
- **Heuristic hinting**: avoids revealing operations; phrases nudge towards inverse operations,
  distribution, or combining like terms depending on detected patterns.

Installation
------------
It is assumed you use a Python 3.10+ virtual environment.
```
python -m pip install -U pip
pip install -e ".[dev]"
```

Quick Start (CLI)
-----------------
```
socratic-tutor --problems examples/equations.yaml --student "YourName"
```
Example steps for a linear problem:
- `2*x + 3 = 11` → `2*x = 8` → `x = 4`
- `3*(x - 2) = 9` → `3x - 6 = 9` → `x - 2 = 3` → `x = 5`

API (FastAPI)
-------------
Run the API:
```
uvicorn socratic_tutor.api.main:app --reload --port 8000
```
Endpoints (JSON):
- `POST /check/equation` — `{ "previous": "...", "current": "..." }`
- `POST /check/expression` — `{ "previous": "...", "current": "..." }`
- `POST /hint` — `{ "prev": "...", "problem_type": "equation"|"expression" }`

Dashboard (Streamlit)
---------------------
Launch:
```
streamlit run app/dashboard.py
```
Dashboard shows:
- Total steps and completion rate
- Top error labels
- Per-student and per-problem OK rates

Metrics Schema
--------------
SQLite table: `steps(ts REAL, problem_id TEXT, student TEXT, ok INTEGER, error_type TEXT)`.
- `ok` is 1 if the step was accepted, 0 otherwise.
- `error_type` stores `"ok"` on success; on failure, a short diagnostic label.

Adaptive Generator
------------------
Generate a targeted practice set from recorded errors:
```
python -m socratic_tutor.tools.generate --student "YourName" --out examples/adaptive_YourName.yaml
```
Heuristics (MVP):
- *one-sided operation* → linear isolation problems.
- *bad distributive?* → equations/expressions requiring distribution.
- *expressions not equal* → simpler expression rewrites.

Testing & Quality
-----------------
- Unit tests cover step checking, implicit multiplication, error labeling, patterns,
  solved-state detection, and generator plumbing.
- Style & lint: Ruff and Black.
```
ruff check src tests
black --check src tests
pytest -q
```

Reproducibility & Data
----------------------
- The repository fixes line length and style via Ruff/Black; tests are deterministic.
- Metrics are stored locally in `metrics.sqlite3`. For research or production, export and
  anonymize as needed.

Scope, Limitations & Future Work
--------------------------------
- The MVP handles single-variable algebraic manipulation and simple expression
  transformations. It does not attempt multi-step solution synthesis or proof.
- False positives/negatives in equivalence can occur for edge cases; the classifier and
  randomized checks aim to minimize those while keeping the system explainable.
- Next steps:
  1) richer error taxonomy (e.g., sign mistakes, cross-multiplication pitfalls, domain
     constraints such as division by zero);
  2) more granular hinting tied to labeled errors;
  3) expanded content: factorization, simple linear systems, algebraic fractions;
  4) session-aware API; 5) content difficulty calibration; 6) teacher analytics.

Ethical Considerations
----------------------
- The system is designed to *resist* giving direct answers; it aims to support learning,
  not shortcut it.
- Logged data should be handled under appropriate privacy guidelines. Avoid collecting
  personal identifiers beyond the student nickname used for metrics.

Citing / Related Work
---------------------
- SymPy: Meurer et al., *SymPy: symbolic computing in Python*, PeerJ Computer Science (2017).
- Socratic tutoring: classic approaches in intelligent tutoring systems and formative feedback.
  This MVP focuses on verifiable, symbolic equivalence rather than language-model hints.

Repository Layout
-----------------
- `src/socratic_tutor/` — core package
- `examples/` — sample YAML problems (and adaptive outputs)
- `tests/` — unit tests
- `app/` — dashboard sources
- `pyproject.toml`, `Makefile` — build & developer tasks
- `README.md` — this document (or its Markdown variant)

License
-------
MIT License (recommended). Add a `LICENSE` file to the repository if appropriate.
