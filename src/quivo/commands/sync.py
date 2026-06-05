"""quivo sync — re-install skills that have changed since last install.

Distinct from 'quivo update': this command refreshes skill *content* from
the latest GitHub Release. To upgrade the quivo CLI itself, use 'quivo update'.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from quivo.adapters.base import ConflictError
from quivo.adapters.claude import ClaudeAdapter
from quivo.adapters.codex import CodexAdapter
from quivo.commands.init import _load_policy
from quivo.registry import load_registry, resolve_install_set
from quivo.release import ensure_skills_cache

console = Console()

LOCK_FILE = ".quivo-lock.json"


def _load_lock(target: Path) -> Optional[dict]:
    lock_path = target / LOCK_FILE
    if not lock_path.exists():
        return None
    with open(lock_path, encoding="utf-8") as f:
        return json.load(f)


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
        help="Overwrite existing skill files.",
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
    """Refresh installed skill content from the latest GitHub Release.

    Reads .quivo-lock.json, compares versions against the release manifest,
    and re-installs changed skills. To upgrade the quivo CLI itself, use
    'quivo update'.
    """
    target = cwd or Path.cwd()

    lock = _load_lock(target)
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

    # Compare versions using the manifest bundled in the cache
    manifest_path = skills_root / "manifest.json"
    if not manifest_path.exists():
        # Try parent in case skills_root points to a skills/ subdir
        manifest_path = skills_root.parent / "manifest.json"

    latest: dict[str, str] = {}
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        latest = {s["name"]: s["version"] for s in manifest.get("skills", [])}
    else:
        # Fall back: treat all as needing sync
        latest = {name: skill.version for name, skill in all_registry.items()}

    to_update = []
    for name, old_ver in installed.items():
        new_ver = latest.get(name)
        if new_ver and new_ver != old_ver:
            to_update.append((name, old_ver, new_ver))

    if not to_update:
        console.print("[green]All skills are up to date.[/green]")
        return

    try:
        policy_content = _load_policy(target, policy, no_policy, skills_root)
    except typer.BadParameter as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    table = Table(title="Skills to Sync", show_header=True, header_style="bold magenta")
    table.add_column("Skill")
    table.add_column("Installed")
    table.add_column("Latest")
    for name, old_ver, new_ver in to_update:
        table.add_row(name, old_ver, f"[green]{new_ver}[/green]")
    console.print(table)

    adapters = []
    if agent in ("claude", "both"):
        adapters.append(ClaudeAdapter(target, force=force, policy_content=policy_content))
    if agent in ("codex", "both"):
        adapters.append(CodexAdapter(target, force=force, policy_content=policy_content))

    skills_to_install = [all_registry[n] for n, _, _ in to_update if n in all_registry]
    install_set = resolve_install_set(skills_to_install, skills_root)

    for skill in install_set:
        try:
            for adapter in adapters:
                adapter.install(skill)
        except ConflictError as e:
            console.print(f"\n[red]{e}[/red]")
            console.print("\n[yellow]Rerun with --force to overwrite existing files.[/yellow]")
            raise typer.Exit(1)
        console.print(f"  [cyan]{skill.name}[/cyan] synced to {skill.version}")

    # Update lock file versions
    new_lock_skills = []
    for s in lock.get("skills", []):
        ver = latest.get(s["name"], s["version"])
        new_lock_skills.append({"name": s["name"], "version": ver})
    lock["skills"] = new_lock_skills
    if release:
        lock["release"] = release
    lock_path = target / LOCK_FILE
    lock_path.write_text(json.dumps(lock, indent=2, ensure_ascii=False), encoding="utf-8")

    console.print("\n[bold green]Sync complete.[/bold green]")
