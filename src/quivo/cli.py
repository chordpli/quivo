"""quivo CLI entry point."""

from typing import Optional

import typer

import quivo
from quivo.commands.init import init
from quivo.commands.update import update
from quivo.commands.sync import sync
from quivo.commands.list_cmd import list_skills
from quivo.commands.doctor import doctor

REPO_URL = "https://github.com/chordpli/quivo"

app = typer.Typer(
    name="quivo",
    help="Forkable skill distribution CLI — installs AI skills for Claude Code, Codex, and more.",
    epilog=f"quivo · created by chordpli · {REPO_URL}",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"quivo {quivo.__version__} — {REPO_URL}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        help="Show quivo version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    pass


app.command("init")(init)
app.command("update")(update)
app.command("sync")(sync)
app.command("list")(list_skills)
app.command("doctor")(doctor)


if __name__ == "__main__":
    app()
