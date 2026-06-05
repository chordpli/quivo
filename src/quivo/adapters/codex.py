"""Codex CLI adapter — writes .codex/prompts/{name}.md and .codex/scripts/{name}/."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Optional

from quivo.adapters.base import BaseAdapter, ConflictError
from quivo.registry import SkillMeta


def _convert_to_codex_prompt(skill_name: str, skill_md_content: str) -> str:
    """
    Convert a Claude-style SKILL.md to a plain Codex slash-command prompt.

    Rules:
    - Strip YAML frontmatter block (--- ... ---)
    - Prepend  # /<skill-name>
    - Replace .claude/skills/{name}/ path references with .codex/scripts/{name}/
    - Keep body content otherwise intact
    """
    content = skill_md_content

    # Strip frontmatter
    frontmatter_re = re.compile(r"^---\s*\n.*?^---\s*\n", re.DOTALL | re.MULTILINE)
    content = frontmatter_re.sub("", content).lstrip("\n")

    # Replace path references
    content = content.replace(
        f".claude/skills/{skill_name}/",
        f".codex/scripts/{skill_name}/",
    )
    # Generic fallback for any remaining .claude/skills/ references
    content = re.sub(
        r"\.claude/skills/([^/\s]+)/",
        r".codex/scripts/\1/",
        content,
    )

    header = f"# /{skill_name}\n\n"
    return header + content


def _convert_to_codex_contract(skill_name: str, skill_md_content: str) -> str:
    """Keep SKILL.md frontmatter for local contract readers, with Codex paths."""
    content = skill_md_content.replace(
        f".claude/skills/{skill_name}/",
        f".codex/scripts/{skill_name}/",
    )
    return re.sub(
        r"\.claude/skills/([^/\s]+)/",
        r".codex/scripts/\1/",
        content,
    )


class CodexAdapter(BaseAdapter):
    """Installs skills into .codex/prompts/ and .codex/scripts/{name}/."""

    @property
    def agent_name(self) -> str:
        return "codex"

    def install(self, skill: SkillMeta) -> list[Path]:
        prompts_dir = self.target_dir / ".codex" / "prompts"
        scripts_dir = self.target_dir / ".codex" / "scripts" / skill.name

        # Collect all target paths for conflict check
        potential_targets: list[Path] = []
        skill_md = skill.skill_dir / "SKILL.md"
        if skill_md.exists():
            potential_targets.append(prompts_dir / f"{skill.name}.md")
            potential_targets.append(scripts_dir / "SKILL.md")
        for filename in ("setup.sh", "setup.ps1"):
            if (skill.skill_dir / filename).exists():
                potential_targets.append(scripts_dir / filename)

        self._check_conflicts(potential_targets)

        written: list[Path] = []

        # Write prompt file
        if skill_md.exists():
            prompts_dir.mkdir(parents=True, exist_ok=True)
            raw_content = skill_md.read_text(encoding="utf-8")
            prompt_content = _convert_to_codex_prompt(skill.name, raw_content)
            prompt_content = self._append_policy(prompt_content, skill.name)
            prompt_path = prompts_dir / f"{skill.name}.md"
            prompt_path.write_text(prompt_content, encoding="utf-8")
            written.append(prompt_path)

            scripts_dir.mkdir(parents=True, exist_ok=True)
            contract_content = _convert_to_codex_contract(skill.name, raw_content)
            contract_content = self._append_policy(contract_content, skill.name)
            contract_path = scripts_dir / "SKILL.md"
            contract_path.write_text(contract_content, encoding="utf-8")
            written.append(contract_path)

        # Write setup scripts
        for filename in ("setup.sh", "setup.ps1"):
            src = skill.skill_dir / filename
            if src.exists():
                scripts_dir.mkdir(parents=True, exist_ok=True)
                target = scripts_dir / filename
                shutil.copy2(src, target)
                written.append(target)

        return written
