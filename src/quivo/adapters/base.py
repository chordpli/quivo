"""Abstract base adapter for skill installation."""

from __future__ import annotations

import re
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import yaml

from quivo.registry import SkillMeta

# Installed skills are namespaced (spec-kit style: speckit-<name>) so they
# never collide with a project's own skills. Invocation names follow suit:
# /q-ripple in Claude Code, $q-ripple in Codex.
SKILL_PREFIX = "q-"

# Frontmatter keys the agent skill validators accept (agentskills.io standard;
# Codex rejects skills with any other top-level key). Everything else is moved
# under metadata: on install.
ALLOWED_FRONTMATTER_KEYS = ("name", "description", "license", "allowed-tools")

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _sanitize_name(skill_name: str) -> str:
    """Normalize a skill name to the validators' ^[a-z0-9-]+$ requirement."""
    s = re.sub(r"[^a-z0-9-]+", "-", skill_name.lower())
    return re.sub(r"-{2,}", "-", s).strip("-")


def install_name(skill_name: str) -> str:
    """Directory and frontmatter name for an installed skill."""
    return f"{SKILL_PREFIX}{_sanitize_name(skill_name)}"


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

    # Where installed skills live, relative to target_dir.
    skills_root_parts: tuple[str, ...]
    # Prefix used when rewriting .claude/skills/<name>/ references in skill bodies.
    path_ref: str
    # Agent context file maintained at the target root.
    context_file: str
    # Set to True for adapters whose context file uses MDC frontmatter (e.g. Cursor).
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
        return install_name(skill_name)

    def skills_root(self) -> Path:
        return self.target_dir.joinpath(*self.skills_root_parts)

    def skill_dir(self, skill_name: str) -> Path:
        return self.skills_root() / install_name(skill_name)

    def skill_md_path(self, skill_name: str) -> Path:
        return self.skill_dir(skill_name) / "SKILL.md"

    def remove_installed(self, skill_name: str) -> bool:
        """Remove this adapter's installed copy of a skill. Returns True if removed."""
        dest = self.skill_dir(skill_name)
        if dest.is_dir():
            shutil.rmtree(dest)
            return True
        return False

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

    def _rewrite_paths(self, content: str) -> str:
        """Rewrite .claude/skills/<name>/ references to this adapter's install layout."""
        return re.sub(
            rf"\.claude/skills/(?!{SKILL_PREFIX})([^/\s]+)/",
            rf"{self.path_ref}/{SKILL_PREFIX}\1/",
            content,
        )

    def _rewrite_frontmatter(self, skill: SkillMeta, content: str) -> str:
        """Reduce frontmatter to validator-accepted keys.

        Disallowed keys (version, scope, risk, outputs, ...) are preserved
        under metadata: — the one free-form key the standard allows — so
        contract readers can still find them without breaking discovery.
        """
        m = _FRONTMATTER_RE.match(content)
        if not m:
            return content
        data = yaml.safe_load(m.group(1)) or {}
        if not isinstance(data, dict):
            return content

        clean: dict = {"name": install_name(skill.name)}
        extras: dict = {}
        for key, value in data.items():
            if key == "name":
                continue
            if key in ALLOWED_FRONTMATTER_KEYS:
                clean[key] = value
            elif key != "metadata":
                extras[key] = value
        existing_meta = data.get("metadata")
        merged = {**extras, **existing_meta} if isinstance(existing_meta, dict) else extras
        if merged:
            clean["metadata"] = merged

        dumped = yaml.safe_dump(
            clean, allow_unicode=True, sort_keys=False, default_flow_style=False
        ).strip()
        return f"---\n{dumped}\n---\n" + content[m.end():]

    def _rewrite_skill_md(self, skill: SkillMeta, content: str) -> str:
        content = self._rewrite_frontmatter(skill, content)
        content = self._rewrite_paths(content)
        return self._append_policy(content, skill.name)

    def install(self, skill: SkillMeta) -> list[Path]:
        dest = self.skill_dir(skill.name)

        sources = [(skill.skill_dir / fn, dest / fn) for fn in ("SKILL.md", "setup.sh", "setup.ps1")]
        sources = [(src, tgt) for src, tgt in sources if src.exists()]

        self._check_conflicts([tgt for _, tgt in sources])

        dest.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []

        for src, target_path in sources:
            raw = src.read_text(encoding="utf-8")
            if src.name == "SKILL.md":
                content = self._rewrite_skill_md(skill, raw)
            else:
                content = self._rewrite_paths(raw)
            target_path.write_text(content, encoding="utf-8")
            shutil.copystat(src, target_path)
            written.append(target_path)

        return written
