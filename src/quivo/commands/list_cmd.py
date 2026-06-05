"""quivo list — show installed skills from .quivo-lock.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

console = Console()

LOCK_FILE = ".quivo-lock.json"


def list_skills(
    cwd: Optional[Path] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Target directory (default: current directory).",
        exists=False,
    ),
) -> None:
    """List installed quivo skills."""
    target = cwd or Path.cwd()
    lock_path = target / LOCK_FILE

    if not lock_path.exists():
        console.print(f"[yellow]No {LOCK_FILE} found in {target}. Run 'quivo init' first.[/yellow]")
        raise typer.Exit(0)

    with open(lock_path, encoding="utf-8") as f:
        lock = json.load(f)

    agent = lock.get("agent", "unknown")
    skills = lock.get("skills", [])

    console.print(f"\n[bold]Installed skills[/bold]  (agent=[cyan]{agent}[/cyan])\n")

    if not skills:
        console.print("[dim]No skills installed.[/dim]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Skill", style="cyan", no_wrap=True)
    table.add_column("Version")

    for s in skills:
        table.add_row(s["name"], s.get("version", "?"))

    console.print(table)
