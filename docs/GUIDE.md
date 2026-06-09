# quivo Guide

<p align="center">
  <a href="./GUIDE.ko.md">한국어</a> · English
</p>

This guide is a practical walkthrough for installing quivo, installing skills,
syncing them, and testing the current checkout in a clean local virtual
environment.

The README explains what quivo is. This guide focuses on the commands someone
can run and the results they should expect.

## Terms

| Term | Meaning |
|------|---------|
| quivo CLI | The command line tool that provides commands such as `quivo init` and `quivo sync` |
| Skills repo | A quivo repository that contains a `skills/` directory |
| Target project | The project where you want Claude Code or Codex to use the installed skills |
| agent | The tool to install skills for: `claude`, `codex`, or `both` |
| release mode | The default mode. quivo downloads a skills bundle from GitHub Releases. |
| local mode | Development/offline mode. quivo installs skills from a local checkout on disk. |

## Requirements

- Python 3.10 or newer
- `uv` recommended
- Network access when installing from GitHub Releases
- `GH_TOKEN` or `GITHUB_TOKEN` when using a private repository

Check your Python version:

```bash
python3 --version
```

Install `uv` if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installing `uv`, open a new terminal or reload your shell config.

## Install quivo

The recommended installation method is `uv tool install`. It puts a real
`quivo` command on your PATH so you can run it from any directory.

```bash
uv tool install git+https://github.com/chordpli/quivo.git
quivo --version
```

If your team uses `pipx`, this works too:

```bash
pipx install git+https://github.com/chordpli/quivo.git
quivo --version
```

To try quivo once without installing it permanently, use `uvx`:

```bash
uvx --from git+https://github.com/chordpli/quivo.git quivo --version
```

## Install skills into a project

Go to the project where you want to use the skills:

```bash
cd /path/to/your/project
```

The simplest flow is to run `quivo init` without options:

```bash
quivo init
```

The CLI asks which agent to install skills for. The default is `3`, which means
`both`. Press Enter to install for both Claude Code and Codex.

![quivo init interactive CLI capture](./assets/quivo-init-interactive.svg)

The choices are:

| Choice | Input | Install location |
|--------|-------|------------------|
| `1` | `claude` | `.claude/skills/` |
| `2` | `codex` | `.codex/prompts/`, `.codex/scripts/` |
| `3` | `both` | Both Claude Code and Codex |

For scripts or docs where you want to avoid the interactive prompt, pass
`--agent` explicitly.

Install skills for both Claude Code and Codex:

```bash
quivo init --agent both
```

Install only for Claude Code:

```bash
quivo init --agent claude
```

Install only for Codex:

```bash
quivo init --agent codex
```

After installation, the target project should contain files like these:

```text
.claude/skills/<skill-name>/SKILL.md
.codex/prompts/<skill-name>.md
.codex/scripts/<skill-name>/SKILL.md
.quivo-lock.json
```

`.quivo-lock.json` records which skills and versions are installed in the
target project.

## List installed skills

From the target project, run:

```bash
quivo list
```

To inspect another directory, pass `--dir`:

```bash
quivo list --dir /path/to/your/project
```

## Sync installed skills

To refresh skill content to the latest available version, run:

```bash
quivo sync
```

To sync a specific project:

```bash
quivo sync --dir /path/to/your/project
```

If existing files cause a conflict, inspect them first. Use `--force` only when
you intentionally want quivo to overwrite installed skill files.

```bash
quivo sync --force
```

## Upgrade the CLI itself

To upgrade the quivo CLI, run:

```bash
quivo update
```

Keep the two update paths separate:

| Goal | Command |
|------|---------|
| Refresh installed skill content | `quivo sync` |
| Upgrade the quivo command line tool | `quivo update` |

## Use quivo for a company repo

For a company setup, fork or copy this repository into a private repository and
edit the `repo` value in `quivo.yml`.

```yaml
repo: my-company/quivo
```

Then add company skills under `skills/`, bump `skills/VERSION`, and publish a
`skills-v*` release with GitHub Actions.

Engineers can install from the company repository:

```bash
uvx --from git+https://github.com/my-company/quivo.git quivo init --agent both
```

For a private repository, set a token:

```bash
export GH_TOKEN=github_pat_...
```

You can also let the CLI prompt for a token. The token is saved to
`~/.quivo/token`.

## Install from a local checkout

Use `QUIVO_LOCAL_SKILLS` when you want to test before publishing a release, or
when you are working offline.

Example from the quivo repository root:

```bash
cd /path/to/quivo
export QUIVO_LOCAL_SKILLS="$PWD"
quivo init --agent both --dir /path/to/test-project --no-policy
```

This skips GitHub Releases and uses the local `skills/` directory and
`manifest.json` from your checkout.

## Verify the current checkout in a clean virtual environment

This section documents the local validation flow used for this repository. The
same flow was run on 2026-06-09 and finished with `27 passed`.

The goal is to verify three things:

- The current checkout can be installed into a clean Python environment.
- The unit tests pass.
- `quivo init`, `quivo list`, and `quivo sync` work against a temporary project.

Start in the quivo repository root:

```bash
cd /path/to/quivo
```

Create a temporary virtual environment and a temporary target project:

```bash
TMPBASE="${TMPDIR:-/tmp}"
VENVDIR="$(mktemp -d "$TMPBASE/quivo-venv.XXXXXX")"
SMOKEDIR="$(mktemp -d "$TMPBASE/quivo-smoke.XXXXXX")"
echo "$VENVDIR"
echo "$SMOKEDIR"
```

The variables mean:

| Variable | Meaning |
|----------|---------|
| `VENVDIR` | A clean temporary Python virtual environment for quivo |
| `SMOKEDIR` | A temporary project where `quivo init` installs skills |

Create the virtual environment:

```bash
python3 -m venv "$VENVDIR"
```

Upgrade pip inside the virtual environment:

```bash
"$VENVDIR/bin/python" -m pip install --upgrade pip
```

Install the current checkout in editable mode and install `pytest`:

```bash
"$VENVDIR/bin/python" -m pip install -e . pytest
```

This reads `pyproject.toml` from the current directory and installs quivo with
its dependencies.

Run the unit tests:

```bash
"$VENVDIR/bin/python" -m pytest -q
```

Expected successful result:

```text
27 passed
```

Check that the installed CLI runs:

```bash
"$VENVDIR/bin/quivo" --version
```

Expected output shape:

```text
quivo 0.1.0
```

Install skills into the temporary project:

```bash
QUIVO_LOCAL_SKILLS="$PWD" "$VENVDIR/bin/quivo" init --agent both --dir "$SMOKEDIR" --no-policy
```

The important part is `QUIVO_LOCAL_SKILLS="$PWD"`. It makes quivo use the local
checkout instead of downloading a GitHub Release. `--no-policy` skips company
policy injection so the smoke test checks the plain install path.

On success, the command prints an installed-skills table containing
`author-skill`, `aws-access`, and `ripple`.

List the installed skills:

```bash
"$VENVDIR/bin/quivo" list --dir "$SMOKEDIR"
```

Check sync:

```bash
QUIVO_LOCAL_SKILLS="$PWD" "$VENVDIR/bin/quivo" sync --dir "$SMOKEDIR" --no-policy
```

Because the skills were just installed, the expected result is:

```text
All skills are up to date.
```

Finally, confirm that representative installed files exist:

```bash
test -f "$SMOKEDIR/.claude/skills/author-skill/SKILL.md"
test -f "$SMOKEDIR/.codex/prompts/author-skill.md"
test -f "$SMOKEDIR/.codex/scripts/author-skill/SKILL.md"
echo "smoke files ok"
```

Expected output:

```text
smoke files ok
```

When you are done, remove the temporary directories:

```bash
rm -rf "$VENVDIR" "$SMOKEDIR"
```

## Actual verification record

This is the local verification result captured right before this guide was
written.

| Item | Result |
|------|--------|
| Python | 3.11.7 |
| Virtual environment | `/private/tmp/quivo-venv.kEAk03` |
| Temporary project | `/private/tmp/quivo-smoke.VARgUf` |
| Install command | `pip install -e . pytest` |
| Unit tests | `27 passed` |
| CLI version check | `quivo 0.1.0` |
| Smoke test | `init`, `list`, `sync`, and file existence checks all passed |

## Troubleshooting

| Symptom | What to check |
|---------|---------------|
| `quivo` command not found | Re-run `uv tool install ...` or open a new terminal. |
| `pytest` is missing | Run `"$VENVDIR/bin/python" -m pip install -e . pytest` inside the clean setup. |
| GitHub API error | For a private repo, set `GH_TOKEN` or `GITHUB_TOKEN`. |
| You want to test without downloading a release | Run in local mode with `QUIVO_LOCAL_SKILLS="$PWD"`. |
| Existing files conflict | Inspect the target `.claude` or `.codex` files, then use `--force` only if overwriting is intended. |
| `quivo sync` fails | Make sure the target project has `.quivo-lock.json`. If not, run `quivo init` first. |

## Next documents

- [README.md](../README.md): Conceptual overview of quivo
- [quivo/fork-guide.md](./quivo/fork-guide.md): Detailed company fork setup
- [quivo/skill-template.md](./quivo/skill-template.md): Template for writing new skills
- [quivo/permissions.md](./quivo/permissions.md): Skill permission model
