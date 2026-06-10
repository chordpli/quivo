"""Removal of files left behind by older quivo install layouts.

Older quivo versions installed Codex skills to .codex/prompts/<name>.md +
.codex/scripts/<name>/ (now deprecated by Codex in favor of .agents/skills/),
and both agents used unprefixed directory names before the q- namespace was
introduced. Skill names come from .quivo-lock.json, so only quivo-managed
installs are ever removed.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable


def _legacy_paths(target: Path, skill_name: str) -> list[Path]:
    return [
        target / ".codex" / "prompts" / f"{skill_name}.md",
        target / ".codex" / "scripts" / skill_name,
        target / ".claude" / "skills" / skill_name,
        target / ".agents" / "skills" / skill_name,
    ]


def cleanup_legacy(target: Path, skill_names: Iterable[str]) -> list[Path]:
    """Remove legacy install locations for the given skills. Returns removed paths."""
    removed: list[Path] = []
    for name in skill_names:
        for p in _legacy_paths(target, name):
            if p.is_dir():
                shutil.rmtree(p)
                removed.append(p)
            elif p.exists():
                p.unlink()
                removed.append(p)

    # Prune legacy-only directories if now empty (.claude/skills and
    # .agents/skills stay — they hold current installs).
    for d in (target / ".codex" / "prompts", target / ".codex" / "scripts", target / ".codex"):
        try:
            d.rmdir()
        except OSError:
            pass

    return removed
