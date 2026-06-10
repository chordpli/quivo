"""quivo init — interactive skill installer."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from quivo.adapters.base import ConflictError
from quivo.adapters.claude import ClaudeAdapter
from quivo.adapters.codex import CodexAdapter
from quivo.cleanup import cleanup_legacy
from quivo.context import update_context_file
from quivo.registry import SkillMeta, load_registry, resolve_install_set
from quivo.release import ensure_skills_cache

console = Console()


class AgentChoice(str, Enum):
    claude = "claude"
    codex = "codex"
    both = "both"


LOCK_FILE = ".quivo-lock.json"


def _choose_agent_interactive() -> AgentChoice:
    console.print("\n[bold]Which AI agent are you installing skills for?[/bold]")
    console.print("  [cyan]1[/cyan]  claude  — Claude Code (.claude/skills/)")
    console.print("  [cyan]2[/cyan]  codex   — Codex CLI (.agents/skills/)")
    console.print("  [cyan]3[/cyan]  both    — Claude Code + Codex CLI")
    choice = Prompt.ask("Select", choices=["1", "2", "3", "claude", "codex", "both"], default="3")
    mapping = {"1": AgentChoice.claude, "2": AgentChoice.codex, "3": AgentChoice.both}
    if choice in mapping:
        return mapping[choice]
    return AgentChoice(choice)


def _load_policy(
    target: Path,
    policy_path: Optional[Path],
    no_policy: bool,
    skills_root: Optional[Path] = None,
) -> Optional[str]:
    """Return policy file content, or None if not applicable."""
    if no_policy:
        return None
    if policy_path is not None:
        if not policy_path.exists():
            raise typer.BadParameter(f"Policy file not found: {policy_path}", param_hint="--policy")
        return policy_path.read_text(encoding="utf-8")
    default_policy = target / ".quivo" / "policy.md"
    if default_policy.exists():
        return default_policy.read_text(encoding="utf-8")
    if skills_root is not None:
        bundled_policy = skills_root / ".quivo" / "policy.md"
        if not bundled_policy.exists():
            bundled_policy = skills_root.parent / ".quivo" / "policy.md"
        if bundled_policy.exists():
            return bundled_policy.read_text(encoding="utf-8")
    return None


def init(
    agent: Optional[AgentChoice] = typer.Option(
        None,
        "--agent",
        "-a",
        help="Target agent: claude, codex, or both.",
        case_sensitive=False,
    ),
    cwd: Optional[Path] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Target directory (default: current directory).",
        exists=False,
    ),
    here: bool = typer.Option(
        False,
        "--here",
        help="Install in the current directory (explicit alias for --dir .).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing skill files.",
    ),
    release: Optional[str] = typer.Option(
        None,
        "--release",
        help="Skills release tag to install (e.g. skills-v0.0.1). Default: latest.",
    ),
    policy: Optional[Path] = typer.Option(
        None,
        "--policy",
        help="Path to a policy.md file to inject into all installed skill files.",
        exists=False,
    ),
    no_policy: bool = typer.Option(
        False,
        "--no-policy",
        help="Skip policy injection even if .quivo/policy.md exists.",
    ),
) -> None:
    """Install quivo skills into the current project.

    Downloads skill content from GitHub Releases (or uses QUIVO_LOCAL_SKILLS
    for offline/dev mode). Use 'quivo sync' to refresh skill content,
    'quivo update' to upgrade the quivo CLI itself.
    """
    # Resolve target directory
    if here and cwd is not None:
        console.print("[red]Error: --here and --dir are mutually exclusive.[/red]")
        raise typer.Exit(1)
    target = (Path.cwd() if here else cwd) or Path.cwd()

    if agent is None:
        agent = _choose_agent_interactive()

    console.print(f"\n[bold green]Installing skills[/bold green] → agent=[cyan]{agent.value}[/cyan]  dir=[dim]{target}[/dim]\n")

    # Obtain skills source (cache or local override)
    try:
        skills_root = ensure_skills_cache(release_tag=release)
    except Exception as e:
        console.print(f"[red]Failed to obtain skills: {e}[/red]")
        raise typer.Exit(1)

    all_skills = load_registry(skills_root)
    public_skills = [s for s in all_skills if not s.internal]
    install_set = resolve_install_set(public_skills, skills_root)

    # Load policy content
    try:
        policy_content = _load_policy(target, policy, no_policy, skills_root)
    except typer.BadParameter as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    if policy_content:
        console.print("[dim]Policy injection: enabled (.quivo/policy.md)[/dim]")

    adapters = []
    if agent in (AgentChoice.claude, AgentChoice.both):
        adapters.append(ClaudeAdapter(target, force=force, policy_content=policy_content))
    if agent in (AgentChoice.codex, AgentChoice.both):
        adapters.append(CodexAdapter(target, force=force, policy_content=policy_content))

    results: list[dict] = []
    for skill in install_set:
        files_written: list[str] = []
        try:
            for adapter in adapters:
                paths = adapter.install(skill)
                files_written.extend(str(p.relative_to(target)) for p in paths)
        except ConflictError as e:
            console.print(f"\n[red]{e}[/red]")
            console.print("\n[yellow]Rerun with --force to overwrite existing files.[/yellow]")
            raise typer.Exit(1)
        results.append({"skill": skill, "files": files_written})

    # Print summary table
    table = Table(title="Installed Skills", show_header=True, header_style="bold magenta")
    table.add_column("Skill", style="cyan", no_wrap=True)
    table.add_column("Version")
    table.add_column("Internal")
    table.add_column("Files written")

    for r in results:
        skill: SkillMeta = r["skill"]
        table.add_row(
            skill.name,
            skill.version,
            "[dim]yes[/dim]" if skill.internal else "no",
            str(len(r["files"])),
        )

    console.print(table)

    # Clean up legacy install layouts (.codex/prompts|scripts, unprefixed dirs)
    removed = cleanup_legacy(target, [s.name for s in install_set])
    if removed:
        console.print(f"[dim]Removed {len(removed)} legacy install path(s).[/dim]")

    # Refresh agent context files (CLAUDE.md / AGENTS.md managed block)
    context_skills = [s for s in install_set if not s.internal]
    for adapter in adapters:
        path = update_context_file(target, adapter.context_file, context_skills)
        console.print(f"[dim]Context file updated: {path}[/dim]")

    # Write lock file
    lock_data = {
        "agent": agent.value,
        "release": release or "latest",
        "skills": [
            {"name": r["skill"].name, "version": r["skill"].version, "files": r["files"]}
            for r in results
            if not r["skill"].internal
        ],
    }
    lock_path = target / LOCK_FILE
    lock_path.write_text(json.dumps(lock_data, indent=2, ensure_ascii=False), encoding="utf-8")
    console.print(f"\n[dim]Lock file written: {lock_path}[/dim]")
    console.print("[bold green]Done.[/bold green]")
