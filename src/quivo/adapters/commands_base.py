"""Abstract base adapter for commands-format skill installation.

Commands adapters install each skill as a single Markdown file:
    {commands_root}/v-<name>.md

This matches the slash-command model used by Gemini CLI, Qwen Code,
Windsurf workflows, and similar agents: no subdirectory, no setup
scripts, no strict frontmatter — just the skill body.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from quivo.adapters.base import ConflictError, SKILL_PREFIX, _FRONTMATTER_RE, _sanitize_name
from quivo.registry import SkillMeta


def cmd_install_name(skill_name: str) -> str:
    """File stem (without extension) for an installed command-format skill."""
    return f"{SKILL_PREFIX}{_sanitize_name(skill_name)}"


class CommandsBaseAdapter(ABC):
    """Installs each skill as a single Markdown file in a commands directory."""

    commands_root_parts: tuple[str, ...]
    context_file: str
    context_file_mdc: bool = False

    def __init__(
        self,
        target_dir: Path,
        force: bool = False,
        policy_content: Optional[str] = None,
    ) -> None:
        self.target_dir = target_dir
        self.force = force
        self.policy_content = policy_content

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Human-readable agent identifier (used for agents: field filtering)."""
        ...

    def install_display_name(self, skill_name: str) -> str:
        """Name as shown in context files and skill lists."""
        return cmd_install_name(skill_name)

    def commands_root(self) -> Path:
        return self.target_dir.joinpath(*self.commands_root_parts)

    def skill_file(self, skill_name: str) -> Path:
        return self.commands_root() / f"{cmd_install_name(skill_name)}.md"

    def remove_installed(self, skill_name: str) -> bool:
        p = self.skill_file(skill_name)
        if p.exists():
            p.unlink()
            return True
        return False

    def _strip_frontmatter(self, content: str) -> str:
        m = _FRONTMATTER_RE.match(content)
        return content[m.end():] if m else content

    def _append_policy(self, content: str) -> str:
        if not self.policy_content:
            return content
        separator = (
            "\n\n---\n\n"
            "## Company Policy (from .quivo/policy.md)\n\n"
            f"{self.policy_content.rstrip()}\n"
        )
        return content.rstrip() + separator

    def _build_content(self, skill: SkillMeta, raw: str) -> str:
        body = self._strip_frontmatter(raw)
        return self._append_policy(body)

    def install(self, skill: SkillMeta) -> list[Path]:
        dest = self.skill_file(skill.name)
        src = skill.skill_dir / "SKILL.md"
        if not src.exists():
            return []

        if not self.force and dest.exists():
            raise ConflictError([dest])

        dest.parent.mkdir(parents=True, exist_ok=True)
        content = self._build_content(skill, src.read_text(encoding="utf-8"))
        dest.write_text(content, encoding="utf-8")
        return [dest]
