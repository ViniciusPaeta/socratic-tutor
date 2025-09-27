"""
Command-line interface (CLI) for the Socratic Tutor (MVP).

Responsibilities
----------------
- Parse command-line options (path to problems file, student id/name).
- Load problems (YAML) into `Problem` objects.
- Let the user pick a problem to work on.
- Run an interactive loop:
    * read the student's next step,
    * validate it via the session,
    * print short feedback + a guiding question,
    * never reveal the answer.

Tech stack
----------
- Typer (Click-based) for ergonomic CLIs.
- Rich for nicer terminal output (panels, rules, colors).
- PyYAML to load example problems.

Entry point
-----------
The `pyproject.toml` exposes a console script:
    socratic-tutor = "socratic_tutor.cli:app"
so running `socratic-tutor` invokes this Typer application.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from .core.problems import Problem
from .core.tutor import TutorSession
from .metrics import Metrics

# Create a Typer app; Typer turns functions into CLI commands automatically.
app = typer.Typer(add_completion=False)
console = Console()


def load_problems(path: str) -> list[Problem]:
    """
    Load a list of problems from a YAML file.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Problems file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    return [Problem(**item) for item in data]


def _print_problem_list(problems: list[Problem]) -> None:
    """
    Pretty-print the available problems in a table for easy selection.
    """
    table = Table(title="Available Problems", show_lines=False)
    table.add_column("#", justify="right", style="bold")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Text", style="white")

    for i, p in enumerate(problems, start=1):
        table.add_row(str(i), p.id, p.type, p.text)
    console.print(table)


@app.command(name="")
def main(
    problems: Annotated[str, typer.Option("--problems", "-p", help="Path to YAML with problems.")],
    student: Annotated[str, typer.Option("--student", "-s", help="Student name/id.")] = "anonymous",
):
    """
    Start an interactive Socratic tutoring session.
    """
    # 1) Load problems & initialize metrics
    try:
        plist = load_problems(problems)
    except Exception as e:
        console.print(f"[red]Failed to load problems[/red]: {e}")
        raise typer.Exit(code=2) from e

    if not plist:
        console.print("[yellow]No problems found in the YAML file.[/yellow]")
        raise typer.Exit(code=1)

    ms = Metrics()  # SQLite file in CWD by default

    # 2) Let the user choose a problem
    console.rule("[bold]Socratic Tutor (MVP)")
    _print_problem_list(plist)
    try:
        idx_str = Prompt.ask("Choose a problem number", default="1")
        idx = int(idx_str)
        if idx < 1 or idx > len(plist):
            raise ValueError(f"Index out of range: {idx}")
    except Exception as e:
        console.print(f"[red]Invalid selection[/red]: {e}")
        raise typer.Exit(code=2) from e

    problem = plist[idx - 1]
    sess = TutorSession(problem, student=student, metrics=ms)

    # 3) Present the starting line
    console.print(
        Panel.fit(
            f"[bold]Problem:[/bold] {problem.text}\n[bold]Start:[/bold] {problem.prompt}",
            title=problem.id,
            border_style="cyan",
        )
    )
    console.print(
        "[dim]Type your next step (e.g., '2*x = 8' or '2*x + 2'). "
        "Type 'quit' or 'exit' to leave.[/dim]"
    )

    # 4) Interactive loop
    while True:
        attempt = Prompt.ask("Your next step").strip()
        if attempt.lower() in {"quit", "exit"}:
            console.print("[yellow]Session ended. Goodbye![/yellow]")
            raise typer.Exit(code=0)

        fb = sess.submit(attempt)

        # Feedback (never reveal the solution)
        if fb.ok:
            console.print(f"[green]{fb.message}[/green]")
        else:
            console.print(f"[red]{fb.message}[/red]")

        console.print(f"[cyan]{fb.next_question}[/cyan]")
        if fb.solved:
            console.print(
                "[green]Session complete — you achieved the target for this problem![/green]"
            )
            raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
