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
- Adapters for Claude Code (`.claude/skills/`) and Codex CLI (`.codex/`).
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
