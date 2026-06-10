"""Codex CLI adapter — writes .agents/skills/q-{name}/ (open agent skills standard).

Codex discovers skills by scanning .agents/skills/ from the CWD up to the
repository root. Frontmatter is preserved — Codex requires the name and
description fields for skill discovery and implicit invocation.
"""

from __future__ import annotations

from quivo.adapters.base import BaseAdapter


class CodexAdapter(BaseAdapter):
    """Installs skills into .agents/skills/q-{name}/ for Codex CLI discovery."""

    skills_root_parts = (".agents", "skills")
    path_ref = ".agents/skills"
    context_file = "AGENTS.md"

    @property
    def agent_name(self) -> str:
        return "codex"
