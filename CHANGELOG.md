# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: skill bundle uses `skills-vX.Y.Z` tags; quivo CLI uses `cli-vX.Y.Z` tags.

---

## [Unreleased]

### Added
- Initial open-source release of **quivo** — a forkable, multi-LLM skill
  distribution CLI for AI coding agents.
- CLI commands: `init`, `sync`, `update` (self-upgrade), `list`, `doctor`.
- Adapters for Claude Code (`.claude/skills/`) and Codex CLI
  (`.agents/skills/`, per the open agent skills standard).
- `q-` namespace prefix for installed skills (directory and frontmatter
  `name:`) so quivo skills never collide with a project's own skills.
  Names are normalized to the validators' `^[a-z0-9-]+$` requirement.
- Frontmatter normalization on install: only validator-accepted keys
  (`name`, `description`, `license`, `allowed-tools`, `metadata`) stay
  top-level; all other keys (`version`, `scope`, `risk`, `outputs`, ...)
  move under `metadata:` so Codex discovery doesn't reject the skill.
- Managed skill-list block in agent context files (`CLAUDE.md` for Claude
  Code, `AGENTS.md` for Codex), regenerated on `init`/`sync`.
- Clean reinstall on `init`/`sync`: the previous install — every file
  recorded in `.quivo-lock.json`'s per-skill manifests — is removed before
  installing fresh, so layout/prefix changes never leave stale copies.
  Known pre-manifest layouts (`.codex/prompts/`, `.codex/scripts/`,
  unprefixed directories) are cleaned as a fallback, and skills dropped
  from the skill source are uninstalled on `sync`.
- `.quivo-lock.json` records installed file paths per skill (including
  internal skills), the manifest driving clean reinstalls.
- Repo resolution via `quivo.yml` (`repo:` key) → `QUIVO_REPO` env → built-in
  default, so a fork declares its skill source once.
- Install-time injection: `.quivo/policy.md` (company policy) and
  `.quivo/config.yml` (per-engineer environment values).
- Authoring standard under `docs/quivo/`: constitution, skill template,
  permission model, adapter reference, framework analysis, and an
  `inspiration.md` reference (pros/cons of spec-kit, superpowers,
  oh-my-claudecode, gstack, Anthropic Agent Skills, karpathy) with source links.
- Bundled example skills: `author-skill` (authoring guide), `aws-access`
  (AWS auth/identity entry point; setup scripts + env-config pattern), and
  `ripple` (post-change side-effect detection: scan → clarify → resolve → check).
- `docs/quivo/fork-guide.md` and `docs/quivo/open-source-plan.md`.
