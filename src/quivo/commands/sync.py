"""quivo sync — clean-reinstall installed skills from the latest release.

Distinct from 'quivo update': this command refreshes skill *content* from
the latest GitHub Release. To upgrade the quivo CLI itself, use 'quivo update'.

Every sync is a clean reinstall: the previous install (recorded as per-skill
file manifests in .quivo-lock.json) is removed first, then the locked skills
are written fresh at the current layout. Targets therefore converge after
layout changes without accumulating stale copies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from quivo.adapters.base import ConflictError
from quivo.adapters.claude import ClaudeAdapter
from quivo.adapters.codex import CodexAdapter
from quivo.cleanup import cleanup_legacy, remove_recorded_files
from quivo.commands.init import _load_policy
from quivo.context import update_context_file
from quivo.lockfile import LOCK_FILE, load_lock, write_lock
from quivo.registry import load_registry, resolve_install_set
from quivo.release import ensure_skills_cache

console = Console()


def sync(
    cwd: Optional[Path] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Target directory (default: current directory).",
        exists=False,
    ),
    release: Optional[str] = typer.Option(
        None,
        "--release",
        help="Skills release tag to sync to (e.g. skills-v0.2.0). Default: latest.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing skill files quivo did not write itself.",
    ),
    policy: Optional[Path] = typer.Option(
        None,
        "--policy",
        help="Path to a policy.md file to inject into synced skill files.",
        exists=False,
    ),
    no_policy: bool = typer.Option(
        False,
        "--no-policy",
        help="Skip policy injection even if .quivo/policy.md or bundled policy exists.",
    ),
) -> None:
    """Clean-reinstall installed skill content from the latest GitHub Release.

    Reads .quivo-lock.json, removes the previous install, and re-installs
    every locked skill fresh. To upgrade the quivo CLI itself, use
    'quivo update'.
    """
    target = cwd or Path.cwd()

    lock = load_lock(target)
    if lock is None:
        console.print(f"[red]No {LOCK_FILE} found in {target}. Run 'quivo init' first.[/red]")
        raise typer.Exit(1)

    agent = lock.get("agent", "both")
    installed: dict[str, str] = {s["name"]: s["version"] for s in lock.get("skills", [])}

    # Obtain skills source
    try:
        skills_root = ensure_skills_cache(release_tag=release)
    except Exception as e:
        console.print(f"[red]Failed to obtain skills: {e}[/red]")
        raise typer.Exit(1)

    all_registry = {s.name: s for s in load_registry(skills_root)}

    try:
        policy_content = _load_policy(target, policy, no_policy, skills_root)
    except typer.BadParameter as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    adapters = []
    if agent in ("claude", "both"):
        adapters.append(ClaudeAdapter(target, force=force, policy_content=policy_content))
    if agent in ("codex", "both"):
        adapters.append(CodexAdapter(target, force=force, policy_content=policy_content))

    # Version diff (informational — everything is reinstalled regardless)
    to_update = [
        (name, old_ver, all_registry[name].version)
        for name, old_ver in installed.items()
        if name in all_registry and all_registry[name].version != old_ver
    ]

    # Clean reinstall: remove the previous install via its file manifest,
    # falling back to legacy-layout cleanup for locks that predate it.
    removed = remove_recorded_files(target, lock)
    removed += cleanup_legacy(target, installed.keys())
    if removed:
        console.print(f"[dim]Removed {len(removed)} path(s) from the previous install.[/dim]")

    for name in installed:
        if name not in all_registry:
            console.print(f"[yellow]'{name}' is no longer in the skill source — uninstalled.[/yellow]")

    skills_to_install = [all_registry[n] for n in installed if n in all_registry]
    install_set = resolve_install_set(skills_to_install, skills_root)
    if not install_set:
        console.print("[red]None of the locked skills exist in the skill source.[/red]")
        raise typer.Exit(1)

    if to_update:
        table = Table(title="Skills to Sync", show_header=True, header_style="bold magenta")
        table.add_column("Skill")
        table.add_column("Installed")
        table.add_column("Latest")
        for name, old_ver, new_ver in to_update:
            table.add_row(name, old_ver, f"[green]{new_ver}[/green]")
        console.print(table)
    else:
        console.print("[dim]All versions up to date — reinstalling for a clean layout.[/dim]")

    files_by_skill: dict[str, list[str]] = {}
    for skill in install_set:
        files_written: list[str] = []
        try:
            for adapter in adapters:
                adapter.remove_installed(skill.name)
                paths = adapter.install(skill)
                files_written.extend(str(p.relative_to(target)) for p in paths)
        except ConflictError as e:
            console.print(f"\n[red]{e}[/red]")
            console.print("\n[yellow]Rerun with --force to overwrite existing files.[/yellow]")
            raise typer.Exit(1)
        files_by_skill[skill.name] = files_written
        console.print(f"  [cyan]{skill.name}[/cyan] synced to {skill.version}")

    context_skills = [s for s in install_set if not s.internal]
    for adapter in adapters:
        update_context_file(target, adapter.context_file, context_skills)

    # Rebuild the lock from what was actually installed
    lock["skills"] = [
        {
            "name": s.name,
            "version": s.version,
            "internal": s.internal,
            "files": files_by_skill.get(s.name, []),
        }
        for s in install_set
    ]
    if release:
        lock["release"] = release
    write_lock(target, lock)

    console.print("\n[bold green]Sync complete.[/bold green]")
