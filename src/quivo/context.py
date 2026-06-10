"""Agent context file maintenance — managed quivo block in CLAUDE.md / AGENTS.md."""

from __future__ import annotations

import re
from pathlib import Path

from quivo.adapters.base import install_name
from quivo.registry import SkillMeta

BEGIN_MARKER = "<!-- quivo:skills:begin -->"
END_MARKER = "<!-- quivo:skills:end -->"


def _render_block(skills: list[SkillMeta]) -> str:
    lines = [
        BEGIN_MARKER,
        "## Quivo Skills",
        "",
        "Managed by quivo — regenerated on `quivo init` / `quivo sync`. Do not edit this block.",
        "",
    ]
    for s in sorted(skills, key=lambda s: s.name):
        desc = f" — {s.description}" if s.description else ""
        lines.append(f"- `{install_name(s.name)}` (v{s.version}){desc}")
    lines += ["", END_MARKER]
    return "\n".join(lines)


def update_context_file(target_dir: Path, filename: str, skills: list[SkillMeta]) -> Path:
    """Create or refresh the managed quivo block in an agent context file.

    Existing content outside the marker block is left untouched.
    """
    path = target_dir / filename
    block = _render_block(skills)
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
        text = block + "\n"
    path.write_text(text, encoding="utf-8")
    return path
