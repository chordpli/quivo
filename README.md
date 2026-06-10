<h1 align="center">quivo</h1>

<p align="center">
  <img src="./docs/assets/quivo-icon.png" alt="quivo icon" width="160">
</p>

<p align="center">
  <b>Forkable, multi-LLM skill distribution for AI coding agents.</b><br>
  Fork it, fill it with your company's skills, and sync them into Claude Code, Codex, and more — all from one versioned repo.
</p>

<p align="center">
  English · <a href="./README.ko.md">한국어</a> · <a href="./docs/GUIDE.md">Guide</a>
</p>

---

## What is quivo?

A **quiver** holds your arrows. **quivo** holds your *skills* — the markdown-plus-frontmatter
capability packages that drive modern coding agents — and delivers the same set to every
engineer's tools.

It is built to be **forked**. You take this repo, strip the examples, drop in your own
skills, and your company now has a single source of truth:

- **One repo** — skills live in one place, version-controlled, history-tracked.
- **One version for everyone** — engineers `quivo sync` and all see the same skill set.
- **Many agents** — the same `SKILL.md` installs into Claude Code, Codex CLI, and (via
  adapters) other LLM harnesses. Author once, run everywhere.
- **Company-customizable** — inject your own policy and environment config at install time
  without rewriting each skill.

> quivo는 AI 코딩 에이전트용 "스킬"을 한 레포에서 관리·배포하는 **포크형 템플릿**입니다.
> 이 레포를 포크해 회사 스킬로 채우면, 모든 엔지니어가 같은 버전의 스킬을 Claude Code·Codex 등에
> 설치해 쓸 수 있습니다.

---

## Quickstart

Requirements: Python 3.10+, [`uv`](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

For step-by-step walkthroughs with CLI examples and local testing, see **[Guide](./docs/GUIDE.md)** / **[한국어 길라잡이](./docs/GUIDE.ko.md)**.

**Install it (recommended)** — puts a real `quivo` on your PATH, then use `quivo` anywhere:

```bash
uv tool install git+https://github.com/chordpli/quivo.git    # or: pipx install git+https://github.com/chordpli/quivo.git
quivo init
```

Upgrade the CLI later with `quivo update` (or `uv tool install --force git+...`).

**Or just try it (zero install)** — run straight from the repo:

```bash
uvx --from git+https://github.com/chordpli/quivo.git quivo init
```

**Or alias the uvx form** — no install, re-resolves each run:

```bash
echo 'alias quivo="uvx --from git+https://github.com/chordpli/quivo.git quivo"' >> ~/.zshrc && source ~/.zshrc
quivo init
```

`quivo init` installs the bundled example skills into the current project:
- `.claude/skills/q-<name>/` for Claude Code (invoked as `/q-<name>`)
- `.agents/skills/q-<name>/` for Codex CLI (open agent skills standard, invoked as `$q-<name>`)

It also maintains a managed skill-list block in `CLAUDE.md` / `AGENTS.md`,
and cleans up install layouts left behind by older quivo versions.

---

## Fork it for your company

1. **Fork or clone** `chordpli/quivo` → `my-company/quivo`. For a **private** copy, clone and
   push to a new private repo — a GitHub fork of a public repo is always public. Throughout these
   steps, `my-company` is a placeholder — replace it with your GitHub org or username.
2. **Enable GitHub Actions** in the fork (forks have Actions off by default).
3. **Point the CLI at your fork** — edit one line in [`quivo.yml`](./quivo.yml):
   ```yaml
   repo: my-company/quivo
   ```
4. **Add your skills** under `skills/` (use the bundled [`author-skill`](./skills/author-skill)
   as a guide), bump `skills/VERSION`, and push to `main`.
5. **Release** — the [`Release Skills Bundle`](./.github/workflows/release-skills.yml) workflow
   builds `skills-bundle.tar.gz` and publishes a `skills-v*` GitHub Release in *your* repo.
6. **Engineers install:**
   ```bash
   uvx --from git+https://github.com/my-company/quivo.git quivo init   # or: quivo sync
   ```

The full step-by-step is in **[docs/quivo/fork-guide.md](./docs/quivo/fork-guide.md)**.

---

## Distribution modes

How a fork's skills reach each engineer's machine. Pick what fits your team.

| Mode | How | Private repo | Best for |
|------|-----|--------------|----------|
| **A. Releases** (default) | Fork builds `skills-v*` bundles; CLI downloads + caches | Engineer provides a read token once | Many engineers, pinned immutable versions, sha256 integrity, offline cache |
| **B. Local / clone** | Clone the repo; install straight from disk | Uses your existing git auth (no token) | Maintainers, small teams |

```bash
# Mode B — install from a local checkout, no releases needed
export QUIVO_LOCAL_SKILLS=/path/to/quivo/skills
quivo init --agent both
```

For private forks, releases work out of the box — set `GH_TOKEN` / `GITHUB_TOKEN`, or let the
CLI prompt once (it saves the token to `~/.quivo/token`, mode `0600`).

---

## Commands

| Command | What it does |
|---------|--------------|
| `quivo init` | Install skills into the current project (`--agent claude\|codex\|both`, `--dir`, `--force`, `--release TAG`, `--no-policy`) |
| `quivo sync` | Refresh installed skill **content** to the latest release |
| `quivo update` | Upgrade the quivo **CLI itself** to the latest `cli-v*` release |
| `quivo list` | List installed skills |
| `quivo doctor` | Check tooling, version, cache, and policy status |

`quivo update` upgrades the CLI; `quivo sync` refreshes the skills. Two tracks, two tags:
`cli-v*` for the CLI, `skills-v*` for the bundle.

---

## Company customization

Two install-time injection seams let one skill set behave differently per company — **no need
to fork the skill body**:

- **`.quivo/policy.md`** — appended to every installed skill (Prod procedures, permission
  rules, code/PR conventions). See the template in this repo.
- **`.quivo/config.yml`** — per-engineer environment values (profiles, regions, IDs) that
  skills resolve at runtime. Copy from [`.quivo/config.example.yml`](./.quivo/config.example.yml).

Skip injection with `quivo init --no-policy`.

---

## Bundled example skills

Kept intentionally minimal — this is a template, not a skill catalog.

| Skill | Purpose | Demonstrates |
|-------|---------|--------------|
| `author-skill` | Guide for writing new quivo skills to the standard | The authoring standard (`docs/quivo/`) |
| `aws-access` | Authenticate to AWS, verify identity, and serve as the entry point for AWS CLI work | `setup.sh`/`setup.ps1` scripts, env-config (config › env › prompt) resolution, company-extension seam |
| `ripple` | Detect side effects of a change that tests miss (scan → clarify → resolve → check) | A self-contained, harness-agnostic SDLC skill with structured outputs and a delta-anchored Iron Law |

Authoring standard lives in [`docs/quivo/`](./docs/quivo): the constitution, skill template,
permission model, and adapter reference.

---

## Inspiration

quivo's design draws on the open-source frameworks that pioneered authoring and distributing
agent skills. Their strengths, weaknesses, and what quivo borrowed (or deliberately rejected)
are written up in **[docs/quivo/reference/inspiration.md](./docs/quivo/reference/inspiration.md)**
(deep comparison in [skill-framework-analysis.md](./docs/quivo/reference/skill-framework-analysis.md)).

- [**spec-kit**](https://github.com/github/spec-kit) — GitHub's Spec-Driven Development toolkit; spec → plan → tasks → implement, 30+ agent targets
- [**superpowers**](https://github.com/obra/superpowers) — Jesse Vincent's agentic SDLC discipline skills (Iron Law, TDD, verification)
- [**oh-my-claudecode**](https://github.com/Yeachan-Heo/oh-my-claudecode) — multi-agent orchestration with evidence-based verification gates
- [**gstack**](https://github.com/garrytan/gstack) — Garry Tan's "virtual engineering team" personas (anti-sycophancy, hard gates, template generation)
- [**Anthropic Agent Skills**](https://github.com/anthropics/skills) — the first-party `SKILL.md` standard ([engineering blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) · [docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview))
- [**Andrej Karpathy**](https://karpathy.ai/) — the minimalist "every token earns its place" skill-authoring philosophy
- [**spec-kit-ripple**](https://github.com/chordpli/spec-kit-ripple) — origin of the bundled `ripple` skill's scan → clarify → resolve → check flow

---

## Requirements

- Python 3.10+
- `uv` (recommended) or pip
- Network access (GitHub Releases) or `QUIVO_LOCAL_SKILLS` for offline/local use

## License

[MIT](./LICENSE)

---

<p align="center">
  Built by <a href="https://github.com/chordpli">chordpli</a> · <a href="./LICENSE">MIT</a> · contributions welcome
</p>
