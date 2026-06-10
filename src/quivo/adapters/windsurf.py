"""Windsurf adapter — writes .windsurf/workflows/v-{name}.md."""

from __future__ import annotations

from quivo.adapters.commands_base import CommandsBaseAdapter


class WindsurfAdapter(CommandsBaseAdapter):
    """Installs skills as Windsurf workflows in .windsurf/workflows/."""

    commands_root_parts = (".windsurf", "workflows")
    context_file = ".windsurf/rules/quivo-skills.md"

    @property
    def agent_name(self) -> str:
        return "windsurf"
