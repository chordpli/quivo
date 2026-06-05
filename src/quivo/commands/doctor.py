"""quivo doctor — check required tools and quivo environment."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

import quivo
from quivo.release import CACHE_BASE, cache_size_bytes, list_cached_releases

console = Console()

REQUIRED_TOOLS = [
    ("uv", "Python package manager (https://docs.astral.sh/uv/)"),
    ("gh", "GitHub CLI (https://cli.github.com/)"),
    ("aws", "AWS CLI v2 (https://aws.amazon.com/cli/)"),
    ("mysql", "MySQL client (brew install mysql-client)"),
]


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n:.1f} TB"


def doctor(
    cwd: Optional[Path] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Project directory to check for policy file (default: current directory).",
        exists=False,
    ),
) -> None:
    """Check required tools, quivo version, cache state, and policy file.

    Use 'quivo update' to upgrade the quivo CLI to the latest release.
    """
    target = cwd or Path.cwd()

    # --- quivo environment section ---
    console.print("\n[bold]quivo environment[/bold]\n")

    env_table = Table(show_header=False, box=None, padding=(0, 2))
    env_table.add_column("Key", style="cyan", no_wrap=True)
    env_table.add_column("Value")

    env_table.add_row("quivo version", quivo.__version__)

    cached = list_cached_releases()
    latest_cached = cached[-1] if cached else "[dim]none[/dim]"
    size = cache_size_bytes()
    env_table.add_row("cache dir", str(CACHE_BASE))
    env_table.add_row("cache size", _human_size(size) if size else "[dim]empty[/dim]")
    env_table.add_row("latest cached release", latest_cached)
    env_table.add_row(
        "cached releases",
        ", ".join(cached) if cached else "[dim]none[/dim]",
    )

    policy_path = target / ".quivo" / "policy.md"
    policy_status = (
        f"[green]found[/green] ({policy_path})" if policy_path.exists()
        else "[dim]not found[/dim]"
    )
    env_table.add_row("policy file", policy_status)

    console.print(env_table)

    # --- tools section ---
    console.print("\n[bold]Required tools[/bold]\n")

    tools_table = Table(show_header=True, header_style="bold magenta")
    tools_table.add_column("Tool", style="cyan", no_wrap=True)
    tools_table.add_column("Status", no_wrap=True)
    tools_table.add_column("Note")

    all_ok = True
    for tool, note in REQUIRED_TOOLS:
        path = shutil.which(tool)
        if path:
            tools_table.add_row(tool, "[green]OK[/green]", path)
        else:
            tools_table.add_row(tool, "[red]MISSING[/red]", note)
            all_ok = False

    console.print(tools_table)

    if all_ok:
        console.print("\n[bold green]All tools are available.[/bold green]")
    else:
        console.print(
            "\n[yellow]Some tools are missing. "
            "Install them before using the related skills.[/yellow]"
        )
        raise typer.Exit(1)
