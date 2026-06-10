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
| `1` | `claude` | `.claude/skills/q-<name>/` |
| `2` | `codex` | `.agents/skills/q-<name>/` |
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
.claude/skills/q-<skill-name>/SKILL.md
.agents/skills/q-<skill-name>/SKILL.md
CLAUDE.md          # managed quivo skill-list block
AGENTS.md          # managed quivo skill-list block
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

## Add a New Skill

The most common maintenance task in a company quivo repository is adding a new
skill under `skills/`. A skill is managed as one directory. At minimum, it needs
`SKILL.md` and `skill.yaml`.

You can create a skill manually, but in practice it is fairly easy to miss a
file or validation step. The recommended workflow is to have an LLM use the
bundled `author-skill` to draft the skill, then have a human review the purpose,
trigger boundary, and validation results.

```text
skills/<skill-name>/
  SKILL.md
  skill.yaml
  setup.sh      # optional
  setup.ps1     # optional
```

For the fastest and safest path, use the bundled `author-skill`. After installing
quivo skills into Claude Code or Codex, ask the LLM for something like:

```text
I want to add a new quivo skill. Purpose: <what>. Trigger moment: <when>. Inputs: <what>. Outputs: <what>.
```

Use the manual steps below when reviewing what `author-skill` produced, or when
you need to write a skill without automation.

1. Choose a skill name.

Use kebab-case.

```bash
export SKILL_NAME="my-new-skill"
mkdir -p "skills/$SKILL_NAME"
```

2. Write `skill.yaml`.

```yaml
name: my-new-skill
version: 0.1.0
description: "One or two sentences explaining what this skill does and when to use it."
agents: [claude, codex]
internal: false
requires: []
```

The `description` matters a lot. Agents use it to decide which skill to trigger
automatically. If neighboring skills are similar, make the boundary explicit.

3. Write `SKILL.md`.

`SKILL.md` must start with frontmatter and must include the required body
sections. Follow [quivo/skill-template.md](./quivo/skill-template.md) for the
full standard.

```markdown
---
name: my-new-skill
description: One or two sentences explaining what this skill does and when to use it.
version: 0.1.0
scope: general
agents: [claude, codex]
risk: low
policy_injection: required
outputs: []
---

# My New Skill

> **The Iron Law**: The one rule this skill must never break.

You are operating as ...

## When to use

## Inputs

## Process

## Iron Laws

## Failure modes
```

Required frontmatter fields are `name`, `description`, `version`, `scope`,
`agents`, `risk`, `policy_injection`, and `outputs`.

Required body sections are `## When to use`, `## Inputs`, `## Process`,
`## Iron Laws`, and `## Failure modes`.

4. Add setup scripts if needed.

If the skill needs tool checks or environment setup before use, put `setup.sh`
or `setup.ps1` in the same directory. quivo copies these files during install.

5. Add a trigger prompt.

```bash
mkdir -p tests/skill-triggering/prompts
printf '%s\n' "A natural-language request a user would make when they need this skill." \
  > "tests/skill-triggering/prompts/$SKILL_NAME.txt"
```

Avoid naming the skill directly in the prompt. Use the kind of phrase a real user
would type. That makes it easier to see whether the `description` disambiguates
the skill correctly.

6. Update `manifest.json`.

For local validation and review, add the new skill version and sha256 to
`manifest.json`. The GitHub Release workflow also regenerates the manifest, but
keeping the local file current makes PR checks and review easier.

```bash
python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path

name = os.environ.get("SKILL_NAME", "my-new-skill")
skill_dir = Path("skills") / name

combined = b""
for fname in sorted(["skill.yaml", "SKILL.md", "setup.sh", "setup.ps1"]):
    path = skill_dir / fname
    if path.exists():
        combined += path.read_bytes()

sha = hashlib.sha256(combined).hexdigest()

manifest_path = Path("manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

version = None
for line in (skill_dir / "skill.yaml").read_text(encoding="utf-8").splitlines():
    if line.startswith("version:"):
        version = line.split(":", 1)[1].strip().strip('"')
        break
if version is None:
    raise SystemExit("version not found in skill.yaml")

entry = {"name": name, "version": version, "sha256": sha}
manifest["skills"] = [s for s in manifest["skills"] if s["name"] != name]
manifest["skills"].append(entry)
manifest["skills"].sort(key=lambda s: s["name"])
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY
```

7. Bump the skills bundle version.

For a release-worthy change, bump `skills/VERSION` using semver.

```bash
echo "0.2.0" > skills/VERSION
```

8. Validate the skill.

```bash
python3 scripts/lint-skills.py
python3 scripts/check-trigger-disambiguation.py
scripts/test-skill.sh "$SKILL_NAME"
```

It is also worth testing a local install:

```bash
TMPPROJECT="$(mktemp -d "${TMPDIR:-/tmp}/quivo-skill-test.XXXXXX")"
QUIVO_LOCAL_SKILLS="$PWD" quivo init --agent both --dir "$TMPPROJECT" --no-policy
quivo list --dir "$TMPPROJECT"
```

The install path is healthy when the new skill appears under Claude Code's
`.claude/skills/q-<skill-name>/` and Codex's `.agents/skills/q-<skill-name>/`.

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
test -f "$SMOKEDIR/.claude/skills/q-author-skill/SKILL.md"
test -f "$SMOKEDIR/.agents/skills/q-author-skill/SKILL.md"
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
| Existing files conflict | Inspect the target `.claude/skills` or `.agents/skills` files, then use `--force` only if overwriting is intended. |
| `quivo sync` fails | Make sure the target project has `.quivo-lock.json`. If not, run `quivo init` first. |

## Next documents

- [README.md](../README.md): Conceptual overview of quivo
- [quivo/fork-guide.md](./quivo/fork-guide.md): Detailed company fork setup
- [quivo/skill-template.md](./quivo/skill-template.md): Template for writing new skills
- [quivo/permissions.md](./quivo/permissions.md): Skill permission model
