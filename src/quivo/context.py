"""Agent context file maintenance — managed quivo block in CLAUDE.md / AGENTS.md / etc."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Optional

from quivo.adapters.base import install_name
from quivo.registry import SkillMeta

BEGIN_MARKER = "<!-- quivo:skills:begin -->"
END_MARKER = "<!-- quivo:skills:end -->"

# Prepended to newly created MDC context files (e.g. .cursor/rules/quivo-skills.mdc).
_MDC_PREAMBLE = "---\nalwaysApply: true\n---\n\n"


def _render_block(skills: list[SkillMeta], name_fn: Callable[[str], str] = install_name) -> str:
    lines = [
        BEGIN_MARKER,
        "## Quivo Skills",
        "",
        "Managed by quivo — regenerated on `quivo init` / `quivo sync`. Do not edit this block.",
        "",
    ]
    for s in sorted(skills, key=lambda s: s.name):
        desc = f" — {s.description}" if s.description else ""
        lines.append(f"- `{name_fn(s.name)}` (v{s.version}){desc}")
    lines += ["", END_MARKER]
    return "\n".join(lines)


def update_context_file(
    target_dir: Path,
    filename: str,
    skills: list[SkillMeta],
    *,
    mdc: bool = False,
    name_fn: Optional[Callable[[str], str]] = None,
) -> Path:
    """Create or refresh the managed quivo block in an agent context file.

    Existing content outside the marker block is left untouched.
    For MDC files (mdc=True) a frontmatter preamble is added to new files.
    """
    if name_fn is None:
        name_fn = install_name
    path = target_dir / filename
    block = _render_block(skills, name_fn)
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if BEGIN_MARKER in text and END_MARKER in text:
            pattern = re.compile(
                re.escape(BEGIN_MARKER) + r".*?" + re.escape(END_MARKER),
                re.DOTALL,
            )
            text = pattern.sub(block, text, count=1)
        else:
            text = text.rstrip("\n") + "\n\n" + block + "\n"
    else:
        preamble = _MDC_PREAMBLE if mdc else ""
        text = preamble + block + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
