"""quivo update — upgrade the quivo CLI itself to the latest release.

Checks the GitHub repo for a newer ``cli-v*`` tag and, when one is found,
refreshes the uv/uvx cache (or reinstalls via ``uv tool`` / ``pipx``) so the
next ``quivo`` invocation runs the new version. Designed for the common case
where ``quivo`` is run through a ``uvx --from git+...`` alias.

To refresh installed *skill content* (not the CLI), use 'quivo sync'.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

import quivo
from quivo.release import _gh_get_json, _repo as resolve_repo

console = Console()

CLI_TAG_PREFIX = "cli-v"

# Exit codes (mirrors spec-kit's self-upgrade conventions)
EXIT_OK = 0
EXIT_RESOLVE_ERROR = 1
EXIT_VERIFY_MISMATCH = 2
EXIT_INSTALLER_MISSING = 3
EXIT_TIMEOUT = 124


def _git_url(repo: str) -> str:
    return f"git+https://github.com/{repo}.git"


def _fetch_latest_cli_tag(repo: str) -> Optional[str]:
    """Return the newest ``cli-v*`` tag in the repo, or None if there are none."""
    data = _gh_get_json(f"https://api.github.com/repos/{repo}/tags?per_page=100")
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected tags response shape: {type(data).__name__}")
    cli_tags = [t["name"] for t in data if t.get("name", "").startswith(CLI_TAG_PREFIX)]
    if not cli_tags:
        return None
    try:
        from packaging.version import Version

        return max(cli_tags, key=lambda t: Version(t.removeprefix(CLI_TAG_PREFIX)))
    except Exception:
        return sorted(cli_tags)[-1]


def _is_newer(latest_ver: str, current: str) -> bool:
    try:
        from packaging.version import Version

        return Version(latest_ver) > Version(current)
    except Exception:
        return latest_ver != current


def _executable_path() -> str:
    """Best-effort resolved path of the running ``quivo`` executable."""
    candidate = shutil.which("quivo") or sys.argv[0] or sys.executable
    try:
        return str(Path(candidate).resolve())
    except OSError:
        return candidate


def _detect_install_method() -> str:
    """Classify how quivo is installed: 'uv-tool', 'pipx', 'uvx', or 'unknown'.

    Heuristics based on the resolved executable / interpreter path. The common
    alias case (``uvx --from git+...``) lands in the uv cache and is treated as
    'uvx'.
    """
    paths = " ".join(
        p.lower()
        for p in (_executable_path(), sys.executable, sys.prefix)
    )
    if "pipx" in paths:
        return "pipx"
    if "uv/tools" in paths or "uv\\tools" in paths:
        return "uv-tool"
    if "/uv/" in paths or "\\uv\\" in paths or "archive-v" in paths or "uvx" in paths:
        return "uvx"
    return "unknown"


def _build_argv(method: str, repo: str, tag: str) -> list[str]:
    """Build the subprocess argv that performs the upgrade for an install method."""
    spec = f"{_git_url(repo)}@{tag}"
    if method == "uv-tool":
        return ["uv", "tool", "install", "--force", "--from", spec, "quivo"]
    if method == "pipx":
        return ["pipx", "install", "--force", "--spec", spec, "quivo"]
    # uvx / unknown — warm the uv cache for the pinned tag.
    return ["uvx", "--refresh", "--from", spec, "quivo", "--version"]


def _run(argv: list[str]) -> int:
    """Run the upgrade command, streaming output. Returns its exit code.

    The environment is passed through unchanged: installing from a private
    fork relies on the user's existing git credentials.
    """
    console.print(f"[dim]$ {' '.join(argv)}[/dim]")
    try:
        proc = subprocess.run(argv, timeout=600)
        return proc.returncode
    except FileNotFoundError:
        console.print(f"[red]Installer not found: '{argv[0]}' is not on PATH.[/red]")
        raise typer.Exit(EXIT_INSTALLER_MISSING)
    except subprocess.TimeoutExpired:
        console.print("[red]Upgrade timed out after 600s.[/red]")
        raise typer.Exit(EXIT_TIMEOUT)


def _verify(repo: str, tag: str, expected_ver: str) -> bool:
    """Run the freshly-cached binary and confirm it reports ``expected_ver``."""
    spec = f"{_git_url(repo)}@{tag}"
    argv = ["uvx", "--from", spec, "quivo", "--version"]
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    reported = (out.stdout or out.stderr).strip()
    return expected_ver in reported


def update(
    tag: Optional[str] = typer.Option(
        None,
        "--tag",
        help="Pin a specific CLI release tag (e.g. cli-v0.2.0). Default: latest.",
    ),
    check: bool = typer.Option(
        False,
        "--check",
        help="Only report whether a newer version exists; do not upgrade.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would run without making any changes.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Re-run the upgrade even if already on the latest version.",
    ),
) -> None:
    """Upgrade the quivo CLI itself to the latest GitHub release.

    Resolves the newest ``cli-v*`` tag, then refreshes the uv/uvx cache (or
    reinstalls via uv tool / pipx) so the next ``quivo`` run uses it. To refresh
    installed skill *content* instead, use 'quivo sync'.
    """
    repo = resolve_repo()
    current = quivo.__version__

    console.print(f"[dim]Current quivo version: {current}[/dim]")

    # --- Resolve target tag ---
    if tag:
        target_tag = tag if tag.startswith(CLI_TAG_PREFIX) else f"{CLI_TAG_PREFIX}{tag.lstrip('v')}"
        target_ver = target_tag.removeprefix(CLI_TAG_PREFIX)
        console.print(f"[dim]Pinned target: {target_tag}[/dim]")
    else:
        console.print(f"[dim]Checking https://github.com/{repo} for cli-v* tags...[/dim]")
        try:
            latest = _fetch_latest_cli_tag(repo)
        except RuntimeError as e:
            console.print(f"[red]{e}[/red]")
            console.print("[yellow]Set GH_TOKEN if the repo is private or you hit rate limits.[/yellow]")
            raise typer.Exit(EXIT_RESOLVE_ERROR)
        if latest is None:
            console.print(f"[yellow]No '{CLI_TAG_PREFIX}*' tags found in {repo}.[/yellow]")
            console.print("To force-refresh from the default branch:")
            console.print(
                f"  [cyan]uvx --refresh --from {_git_url(repo)} quivo --version[/cyan]"
            )
            raise typer.Exit(EXIT_OK)
        target_tag = latest
        target_ver = target_tag.removeprefix(CLI_TAG_PREFIX)

    # --- Up-to-date short-circuit ---
    newer = _is_newer(target_ver, current)
    if not newer and not force and not tag:
        console.print(
            f"\n[bold green]Up to date.[/bold green] quivo {current} matches latest tag {target_tag}."
        )
        raise typer.Exit(EXIT_OK)

    if newer:
        console.print(
            f"\n[bold yellow]New version available: {target_ver}[/bold yellow] (current: {current})"
        )
    elif not tag:
        console.print(f"\n[dim]Already on {current}; re-running due to --force.[/dim]")

    if check:
        console.print(f"\nTo upgrade, run: [cyan]quivo update[/cyan]")
        raise typer.Exit(EXIT_OK)

    # --- Perform the upgrade ---
    method = _detect_install_method()
    argv = _build_argv(method, repo, target_tag)
    console.print(f"[dim]Install method: {method}[/dim]")

    if dry_run:
        console.print("\n[bold]Dry run — would execute:[/bold]")
        console.print(f"  [cyan]{' '.join(argv)}[/cyan]")
        raise typer.Exit(EXIT_OK)

    rc = _run(argv)
    if rc != 0:
        console.print(f"[red]Upgrade command exited with code {rc}.[/red]")
        raise typer.Exit(rc)

    # --- Verify ---
    if _verify(repo, target_tag, target_ver):
        console.print(f"\n[bold green]Upgraded to quivo {target_ver}.[/bold green]")
    else:
        console.print(
            f"\n[yellow]Refreshed {target_tag}, but could not confirm the version.[/yellow]"
        )

    # --- Guidance for alias users ---
    if method in ("uvx", "unknown"):
        console.print(
            "\n[dim]If your shell alias pins a tag, update it to "
            f"@{target_tag}. An unpinned alias picks up the latest on the next "
            "[/dim][cyan]uvx --refresh[/cyan][dim] run.[/dim]"
        )
