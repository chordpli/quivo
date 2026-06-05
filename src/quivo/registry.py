"""Registry: loads canonical skill definitions from a cache dir or local override."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class SkillMeta:
    name: str
    version: str
    description: str
    agents: list[str]
    internal: bool
    requires: list[str]
    skill_dir: Path


def load_registry(skills_root: Optional[Path] = None) -> list[SkillMeta]:
    """Load all skills from the given root directory.

    If skills_root is None, callers should obtain it via
    quivo.release.ensure_skills_cache() before calling this function.
    The root should contain sub-directories each with a skill.yaml.
    """
    if skills_root is None:
        raise ValueError(
            "skills_root must be provided. "
            "Call quivo.release.ensure_skills_cache() to obtain the path."
        )

    # The tar bundle extracts as skills/ inside the cache dir.
    # Accept either: root = the dir containing skills/ subdirs directly,
    # or root = a dir that has a skills/ child.
    actual_root = skills_root
    candidate = skills_root / "skills"
    if candidate.is_dir():
        actual_root = candidate

    skills: list[SkillMeta] = []
    for skill_dir in sorted(actual_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        yaml_path = skill_dir / "skill.yaml"
        if not yaml_path.exists():
            continue
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        skills.append(
            SkillMeta(
                name=data["name"],
                version=data.get("version", "0.0.1"),
                description=data.get("description", ""),
                agents=data.get("agents", ["claude", "codex"]),
                internal=data.get("internal", False),
                requires=data.get("requires", []),
                skill_dir=skill_dir,
            )
        )

    return skills


def get_skill(name: str, skills_root: Optional[Path] = None) -> Optional[SkillMeta]:
    """Return a single skill by name, or None if not found."""
    for skill in load_registry(skills_root):
        if skill.name == name:
            return skill
    return None


def resolve_install_set(skills: list[SkillMeta], skills_root: Optional[Path] = None) -> list[SkillMeta]:
    """
    Given a list of non-internal skills to install, pull in any
    internal skills they require (transitively).
    """
    all_skills = {s.name: s for s in load_registry(skills_root)}
    to_install: dict[str, SkillMeta] = {}

    def add(name: str) -> None:
        if name in to_install:
            return
        skill = all_skills.get(name)
        if skill is None:
            return
        to_install[name] = skill
        for dep in skill.requires:
            add(dep)

    for s in skills:
        add(s.name)

    # Return in dependency order: deps first, then public skills
    ordered: list[SkillMeta] = []
    seen: set[str] = set()

    def emit(name: str) -> None:
        if name in seen:
            return
        skill = to_install.get(name)
        if skill is None:
            return
        for dep in skill.requires:
            emit(dep)
        seen.add(name)
        ordered.append(skill)

    for s in to_install.values():
        emit(s.name)

    return ordered
