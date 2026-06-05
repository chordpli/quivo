#!/usr/bin/env python3
"""Static validator for quivo SKILL.md files.

Checks each skills/<name>/SKILL.md against docs/quivo/skill-template.md:
  - 8 required frontmatter fields with valid types/values
  - outputs[] schema
  - 5 required body sections
  - name matches parent directory

Exit code 0 on pass, 1 on any failure. Designed for CI.

Usage:
  python scripts/lint-skills.py                 # default: skills/
  python scripts/lint-skills.py path/to/skills
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REQUIRED_FIELDS = {
    "name",
    "description",
    "version",
    "scope",
    "agents",
    "risk",
    "policy_injection",
    "outputs",
}

ENUM_VALUES = {
    "scope": {"general", "company"},
    "risk": {"low", "medium", "high"},
    "policy_injection": {"required", "optional", "forbidden"},
}

ALLOWED_AGENTS = {"claude", "codex"}

REQUIRED_BODY_SECTIONS = [
    "## When to use",
    "## Inputs",
    "## Process",
    "## Iron Laws",
    "## Failure modes",
]

# Allows optional `__` prefix for private/internal skills (e.g. __my-helper).
# Body must still be kebab-case.
KEBAB_CASE = re.compile(r"^(__)?[a-z][a-z0-9]*(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[\w.]+)?$")
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)^---\s*\n", re.DOTALL | re.MULTILINE)


@dataclass
class SkillReport:
    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def split_frontmatter(text: str) -> tuple[dict | None, str, str | None]:
    """Return (parsed_frontmatter, body, error). frontmatter is None on error."""
    m = FRONTMATTER.match(text)
    if not m:
        return None, text, "frontmatter block (--- ... ---) not found at top"
    raw = m.group(1)
    body = text[m.end():]
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return None, body, f"YAML parse error: {e}"
    if not isinstance(data, dict):
        return None, body, "frontmatter is not a mapping"
    return data, body, None


def validate_outputs(value, report: SkillReport) -> None:
    if not isinstance(value, list):
        report.errors.append("outputs: must be a list (use [] for none)")
        return
    for i, item in enumerate(value):
        prefix = f"outputs[{i}]"
        if not isinstance(item, dict):
            report.errors.append(f"{prefix}: must be a mapping")
            continue
        if "path" not in item or not isinstance(item["path"], str) or not item["path"]:
            report.errors.append(f"{prefix}.path: required non-empty string")
        if "min_lines" in item:
            if not isinstance(item["min_lines"], int) or item["min_lines"] < 0:
                report.errors.append(f"{prefix}.min_lines: must be non-negative int")
        if "required_sections" in item:
            rs = item["required_sections"]
            if not isinstance(rs, list) or not all(isinstance(s, str) for s in rs):
                report.errors.append(f"{prefix}.required_sections: must be list[str]")
        extra = set(item.keys()) - {"path", "min_lines", "required_sections"}
        if extra:
            report.warnings.append(f"{prefix}: unknown keys {sorted(extra)}")


def validate_frontmatter(fm: dict, skill_dir_name: str, report: SkillReport) -> None:
    missing = REQUIRED_FIELDS - set(fm.keys())
    if missing:
        report.errors.append(f"missing required fields: {sorted(missing)}")

    # name
    name = fm.get("name")
    if isinstance(name, str):
        if not KEBAB_CASE.match(name):
            report.errors.append(f"name: '{name}' is not kebab-case")
        if name != skill_dir_name:
            report.errors.append(f"name: '{name}' does not match directory '{skill_dir_name}'")
    elif "name" in fm:
        report.errors.append("name: must be a string")

    # description
    desc = fm.get("description")
    if isinstance(desc, str):
        if len(desc.strip()) < 10:
            report.errors.append("description: too short (need at least 10 chars)")
        if len(desc) > 500:
            report.warnings.append(f"description: very long ({len(desc)} chars), consider shortening")
    elif "description" in fm:
        report.errors.append("description: must be a string")

    # version
    version = fm.get("version")
    if isinstance(version, str):
        if not SEMVER.match(version):
            report.errors.append(f"version: '{version}' is not semver (X.Y.Z)")
    elif "version" in fm:
        report.errors.append("version: must be a string")

    # enums
    for key, allowed in ENUM_VALUES.items():
        if key in fm:
            val = fm[key]
            if val not in allowed:
                report.errors.append(f"{key}: '{val}' not in {sorted(allowed)}")

    # agents
    if "agents" in fm:
        agents = fm["agents"]
        if not isinstance(agents, list) or not agents:
            report.errors.append("agents: must be a non-empty list")
        else:
            unknown = [a for a in agents if a not in ALLOWED_AGENTS]
            if unknown:
                report.errors.append(f"agents: unknown values {unknown} (allowed: {sorted(ALLOWED_AGENTS)})")

    # outputs
    if "outputs" in fm:
        validate_outputs(fm["outputs"], report)

    # unknown fields (warning)
    known = REQUIRED_FIELDS | {"owners", "triggers", "requires", "related_skills"}
    extra = set(fm.keys()) - known
    if extra:
        report.warnings.append(f"unknown frontmatter fields: {sorted(extra)}")


def validate_body(body: str, report: SkillReport) -> None:
    for section in REQUIRED_BODY_SECTIONS:
        # Match header at line start, allow trailing content on same line
        pattern = re.compile(rf"^{re.escape(section)}\b", re.MULTILINE)
        if not pattern.search(body):
            report.errors.append(f"body: missing required section '{section}'")


def lint_skill(skill_md: Path) -> SkillReport:
    report = SkillReport(path=skill_md)
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as e:
        report.errors.append(f"cannot read: {e}")
        return report

    fm, body, err = split_frontmatter(text)
    if err:
        report.errors.append(err)
    if fm is not None:
        validate_frontmatter(fm, skill_md.parent.name, report)
    validate_body(body, report)
    return report


def discover_skills(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.glob("*/SKILL.md"))


def main(argv: list[str]) -> int:
    skills_root = Path(argv[1]) if len(argv) > 1 else Path("skills")
    skill_files = discover_skills(skills_root)

    if not skill_files:
        print(f"No SKILL.md files found under {skills_root}/", file=sys.stderr)
        # No skills = nothing to fail on. CI may want to override.
        return 0

    failed = 0
    warned = 0
    for f in skill_files:
        r = lint_skill(f)
        rel = f.relative_to(Path.cwd()) if f.is_absolute() else f
        if r.errors:
            failed += 1
            print(f"FAIL {rel}")
            for e in r.errors:
                print(f"  - {e}")
        else:
            print(f"OK   {rel}")
        for w in r.warnings:
            warned += 1
            print(f"  ! {w}")

    print()
    total = len(skill_files)
    print(f"Summary: {total - failed}/{total} passed, {failed} failed, {warned} warnings")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
