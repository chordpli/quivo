"""Uninstall of previously installed skill files.

quivo treats every install as a clean reinstall: whatever the previous
install wrote (recorded as per-skill ``files`` lists in .quivo-lock.json)
is removed first, then the current layout is written fresh. This keeps
targets convergent across layout changes (e.g. .codex/prompts → .agents/
skills, the q- prefix) without accumulating stale copies.

``cleanup_legacy`` is the fallback for locks written before the file
manifest existed: it removes the known historical layouts by name. Skill
names always come from .quivo-lock.json, so only quivo-managed installs
are ever touched.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable


def _prune_empty_dirs(target: Path, dirs: Iterable[Path]) -> None:
    """Best-effort removal of now-empty directories, walking up to target."""
    root = target.resolve()
    for d in dirs:
        cur = d
        while cur.resolve() != root and root in cur.resolve().parents:
            try:
                cur.rmdir()
            except OSError:
                break
            cur = cur.parent


def remove_recorded_files(target: Path, lock: dict) -> list[Path]:
    """Remove every file the lock's per-skill manifests record. Returns removed paths.

    Paths are resolved against the target and anything escaping it is ignored.
    """
    root = target.resolve()
    removed: list[Path] = []
    parents: set[Path] = set()
    for skill in lock.get("skills", []):
        for rel in skill.get("files", []):
            p = (target / rel).resolve()
            if root not in p.parents:
                continue
            if p.is_file():
                p.unlink()
                removed.append(p)
                parents.add(p.parent)
    _prune_empty_dirs(target, parents)
    return removed


def _legacy_paths(target: Path, skill_name: str) -> list[Path]:
    # Skills-format layouts (folder-based, q- prefix or bare name)
    skills_dirs = [
        target / ".claude" / "skills" / skill_name,
        target / ".agents" / "skills" / skill_name,
        target / ".cursor" / "skills" / skill_name,
    ]
    # Commands-format layouts (single file, v- prefix or bare name)
    commands_files = [
        target / ".gemini" / "commands" / f"{skill_name}.md",
        target / ".qwen" / "commands" / f"{skill_name}.md",
        target / ".windsurf" / "workflows" / f"{skill_name}.md",
    ]
    # Pre-q-prefix legacy paths
    old_codex = [
        target / ".codex" / "prompts" / f"{skill_name}.md",
        target / ".codex" / "scripts" / skill_name,
    ]
    return skills_dirs + commands_files + old_codex


def cleanup_legacy(target: Path, skill_names: Iterable[str]) -> list[Path]:
    """Remove pre-manifest install layouts for the given skills. Returns removed paths."""
    removed: list[Path] = []
    for name in skill_names:
        for p in _legacy_paths(target, name):
            if p.is_dir():
                shutil.rmtree(p)
                removed.append(p)
            elif p.exists():
                p.unlink()
                removed.append(p)

    _prune_empty_dirs(
        target,
        [
            target / ".codex" / "prompts",
            target / ".codex" / "scripts",
            target / ".gemini" / "commands",
            target / ".qwen" / "commands",
            target / ".windsurf" / "workflows",
            target / ".cursor" / "skills",
        ],
    )

    return removed
