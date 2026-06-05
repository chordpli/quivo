"""Abstract base adapter for skill installation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from quivo.registry import SkillMeta


class ConflictError(Exception):
    """Raised when a target file already exists and --force was not given."""

    def __init__(self, paths: list[Path]) -> None:
        self.paths = paths
        super().__init__(
            "Target files already exist. Rerun with --force to overwrite:\n"
            + "\n".join(f"  {p}" for p in paths)
        )


class BaseAdapter(ABC):
    """Writes a skill's files into the target project directory."""

    def __init__(
        self,
        target_dir: Path,
        force: bool = False,
        policy_content: Optional[str] = None,
    ) -> None:
        self.target_dir = target_dir
        self.force = force
        self.policy_content = policy_content

    def _check_conflicts(self, paths: list[Path]) -> None:
        """Raise ConflictError if any path exists and force is False."""
        if self.force:
            return
        conflicts = [p for p in paths if p.exists()]
        if conflicts:
            raise ConflictError(conflicts)

    def _append_policy(self, content: str, skill_name: str) -> str:
        """Append policy content to a skill file if policy_content is set."""
        if not self.policy_content:
            return content
        separator = (
            "\n\n---\n\n"
            "## Company Policy (from .quivo/policy.md)\n\n"
            f"{self.policy_content.rstrip()}\n"
        )
        return content.rstrip() + separator

    @abstractmethod
    def install(self, skill: SkillMeta) -> list[Path]:
        """Install the skill and return a list of written file paths."""
        ...

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Human-readable agent identifier."""
        ...
