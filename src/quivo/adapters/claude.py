"""Claude Code adapter — writes .claude/skills/q-{name}/."""

from __future__ import annotations

from quivo.adapters.base import BaseAdapter


class ClaudeAdapter(BaseAdapter):
    """Installs skills into .claude/skills/q-{name}/."""

    skills_root_parts = (".claude", "skills")
    path_ref = ".claude/skills"
    context_file = "CLAUDE.md"

    @property
    def agent_name(self) -> str:
        return "claude"
