"""Qwen Code adapter — writes .qwen/commands/v-{name}.md."""

from __future__ import annotations

from quivo.adapters.commands_base import CommandsBaseAdapter


class QwenAdapter(CommandsBaseAdapter):
    """Installs skills as Qwen Code slash commands in .qwen/commands/."""

    commands_root_parts = (".qwen", "commands")
    context_file = "QWEN.md"

    @property
    def agent_name(self) -> str:
        return "qwen"
