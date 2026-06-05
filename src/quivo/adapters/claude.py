"""Claude Code adapter — writes .claude/skills/{name}/."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from quivo.adapters.base import BaseAdapter, ConflictError
from quivo.registry import SkillMeta


class ClaudeAdapter(BaseAdapter):
    """Installs skills into .claude/skills/{name}/."""

    @property
    def agent_name(self) -> str:
        return "claude"

    def install(self, skill: SkillMeta) -> list[Path]:
        dest = self.target_dir / ".claude" / "skills" / skill.name

        # Determine which source files exist
        sources = [(skill.skill_dir / fn, dest / fn) for fn in ("SKILL.md", "setup.sh", "setup.ps1")]
        sources = [(src, tgt) for src, tgt in sources if src.exists()]

        # Conflict check before writing anything
        self._check_conflicts([tgt for _, tgt in sources])

        dest.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []

        for src, target_path in sources:
            if src.name == "SKILL.md":
                content = src.read_text(encoding="utf-8")
                content = self._append_policy(content, skill.name)
                target_path.write_text(content, encoding="utf-8")
            else:
                shutil.copy2(src, target_path)
            written.append(target_path)

        return written
