"""Gemini CLI adapter — writes .gemini/commands/v-{name}.md."""

from __future__ import annotations

from quivo.adapters.commands_base import CommandsBaseAdapter


class GeminiAdapter(CommandsBaseAdapter):
    """Installs skills as Gemini CLI slash commands in .gemini/commands/."""

    commands_root_parts = (".gemini", "commands")
    context_file = "GEMINI.md"

    @property
    def agent_name(self) -> str:
        return "gemini"
