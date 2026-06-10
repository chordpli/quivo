"""quivo init — interactive skill installer."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from quivo.adapters.base import BaseAdapter, ConflictError
from quivo.adapters.commands_base import CommandsBaseAdapter
from quivo.adapters.claude import ClaudeAdapter
from quivo.adapters.codex import CodexAdapter
from quivo.adapters.cursor import CursorAdapter
from quivo.adapters.gemini import GeminiAdapter
from quivo.adapters.qwen import QwenAdapter
from quivo.adapters.windsurf import WindsurfAdapter
from quivo.cleanup import cleanup_legacy, remove_recorded_files
from quivo.context import update_context_file
from quivo.lockfile import load_lock, write_lock
from quivo.registry import SkillMeta, load_registry, resolve_install_set
from quivo.release import ensure_skills_cache

console = Console()

# Ordered list of all supported agent names (determines interactive menu order).
ALL_AGENTS = ["claude", "codex", "gemini", "qwen", "windsurf", "cursor"]


class AgentChoice(str, Enum):
    claude = "claude"
    codex = "codex"
    gemini = "gemini"
    qwen = "qwen"
    windsurf = "windsurf"
    cursor = "cursor"
    both = "both"   # backward-compat alias: claude + codex
    all = "all"     # all supported agents


def _build_adapters(
    agent: AgentChoice,
    target: Path,
    force: bool,
    policy_content: Optional[str],
) -> list[BaseAdapter | CommandsBaseAdapter]:
    """Instantiate the adapters implied by the agent choice."""
    factory: dict[str, BaseAdapter | CommandsBaseAdapter] = {
        "claude":    ClaudeAdapter(target, force=force, policy_content=policy_content),
        "codex":     CodexAdapter(target, force=force, policy_content=policy_content),
        "gemini":    GeminiAdapter(target, force=force, policy_content=policy_content),
        "qwen":      QwenAdapter(target, force=force, policy_content=policy_content),
        "windsurf":  WindsurfAdapter(target, force=force, policy_content=policy_content),
        "cursor":    CursorAdapter(target, force=force, policy_content=policy_content),
    }
    if agent == AgentChoice.both:
        names = ["claude", "codex"]
    elif agent == AgentChoice.all:
        names = ALL_AGENTS
    else:
        names = [agent.value]
    return [factory[n] for n in names]


def _choose_agent_interactive() -> AgentChoice:
    console.print("\n[bold]Which AI agent are you installing skills for?[/bold]")
    console.print("  [cyan]1[/cyan]  claude   — Claude Code (.claude/skills/)")
    console.print("  [cyan]2[/cyan]  codex    — Codex CLI (.agents/skills/)")
    console.print("  [cyan]3[/cyan]  gemini   — Gemini CLI (.gemini/commands/)")
    console.print("  [cyan]4[/cyan]  qwen     — Qwen Code (.qwen/commands/)")
    console.print("  [cyan]5[/cyan]  windsurf — Windsurf (.windsurf/workflows/)")
    console.print("  [cyan]6[/cyan]  cursor   — Cursor (.cursor/skills/)")
    console.print("  [cyan]7[/cyan]  both     — Claude Code + Codex")
    console.print("  [cyan]8[/cyan]  all      — All agents")
    valid = ["1", "2", "3", "4", "5", "6", "7", "8"] + ALL_AGENTS + ["both", "all"]
    choice = Prompt.ask("Select", choices=valid, default="7")
    mapping = {
        "1": AgentChoice.claude,
        "2": AgentChoice.codex,
        "3": AgentChoice.gemini,
        "4": AgentChoice.qwen,
        "5": AgentChoice.windsurf,
        "6": AgentChoice.cursor,
        "7": AgentChoice.both,
        "8": AgentChoice.all,
    }
    return mapping.get(choice, AgentChoice(choice))


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
        help="Target agent: claude, codex, gemini, qwen, windsurf, cursor, both, or all.",
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
    if here and cwd is not None:
        console.print("[red]Error: --here and --dir are mutually exclusive.[/red]")
        raise typer.Exit(1)
    target = (Path.cwd() if here else cwd) or Path.cwd()

    if agent is None:
        agent = _choose_agent_interactive()

    console.print(f"\n[bold green]Installing skills[/bold green] → agent=[cyan]{agent.value}[/cyan]  dir=[dim]{target}[/dim]\n")

    try:
        skills_root = ensure_skills_cache(release_tag=release)
    except Exception as e:
        console.print(f"[red]Failed to obtain skills: {e}[/red]")
        raise typer.Exit(1)

    all_skills = load_registry(skills_root)
    public_skills = [s for s in all_skills if not s.internal]
    install_set = resolve_install_set(public_skills, skills_root)

    try:
        policy_content = _load_policy(target, policy, no_policy, skills_root)
    except typer.BadParameter as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    if policy_content:
        console.print("[dim]Policy injection: enabled (.quivo/policy.md)[/dim]")

    adapters = _build_adapters(agent, target, force, policy_content)

    # Clean reinstall: remove whatever a previous install wrote (recorded in
    # the lock's file manifests), plus pre-manifest legacy layouts, before
    # writing the current layout fresh.
    old_lock = load_lock(target)
    removed: list[Path] = []
    if old_lock:
        removed += remove_recorded_files(target, old_lock)
    legacy_names = {s.name for s in install_set}
    if old_lock:
        legacy_names |= {s["name"] for s in old_lock.get("skills", []) if s.get("name")}
    removed += cleanup_legacy(target, legacy_names)
    if removed:
        console.print(f"[dim]Removed {len(removed)} path(s) from the previous install.[/dim]")

    results: list[dict] = []
    for skill in install_set:
        files_written: list[str] = []
        try:
            for adapter in adapters:
                # Respect the skill's declared agent support list.
                if skill.agents and adapter.agent_name not in skill.agents:
                    continue
                paths = adapter.install(skill)
                files_written.extend(str(p.relative_to(target)) for p in paths)
        except ConflictError as e:
            console.print(f"\n[red]{e}[/red]")
            console.print("\n[yellow]Rerun with --force to overwrite existing files.[/yellow]")
            raise typer.Exit(1)
        results.append({"skill": skill, "files": files_written})

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

    # Refresh agent context files; pass the adapter's display-name function so
    # commands adapters show v-<name> and skills adapters show q-<name>.
    context_skills = [s for s in install_set if not s.internal]
    for adapter in adapters:
        path = update_context_file(
            target,
            adapter.context_file,
            context_skills,
            mdc=adapter.context_file_mdc,
            name_fn=adapter.install_display_name,
        )
        console.print(f"[dim]Context file updated: {path}[/dim]")

    lock_data = {
        "agent": agent.value,
        "release": release or "latest",
        "skills": [
            {
                "name": r["skill"].name,
                "version": r["skill"].version,
                "internal": r["skill"].internal,
                "files": r["files"],
            }
            for r in results
        ],
    }
    lock_path = write_lock(target, lock_data)
    console.print(f"\n[dim]Lock file written: {lock_path}[/dim]")
    console.print("[bold green]Done.[/bold green]")
