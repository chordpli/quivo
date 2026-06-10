"""Cursor IDE adapter — writes .cursor/skills/q-{name}/SKILL.md."""

from __future__ import annotations

from quivo.adapters.base import BaseAdapter


class CursorAdapter(BaseAdapter):
    """Installs skills into .cursor/skills/q-{name}/ with MDC context file."""

    skills_root_parts = (".cursor", "skills")
    path_ref = ".cursor/skills"
    context_file = ".cursor/rules/quivo-skills.mdc"
    context_file_mdc = True

    @property
    def agent_name(self) -> str:
        return "cursor"
