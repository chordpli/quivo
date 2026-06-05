# Skill-Framework Analysis

## Purpose

This document is a fresh, standalone comparative analysis of seven reference frameworks for authoring and orchestrating agent "skills" — the markdown-plus-frontmatter capability packages that drive modern coding agents (Claude Code, Codex CLI, and peers). The goal is to extract, with evidence, what a **Claude+Codex multi-agent SDLC skill-distribution system** should adopt: a system that distributes atomic, individually-invocable skills with parity across both Claude and Codex harnesses, wires them into a software-delivery lifecycle (intake → spec → plan → implement → review → ship), and proves quality mechanically rather than by assertion.

## The seven sources analyzed

1. **spec-kit** — GitHub's canonical Spec-Driven Development toolkit (the upstream repo).
2. **speckit-applied** — spec-kit's methodology repackaged as 14 discrete, individually-invocable Claude Code skills.
3. **superpowers** — Jesse Vincent / Prime Radiant's composable SDLC methodology delivered as auto-triggering discipline skills.
4. **oh-my-claudecode (OMC)** — a Claude Code plugin that turns the main session into a multi-agent orchestrator with hook-enforced persistence.
5. **karpathy** — a minimalist skill-authoring *philosophy* (design sensibility, not a repo), grounded against superpowers' `writing-skills` guidance and Anthropic's best-practices doc.
6. **native-anthropic** — Anthropic's first-party skill standard (`skill-creator` + `plugin-dev/skill-development`), including an empirical eval/description-optimization toolchain.
7. **gstack** — Garry Tan's open-source TypeScript skills framework casting an agent as a "virtual engineering team" of role-personas across a sprint lifecycle.

## Method

Each source was read directly from its on-disk (or canonical-repo) location, an analysis was written, and a **separate adversarial verifier independently re-opened every cited file** to confirm or refute each claim, returning a grounding verdict, a list of ungrounded claims, and a list of confirmed highlights. This document prefers `confirmedHighlights`, hedges or drops anything the verifier flagged, and treats labelled-conceptual claims as recommendations rather than facts.

## Grounding-confidence note per source

- **spec-kit** — *solid*. All 10 signature patterns, 9 strengths, 7 weaknesses, 11 extractables grounded; only two off-by-N line anchors (quoted text correct) and one runtime-vs-install-time over-generalization.
- **speckit-applied** — *solid*. Zero ungrounded claims; every quoted snippet verbatim; only trivial 0–2 line drift.
- **superpowers** — *solid*. All 13 signature patterns and 9 extractables grounded; four minor off-by-1-to-3 citation quibbles, no fabrication.
- **oh-my-claudecode** — *solid*. Every evidence-bearing citation verified; three minor framing imprecisions (a field-name conflation, a cost figure sourced from README not the cited doc, "versioned" overstatement) — no fabricated mechanisms.
- **karpathy** — *partial*. All 10 signature patterns and the core philosophy solidly grounded; defect is a systematic file-misattribution in the *weaknesses* section (three citations point to a sibling file; one cited line is impossible). The substance exists; the citations were wrong.
- **native-anthropic** — *solid*. All 10 signature patterns and load-bearing weaknesses verified verbatim; only cosmetic off-by-one and a source-internal word-budget inconsistency the analysis itself flagged.
- **gstack** — *partial*. Architecture, validators, gates, learnings corpus, and BAD/GOOD pairs all verified true; but one **load-bearing fabrication**: gstack skills do **not** open with a "You are Claude Code…" persona-first-line (that string appears nowhere in the cited skill), and the "Tone Lock" label, a truncated quote, and a reconstructed dashboard table were presented as verbatim. Claims downstream of the fabricated persona-first-line are treated as unsupported here.

---

## Source profiles

### spec-kit (canonical repo)

**What it is.** GitHub's toolkit for Spec-Driven Development: an ordered pipeline of slash commands (`constitution → specify → clarify → plan → tasks → analyze → implement`, plus optional `checklist` and `taskstoissues`) that turns a natural-language feature description into an executable spec, a plan, a task list, and an implementation, where the spec — not the code — is the source of truth. It is markdown command files plus shell scripts installing into 30+ AI agents, not a runtime engine.

**Core architecture.** Each command is a markdown prompt with YAML frontmatter and a numbered flow. State is on-disk per feature in a numbered artifact set (`spec`, `plan`, `tasks`, `research`, `data-model`, `quickstart`, `contracts`, `checklist`). A deterministic bash/PowerShell layer beneath the agent does path resolution, numbering, and prerequisite validation, emitting JSON; the LLM only parses JSON and fills templates. Gates are explicit and partly script-enforced. A four-level override → preset → extension → core stack plus before/after lifecycle hooks wrap every command, and a `workflow.yml` chains them with typed human-review gates.

**Signature patterns.**
- Deterministic scripts + JSON handoff separating mechanics from reasoning, so bookkeeping never depends on model reliability — `check-prerequisites.sh:118-135` hard-errors with "Run /speckit.plan first"; both `scripts/bash/` and `scripts/powershell/` variants exist.
- `[NEEDS CLARIFICATION]` markers with a hard cap and impact ordering — `specify.md:123` "LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total"; priority `scope > security/privacy > user experience > technical details` (`specify.md:124`).
- Constitution as a re-checked gate, auto-CRITICAL in analysis — `plan-template.md:41` GATE before Phase 0 / re-check after Phase 1; `analyze.md:58` "Constitution conflicts are automatically CRITICAL".
- Read-only cross-artifact analyzer with six detection passes (Duplication/Ambiguity/Underspecification/Constitution/Coverage/Inconsistency) and CRITICAL/HIGH/MEDIUM/LOW severity — `analyze.md:56` "STRICTLY READ-ONLY: Do not modify any files".
- Strict machine-parseable task format with `[P]` parallel + `[Story]` traceability + file paths — `tasks.md:150` `- [ ] [TaskID] [P?] [Story?] Description with file path`.
- Checklists as "unit tests for requirements writing", not behavior — `checklist.md:10`; `≥80%` of items must carry a traceability reference (`checklist.md:211`).
- User-story-sliced, independently-testable phases with MVP-first checkpoints — `tasks-template.md:77` "Phase 3: User Story 1 … (Priority: P1) 🎯 MVP".
- Layered override/preset/extension/core stack — `README.md:200-211` priority table; templates resolved at runtime, first match wins.

**Strengths.** Deterministic bookkeeping layer isolates the LLM from path/numbering/gating failures; bounded ambiguity protocol (informed-guesses-by-default + capped markers); end-to-end traceability (requirements → user stories → tasks → coverage table → checklists); enforced constitution gate; read-only analyze is safe and re-runnable; extensible without forking; explicit human-review gates with `on_reject: abort`.

**Weaknesses.** Massive prompt duplication — the ~55-60-line extension-hook block is copy-pasted into all 9 command files, risking drift (verifier-confirmed). Single-agent-centric: no native multi-agent parallelism, role specialization, or worktree model; only intra-phase `[P]` hints. Gates beyond the bash prerequisite scripts are honor-system. No automated QA/review loop in core — testing is OPTIONAL. **The constitution placeholder silently neutralizes the gate** — verifier confirmed `.specify/memory/constitution.md` is 100% `[PLACEHOLDER]` tokens, so the Constitution Check passes vacuously when unfilled. Brittle task-line string matching; plain-file state has no locking.

### speckit-applied (the 14-skill port)

**What it is.** spec-kit's methodology repackaged as 14 discrete, individually-invocable Claude Code skills (specify, clarify, plan, tasks, analyze, implement, checklist, constitution, taskstoissues, and a 5-skill git family). Each is a self-contained `SKILL.md` declaring its upstream `metadata.source`, so the SDLC becomes a set of atomic skills rather than one monolithic pipeline.

**Core architecture.** Each skill is markdown + YAML frontmatter (name, description, argument-hint, compatibility, `metadata`, `user-invocable`, `disable-model-invocation`). The runtime contract is a `.specify/` directory: skills shell out to `check-prerequisites.sh --json` / `setup-plan.sh --json` to resolve absolute paths, copy from `.specify/templates/*`, and persist cross-command state in `.specify/feature.json`. The lifecycle is a linear artifact pipeline where each phase's output is the next phase's required input, enforced by prerequisite scripts that abort when inputs are missing. Crucially, **phases are decoupled from git**: branch creation is delegated to an optional `git-feature` hook, while the spec directory path is persisted to `feature.json` so downstream commands locate the feature without relying on branch names.

**Signature patterns.**
- Methodology decomposed into independently-invocable phase skills with explicit ordering contracts — `speckit-analyze/SKILL.md:59` "This command MUST run only after `/speckit.tasks` has successfully produced a complete `tasks.md`."
- A universal before_/after_ lifecycle-hook protocol embedded in every skill body, with optional (offer to user) vs mandatory (`EXECUTE_COMMAND:` + block until result) semantics, translating dotted hook names to skill slugs — `speckit.git.commit` → `/speckit-git-commit` (`speckit-specify/SKILL.md:32`).
- Gates encoded as prose STOP-points — `speckit-implement/SKILL.md:83` `STOP and ask: "Some checklists are incomplete. Do you want to proceed with implementation anyway? (yes/no)"`.
- Constitution as supreme governance with semver amendments + a Sync Impact Report propagating to dependent templates — `speckit-constitution/SKILL.md:73-76`, `:92-97`.
- Bounded, prioritized clarification with recommendation-first Q&A — `speckit-clarify/SKILL.md:129` "Maximum of 5 total questions"; top-5 by `(Impact * Uncertainty)`; each accepted answer written back atomically under a dated Clarifications session.
- Identity decoupling — `speckit-specify/SKILL.md:109` "The spec directory name and the git branch name are independent".
- Git family with hard safety guardrails — `speckit-taskstoissues/SKILL.md:73` "UNDER NO CIRCUMSTANCES EVER CREATE ISSUES IN REPOSITORIES THAT DO NOT MATCH THE REMOTE URL".

**Strengths.** One skill = one SDLC phase, each self-describing and individually discoverable without an orchestrator; durable artifact hand-offs make the pipeline resumable and inspectable; gates enforced via real STOP/wait-for-user prompts; uniform extension seam; strong anti-hallucination bounding (capped questions/findings, "NEVER hallucinate missing sections"); machine-parseable task grammar with worked ✅/❌ examples; pervasive graceful degradation in the git family; CAUTION-gated external writes.

**Weaknesses.** **~500+ duplicated lines** — the ~30-line hook protocol is copy-pasted into Pre- and Post-Execution of all 9 core skills (verifier confirmed exactly 2 `EXECUTE_COMMAND` blocks per skill). Gates are prose-enforced, not mechanically guaranteed. Tight coupling to a `.specify/` runtime that is **not materialized in the checkout** — the skills are inert templates until bootstrapped, and no skill bootstraps it. `taskstoissues` is underspecified vs its "dependency-ordered" promise (body only says "use the GitHub MCP server to create a new issue"). Hook name-translation is a brittle dots→hyphens convention with no existence check. No real state machine — phase completion is inferred from file presence. Heavy human-in-the-loop Q&A makes fully-autonomous multi-agent runs awkward.

### superpowers

**What it is.** A complete, composable SDLC methodology delivered as auto-triggering "skills" (`SKILL.md` + frontmatter) plus an entry instruction that forces the agent to consult them. It makes a coding agent step back and follow discipline: brainstorm a spec, isolate a worktree, write a bite-sized plan, execute via fresh subagents under two-stage review, enforce real RED-GREEN-REFACTOR TDD, debug systematically, and never claim completion without fresh verification evidence. Its standout is the meta-skill `writing-skills`, which treats skill authoring itself as TDD.

**Core architecture.** A flat namespace of single-purpose skill directories. Frontmatter is just `name` + `description` (≤1024 chars), where the description encodes **only** triggering conditions and deliberately omits any workflow summary. Skills cross-reference by name with `REQUIRED` markers and never `@`-link (which would force-load and burn context). The lifecycle is a chain of hard-gated handoffs: `using-superpowers` (invoke a skill before ANY response) → `brainstorming` (HARD-GATE: no code until design approved) → `using-git-worktrees` → `writing-plans` → `subagent-driven-development` → `test-driven-development` → `requesting-code-review` (spec-compliance then code-quality) → `finishing-a-development-branch`. A controller dispatches a fresh subagent per task with hand-curated context (never session history) and receives one of four statuses (DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT).

**Signature patterns.**
- The Iron Law — a single code-fenced absolute rule per discipline skill — `test-driven-development/SKILL.md:31-43` "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST … Delete means delete"; mirrored at `verification-before-completion:16-20` and `systematic-debugging:18-20`.
- Spirit-vs-letter pre-emption — `test-driven-development/SKILL.md:14` "Violating the letter of the rules is violating the spirit of the rules."
- Rationalization tables (Excuse | Reality), mined verbatim from baseline testing — `test-driven-development/SKILL.md:256-270`.
- Red Flags – STOP self-check lists ending in a single collapsing instruction.
- Description = trigger only, never workflow — `writing-skills/SKILL.md:150-172`, with the documented failure that a workflow-summarizing description "caused Claude to do ONE review, even though the skill's flowchart clearly showed TWO reviews".
- Skill authoring IS TDD — baseline-fail before write, pressure-test after, refactor loopholes.
- Fresh-subagent-per-task + two-stage (spec-then-quality) review with the four-status protocol — `subagent-driven-development/SKILL.md:8`, `:106-120`, "Never ignore an escalation or force the same model to retry without changes".
- Verification gate function — IDENTIFY → RUN → READ → VERIFY with a claim→proof table — `verification-before-completion/SKILL.md:25-50`, "Skip any step = lying, not verifying".
- Hard gates with named terminal-state handoffs — `brainstorming/SKILL.md:12-14`, "The ONLY skill you invoke after brainstorming is writing-plans".
- Token-efficiency and progressive disclosure — `<150`/`<200`/`<500` word budgets, `@`-link prohibition ("force-loads … 200k+ context").

**Strengths.** Rhetorical consistency makes discipline instantly legible across domains; rules are empirically grounded (mined from real subagent transcripts, not invented); self-bootstrapping meta-skill gives a reproducible quality bar; context hygiene by design; hard gates prevent the classic jump-to-code failure; verification is operationalized as a mechanical checklist; composability via named successors; cross-harness portability (ships a tool-name mapping for Codex/Copilot/etc.).

**Weaknesses.** Heavy reliance on **rhetorical** pressure rather than mechanical enforcement — a differently-aligned model can still ignore prose; the system itself admits most rules are not automated. Token/review overhead — implementer + 2-3 reviewer dispatches per task. Human-in-the-loop friction in brainstorming conflicts with autonomous runs. Idiosyncratic stylistic prescriptions (banned phrases, a "Strange things are afoot at the Circle K" safe-word) are tied to one human's culture, hurting portability. Effectiveness is validated only by the authors' own pressure scenarios; nothing technically blocks a false "tests pass" claim. Flat namespace + name-only references make discovery depend entirely on description quality. Plans demand complete inline code with no placeholders — powerful but brittle to drift, caught only by manual self-review.

### oh-my-claudecode (OMC)

**What it is.** A Claude Code plugin that turns the main session into a multi-agent orchestrator ("conductor"). The user states intent; OMC selects an execution mode, decomposes work, delegates to ~32 tiered specialist subagents (haiku/sonnet/opus), and refuses to declare completion until a separate Architect agent verifies with fresh evidence. It ships execution modes (autopilot, ralph, ultrawork, ultrapilot, swarm, pipeline, ecomode) and a Stop-hook that mechanically re-injects the agent to keep it working until state files clear.

**Core architecture.** Three layers: (1) **Skills** — keyword-triggered `SKILL.md` files defining modes/workflows; (2) **Agents** — 32+ markdown agent definitions with YAML frontmatter pinning a model and role contract (`architect.md` sets `model: opus, disallowedTools: Write, Edit`); the canonical tier matrix lives in `docs/shared/agent-tiers.md`; (3) **Hooks + state** — `scripts/persistent-mode.mjs` is a Stop hook that, while a mode is `active`, returns `{"decision":"block",...}` to force continuation, with deadlock guards. Modes are hierarchical: autopilot ⊃ ralph ⊃ ultrawork; ecomode is a model-routing modifier; swarm/pipeline are orthogonal (swarm uses a SQLite DB).

**Signature patterns.**
- Conductor / delegation-first orchestrator — workers are blocked from spawning subagents via a Worker Preamble (`src/agents/preamble.ts:8-18` "Do NOT spawn sub-agents"), keeping topology flat.
- Tiered model routing (haiku/sonnet/opus) — `docs/shared/agent-tiers.md:7-25`; orchestrator must pass `model` explicitly on every delegation.
- Architect-verification gate (Iron Law: no completion without fresh evidence) — `skills/orchestrate/SKILL.md:251-287` "NEVER declare a task complete without Architect verification … Return: APPROVED or REJECTED"; the verifier is hard-blocked from Write/Edit via frontmatter; red-flag words "should/probably/seems to" flagged.
- Tiered verification (cost-scaled review) — `docs/shared/verification-tiers.md` LIGHT/STANDARD/THOROUGH with deterministic path triggers (`auth/**`, `.env*`, `schema.*` force THOROUGH); ralph floors at STANDARD.
- Ralph persistence loop via Stop-hook re-injection — `persistent-mode.mjs:313-330` emits `decision:block` while active and under the iteration cap; never blocks context-limit or user-abort stops.
- Hierarchical, composable execution modes with an explicit decision tree and a valid/invalid combination matrix — `docs/shared/mode-hierarchy.md`.
- SQLite atomic task-claiming swarm — `skills/swarm/SKILL.md:216-247` `UPDATE … WHERE status='pending'` in an `.immediate()` transaction; heartbeats + 5-minute lease auto-release dead agents; capped at 5 background agents.
- Phase-gated autopilot pipeline (Expansion → Planning → Execution → QA ≤5 cycles → Validation where all reviewers must APPROVE) — `skills/autopilot/SKILL.md:39-93`.
- PRD/AC discipline — `skills/ralph-init/SKILL.md` emits `prd.json` user stories with `acceptanceCriteria` that must include verifiable gates ("Typecheck passes"), a `passes:false` flag, and priority ordering.

**Strengths.** **Mechanical persistence** — the Stop-hook makes "don't stop until done" a hard system property, not a fragile prompt, with deadlock guards and iteration caps. Strong, frontmatter-enforced separation of concerns (verifier can't mutate; workers can't delegate). Cost discipline is first-class (tiered agents + tiered verification + ecomode). Single source of truth for tiers reduces drift. Composable mode hierarchy with a decision tree. **Concurrency done right** — real ACID atomic claiming with lease-based stale recovery. Evidence-first culture with red-flag word lists.

**Weaknesses.** Heavy prompt surface with duplicated tier tables (verifier confirmed `commands/ralph.md` restates `agent-tiers.md`). Much "orchestration" (pipeline branching, merge strategies) is aspirational prose the model must obey, not engine-executed. The swarm SQLite/TS API is documented as code but is plugin internals the model must wire up at runtime. Hard 5-agent cap bounds fan-out. Verification quality hinges on Architect diligence and honest self-report — a dishonest STANDARD review can pass. Plain-JSON state has cross-session/worktree edge cases handled by heuristics that can misfire. Strong delegation adds latency/cost for trivial edits.

### karpathy (skill-writing philosophy)

**What it is.** A design *sensibility* for authoring agent skills — not a repo or product. Its goal is maximum behavior-change per token: minimal frontmatter (just `name` + a sharp "what + when" description), checklists/tables over prose, one dependency-free example over many, and ruthless concision where "every token earns its place." It treats the model as already-smart, supplying only what it lacks (trigger signal, non-obvious procedure, loophole closure). On disk it is most realized by superpowers' `writing-skills` guidance and Anthropic's "Concise is key" best-practices, in deliberate contrast to the heavyweight official `skill-creator`.

**Core architecture.** No runtime — a set of authoring constraints on a single `SKILL.md` plus optional bundled files, organized by progressive disclosure across three load tiers (metadata always resident; body on trigger; bundled resources on demand). The lifecycle it endorses is TDD-for-docs: write a failing pressure test (baseline behavior without the skill), write the minimal skill that fixes exactly those failures, refactor to close loopholes. The "gate" is behavioral compliance under pressure, not an eval-score harness.

**Signature patterns** (all verifier-grounded).
- Two-field minimal frontmatter — `writing-skills/SKILL.md:95-98` "Two required fields: name and description … Max 1024 characters".
- Description = WHEN to use, never WHAT it does — `:150-158`.
- Ruthless concision — `:217-220` word budgets; `anthropic-best-practices.md:22-28` "Does this paragraph justify its token cost?".
- Checklists and tables over prose — quick-reference tables, rationalization tables, red-flag lists.
- One excellent, dependency-free example beats many — `:326-345` "Don't: Implement in 5+ languages / Create fill-in-the-blank templates".
- No narrative / no storytelling — `:26-29`.
- Behavioral verification (TDD-for-docs), not an eval harness — `:16`, `:533-561`.
- Cross-reference, don't force-load — `:278-288`.
- Verb-first, gerund naming carrying the core insight — `:208-211`.

**Strengths.** Trigger fidelity (WHEN-only descriptions prevent body-skipping); low resident cost so many skills coexist; scannability; cheap to ship (behavioral pressure-testing without a benchmark pipeline); portability via one abstract example; anti-rot via the no-narrative rule.

**Weaknesses.** **Direct tension with the official standard**: `skill-creator` deliberately puts WHAT-it-does plus a "pushy" nudge into the description to fight under-triggering — minimalism can under-trigger. Under-specification risk: "Claude is already smart" can omit context a fragile/deterministic task genuinely needs. Weak quantitative feedback — behavioral tests give no pass-rate/variance/regression signal. Checklist-over-prose can strip the WHY (the official guidance warns ALL-CAPS MUSTs are a "yellow flag"). Minimal frontmatter omits the version/owner/compatibility metadata a distribution system needs. No built-in packaging/discovery story.

> Note on grounding: the *philosophy* and its nine signature patterns are solidly grounded, but the verifier found the *weaknesses* section misattributed three citations to a sibling file (one to an impossible line number). The underlying tension is real and lives in `skill-creator/SKILL.md` (`:67` "pushy", `:302` "yellow flag"); it is presented here as the substantive tension it is, with corrected attribution.

### native-anthropic (Claude Code native standard)

**What it is.** Anthropic's first-party standard for model-invoked Skills. The contract is a directory with a required `SKILL.md` (YAML frontmatter + Markdown body) plus optional `scripts/`, `references/`, `assets/`. The `skill-creator` meta-skill is a full toolchain: draft a skill, run behavioral evals (with-skill vs baseline subagents), grade against assertions, benchmark with variance analysis, and — distinctively — an **automated description-optimization loop** that tunes the frontmatter `description` for triggering accuracy. `plugin-dev/skill-development` is the plugin-targeted sibling with a stricter style guide.

**Core architecture.** Frontmatter: `name` (required, kebab-case, ≤64 chars), `description` (required, ≤1024 chars, no angle brackets); optional `license`, `allowed-tools`, `metadata`, `compatibility`, `version`. Three-level progressive disclosure: name+description always resident (~100 words); body on trigger; bundled resources on demand (scripts can execute without entering context, so the third tier is effectively unlimited). The creator lifecycle is an iteration loop: intent → draft → generate test prompts → spawn with-skill AND baseline subagents in the same turn → grade (`grader.md`) → aggregate to `benchmark.json` (mean±stddev, delta) → analyst pass → HTML viewer → read feedback → improve → repeat. `quick_validate.py` enforces the frontmatter schema; `package_skill.py` zips to a distributable `.skill`.

**Signature patterns** (all verifier-grounded verbatim).
- Description-as-trigger contract, deliberately "pushy" — `skill-creator/SKILL.md:67` "please make the skill descriptions a little bit 'pushy' … even if they don't explicitly ask for a 'dashboard.'".
- Three-level progressive disclosure — `plugin-dev/skill-development/SKILL.md:79-85`.
- `scripts/` + `references/` + `assets/` sidecar taxonomy with explicit inclusion criteria.
- Frontmatter schema enforced by a validator — `quick_validate.py:42` `ALLOWED_PROPERTIES = {name, description, license, allowed-tools, metadata, compatibility}`; unknown keys fail.
- **Automated description-optimization loop with train/test split** — `run_loop.py` stratifies by `should_trigger` into 60/40 train/test, runs each query 3× via `claude -p`, proposes a new description via extended thinking, and selects by **held-out TEST score** to avoid overfitting (`SKILL.md:394`).
- Empirical with-skill vs baseline A/B harness — `SKILL.md:169-171` "Spawn all runs … in the same turn".
- Grader as adversary + assertion critic — `grader.md:9` "A passing grade on a weak assertion is worse than useless".
- Strict JSON schemas with viewer-coupled field names — `schemas.md:305` warns a renamed field "will cause the viewer to show empty/zero values".
- Anti-overfit, explain-the-why philosophy — `SKILL.md:302` "If you find yourself writing ALWAYS or NEVER in all caps … that's a yellow flag".
- Bundle-the-repeated-script signal — `SKILL.md:304` "If all 3 test cases resulted in the subagent writing a create_docx.py … bundle that script".

**Strengths.** Triggering treated as empirically measurable and optimizable (not prose intuition), with anti-overfit held-out testing. Clean separation via the taxonomy + 3-level disclosure keeps resident context tiny while allowing unbounded capability. Behavioral A/B produces a quantified value delta. The grader doubles as an assertion critic, guarding against false confidence. Machine-enforced schema + deterministic packager make skills portable and CI-checkable. Strong "explain the why / avoid ALL-CAPS / generalize, don't overfit" philosophy. Graceful environment adaptation (Claude.ai / Cowork / Claude Code variants).

**Weaknesses.** **Two competing official standards diverge**: `skill-creator` says descriptions should be "pushy"/imperative, while `plugin-dev/skill-development` mandates third-person — the marketplace itself is inconsistent. The eval/optimization tooling is Python + Anthropic-SDK + `claude -p` heavy (parses stream-json, strips `CLAUDECODE` env) — powerful but brittle and CLI-coupled, needing an API key. The viewer's hard dependency on exact JSON field names is a footgun with no pre-render schema validation. Body budgets stated inconsistently (`<500 lines` vs `1,500-2,000 words`). The 1024-char description cap fights the "pushy + enumerate triggers" guidance. No first-party worked eval set ships with `skill-creator` to copy from.

### gstack

**What it is.** An open-source, MIT-licensed TypeScript skills framework (Garry Tan) that casts a coding agent as a "virtual engineering team" of ~23 role-personas (Founder/CEO, Staff Engineer, QA Lead, Release Engineer, Security auditor) wired into a sprint lifecycle (Think → Plan → Build → Review → Test → Ship → Reflect). Each skill is a markdown slash command encoding a distinct persona with forcing-questions, hard gates, and an anti-sycophancy tone lock. It targets Claude Code primarily, plus Codex CLI, Cursor, and others.

**Core architecture.** Per-skill directories each contain a `SKILL.md` plus supporting files. Crucially, `SKILL.md` files are **generated from `SKILL.md.tmpl` templates by `scripts/gen-skill-docs.ts`**, formatted per host, with a "trim"/catalog mode that shortens frontmatter to the lead sentence and moves routing/voice prose into a "When to invoke" section to save context. Frontmatter carries `name`, `version`, `description` (suffixed "(gstack)"), `preamble-tier` (1-4, controlling shared-boilerplate injection), `allowed-tools`, `triggers`. `scripts/skill-check.ts` is a static validator that walks discovered skills, calls `validateSkill()`, and `process.exit(hasErrors ? 1 : 0)` — gating on unknown commands, snapshot-flag errors, and stale generated docs (via `--dry-run`). A single agent shape-shifts persona per skill; heavy skills fan out parallel specialist sub-agents (e.g. `/review` → testing/security/perf/maintainability/api-contract reviewers, merged with dedup + confidence gating). Memory: `~/.gstack/projects/{slug}/learnings.jsonl` loaded at skill start, searched, and appended at session end.

**Signature patterns.**
- BAD/GOOD anti-sycophancy pairs reused across skills — both `investigate/SKILL.md` and `review/SKILL.md` quote the same pair: Bad "I've identified a potential issue in the authentication flow…" vs Good "auth.ts:47 returns undefined when the session cookie expires. … Fix: add a null check … Two lines." (verifier-confirmed verbatim in both files).
- HARD GATE / Iron Law blocking rules — `investigate/SKILL.md` "NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST"; "Three failed hypotheses → STOP and escalate"; ">5-file blast radius requires AskUserQuestion"; review's "cite evidence or confidence forced to suppressed".
- Structured completion-status protocol — `investigate/SKILL.md` DONE / DONE_WITH_CONCERNS / BLOCKED with explicit definitions.
- Template-generated, multi-host, tiered `SKILL.md` with `preamble-tier` and trim mode — confirmed via deepwiki "template-based generation pipeline … consistent across different model families and agent platforms".
- Static SKILL validator gating CI — `scripts/skill-check.ts` + `test/helpers/skill-parser.ts`'s `validateSkill()` returning `valid/invalid/snapshotFlagErrors/warnings`.
- Persistent per-project learnings corpus — load-at-start, surface-before-recommendation, append-at-end, scoped per slug as JSONL with confidence scores.
- A voice/tone lock banning AI filler vocabulary — root `SKILL.md` "Direct, concrete, builder-to-builder … No em dashes. No AI vocabulary: delve, crucial, robust, comprehensive, nuanced, multifaceted" (verifier-confirmed verbatim).
- Review Readiness Dashboard distinguishing a single blocking gate (Eng Review) from informational ones; cross-AI adversarial review via `/codex` ("two doctors, same patient").

**Strengths.** Anti-sycophancy authoring (voice-lock + BAD/GOOD pairs) is a cheap, model-agnostic lever that converts flattery into concrete file:line findings. Hard gates encode "fail loudly / BLOCKED" instead of optimistic completion. Template + generated `SKILL.md` + static validator means author-once, distribute-to-many-hosts without per-host drift, with CI catching staleness. Structured completion-status enum makes self-reports machine-parseable. Per-project learnings give durable, confidence-scored memory surviving compaction. One explicit blocking ship gate (Eng Review) rather than every reviewer blocking. Cross-AI adversarial review is concrete and low-cost.

**Weaknesses.** **The static validator does not structurally enforce the persona, HARD GATE, or BAD/GOOD prose** — it validates embedded commands and generated-doc staleness; authoring discipline rests on the template + human review, so a syntactically-valid but malformed skill can slip through. Highly opinionated and founder-workflow specific (CEO/office-hours/YC personas) — may not transfer to other org contexts. Heavy bespoke shell tooling (`gstack-learnings-log`, `$B` browser CLI, iOS CoreDevice tunnel) increases install/OS coupling. The learnings JSONL has no shown schema validation/GC beyond a >5-entry search trigger — risk of unbounded low-signal accumulation. Single-agent persona-switching (vs isolated agents) carries all role state in one context, relying on prose to keep modes from bleeding. 23-skill catalog risks context bloat, mitigated only by trim mode.

> Note on grounding: the verifier flagged the "persona-first-line (`You are Claude Code…`)" claim as **fabricated** — that string appears nowhere in the cited skill, and the "Tone Lock" label, a truncated consultant quote, and a reconstructed dashboard table were presented as verbatim. This document therefore **drops** the persona-first-line pattern and does not recommend mandating an identity first line on gstack's authority. The verified levers (voice-lock vocabulary ban, BAD/GOOD pairs, hard gates, status enum, validator, learnings corpus, template generation) are retained.

---

## Cross-framework pattern matrix

Cell legend: **strong** = a defining, mechanically- or structurally-embodied pattern; **partial** = present but advisory/incomplete/honor-system; **—** = absent or out of scope. Notes are 2-4 words.

| Pattern | spec-kit | speckit-applied | superpowers | OMC | karpathy | native-anthropic | gstack |
|---|---|---|---|---|---|---|---|
| Numbered-artifact lifecycle | **strong** per-feature dir | **strong** feature.json state | partial plan files | partial `.omc/` artifacts | — no runtime | — single file | partial sprint artifacts |
| Constitution-as-DNA | **strong** re-checked gate | **strong** semver + sync | — | — | — | — | partial voice/persona rules |
| `[NEEDS CLARIFICATION]` markers | **strong** cap 3 | **strong** cap 3 + clarify 5 | — implicit in brainstorm | — | — | — | partial forcing-questions |
| Iron-Law / STOP rhetoric | partial gate prose | **strong** STOP prompts | **strong** code-fenced law | **strong** verify Iron Law | partial via red-flags | partial anti-ALL-CAPS | **strong** hard gate + 3-strike |
| Verification-before-completion | partial analyze read-only | partial CRITICAL block | **strong** gate function | **strong** Architect gate + hook | partial behavioral test | **strong** A/B + grader | **strong** status enum + evidence |
| TDD-first | partial OPTIONAL tests | partial OPTIONAL | **strong** RED-GREEN law | partial AC "tests pass" | **strong** TDD-for-docs | **strong** eval-driven | partial regression-test in status |
| Subagent / parallel orchestration | partial `[P]` hints only | partial via hooks | **strong** fresh-per-task | **strong** tiered + swarm | — | partial eval subagents | **strong** specialist fan-out |
| Tiered model routing | — agent-agnostic | — | partial model escalation rule | **strong** haiku/sonnet/opus | — | — | partial preamble-tier (context) |
| Worktree isolation | — | partial git-feature hook | **strong** detect + provenance | partial `.omc/` + PSM | — | — | — |
| Description-as-trigger | partial frontmatter | partial frontmatter | **strong** WHEN-only | partial keyword trigger | **strong** WHEN-only rule | **strong** measured + "pushy" | partial trim "When to invoke" |
| Progressive disclosure | partial templates | partial scripts on demand | **strong** word budgets + no-@ | partial shared docs | **strong** 3-tier + budgets | **strong** 3-tier + scripts | partial preamble-tier + trim |
| Minimal-meta authoring | partial | partial | **strong** 2-field | — heavy prose | **strong** 2-field | partial schema'd frontmatter | partial richer frontmatter |
| AC / PRD discipline | **strong** traceability | **strong** traceability | partial plan tasks | **strong** prd.json + passes | — | — | partial forcing-questions |
| Gates / checklists | **strong** constitution + analyze | **strong** checklist STOP | **strong** two-stage review | **strong** validation phase | partial creation checklist | **strong** validator + grader | **strong** Eng Review gate |
| Deterministic script layer | **strong** bash/PS + JSON | **strong** `.specify/` scripts | partial test runners | partial swarm SQLite | — | **strong** validate/eval/package | **strong** gen + skill-check.ts |
| Cross-AI adversarial check | — | — | partial Codex tool-map | partial Codex advisory | — | — | **strong** `/codex` two-doctors |
| Persistent cross-session memory | partial files | partial feature.json | — | partial notepad/state | — | — | **strong** learnings.jsonl |
| Hook-enforced continuation | — | — | — | **strong** Stop-hook re-inject | — | — | partial PreToolUse safety hooks |
| Empirical trigger optimization | — | — | partial pressure tests | — | partial behavioral | **strong** train/test loop | partial validator only |
| Anti-sycophancy / tone lock | — | — | **strong** no-gratitude rule | partial red-flag words | partial | partial explain-why | **strong** voice ban + BAD/GOOD |
| Atomic task claiming (concurrency) | — | — | — | **strong** SQLite IMMEDIATE | — | — | — |
| Lifecycle hooks (before/after) | **strong** extensions.yml | **strong** in every skill | partial named successors | partial mode composition | — | — | partial safety hooks |

---

## Tensions & tradeoffs

**1. Heavy gates (spec-kit / speckit-applied) vs minimalism (karpathy).** spec-kit demands a numbered-artifact set, a constitution gate, a clarify loop, a checklist, and a read-only analyzer before code; karpathy says every token must earn its place and the model is already smart. **Position:** these operate at different layers and should be combined, not chosen between. Use karpathy's *authoring* discipline (lean bodies, WHEN-only descriptions, one example, no narrative) for **how each skill is written**, and spec-kit's *lifecycle* discipline (artifacts, traceability, gates) for **how skills chain into an SDLC**. The synthesis: heavyweight pipeline, lightweight prose. A 5k-word command file like OMC's is the failure mode of ignoring karpathy; an ungated free-for-all is the failure mode of ignoring spec-kit.

**2. OMC "delegate everything" vs single-agent simplicity (superpowers/gstack persona-switching).** OMC forbids the orchestrator from doing any substantive work; gstack runs one agent that shape-shifts personas; superpowers delegates to fresh subagents but only for plan execution. **Position:** delegation should be **proportional to task size and verification independence**, not absolute. Trivial edits routed through a subagent (OMC's acknowledged latency/cost weakness) waste tokens; but *verification* must always be an independent, write-disabled agent (OMC's and gstack's strongest idea) because a self-grading agent over-claims. Adopt: orchestrator may do trivial, fully-reversible edits directly; **all non-trivial implementation and all verification go to separate agents**, and verifiers can never mutate code (`disallowedTools: Write, Edit`).

**3. Mechanical enforcement (OMC Stop-hook, native validators) vs rhetorical enforcement (superpowers Iron Law, gstack hard gates).** superpowers and gstack lean on ALL-CAPS prose that a differently-aligned model can ignore; OMC's Stop-hook and native-anthropic's `quick_validate.py` are real code. **Position:** rhetoric is necessary but insufficient — it shapes the model's default behavior cheaply, but anything load-bearing (gate passage, completion claims, schema conformance, doc staleness) must have a mechanical backstop. The gstack weakness is decisive evidence: its validator checks *commands* but not the persona/gate *prose*, so a malformed skill ships. **Every gate should pair an Iron-Law statement (cheap behavioral nudge) with a mechanical check (the actual enforcement).**

**4. Auto-branch / auto-worktree vs user choice.** superpowers auto-isolates a worktree with provenance-checked cleanup; speckit-applied deliberately decouples spec-dir from branch and delegates branch creation to an *optional* hook; OMC has PSM worktrees. **Position:** isolation should be **automatic but provenance-safe and opt-outable** — superpowers' "only remove worktrees I created" rule resolves the real danger (clobbering user state). Couple identity to a persisted pointer file (speckit's `feature.json`), **not** to the branch name, so the pipeline runs identically headless, in CI, or with VCS absent. Auto-create, never auto-destroy unowned state.

**5. Description "pushy + what-it-does" (native-anthropic) vs "WHEN-only, never what" (karpathy/superpowers).** native-anthropic deliberately stuffs the description with what-it-does and a pushy nudge to fight under-triggering; karpathy/superpowers forbid workflow summaries because the model follows the summary and skips the body (the documented "one review instead of two" failure). The marketplace is internally inconsistent here. **Position:** separate the two audiences. The **model-injected** `description` should be WHEN-only and pushy about triggering conditions (resolving both camps: triggering signal yes, *workflow* summary no), while a separate non-injected `whatItDoes`/catalog field serves human browsing. Then **measure** triggering empirically (native-anthropic's train/test loop) rather than arguing about it — the disagreement is an empirical question, not a stylistic one.

**6. Empirical eval machinery (native-anthropic) vs cheap behavioral testing (karpathy/superpowers).** native-anthropic ships a Python+SDK benchmark/variance/viewer pipeline; karpathy ships on a single pressure-test transcript. **Position:** hybrid by skill value. Default to the cheap behavioral gate (baseline-vs-with-skill transcript) for every skill; reserve the full train/test trigger-optimization and variance benchmark for **high-traffic, contested, or safety-critical** skills. The native pipeline's CLI/API coupling and viewer-field fragility make it too heavy to mandate per skill.

**7. Duplicated prose (spec-kit/speckit-applied/OMC) vs single-source-of-truth (gstack templates, OMC's own docs/shared aspiration).** spec-kit copy-pastes a ~55-line hook block into 9 files; speckit-applied duplicates ~500 lines; OMC restates tier tables. gstack solves this with `gen-skill-docs.ts` generating from `.tmpl`. **Position:** unambiguous — **generate, don't copy.** Author canonical templates with shared includes (the hook protocol, the tier table, the voice lock) and generate per-host `SKILL.md`, with a static validator (gstack's `--dry-run`) that fails CI on stale generated output. This is the single highest-leverage maintainability fix across the corpus.

---

## Extraction recommendations

Priorities: **P0** = adopt first; foundational and high-leverage. **P1** = adopt next; strong value, depends on or complements P0. **P2** = valuable refinements.

### P0 — foundational

**P0-1. Independent, write-disabled verifier as a mandatory completion gate.**
*Sources:* OMC (`architect.md` `disallowedTools: Write, Edit`; `orchestrate/SKILL.md:251-287`), superpowers (verification gate function + claim→proof table), gstack (status enum + cite-evidence-or-suppress), native-anthropic (grader-as-assertion-critic).
*Why:* The universal LLM failure is over-claiming completion. Every framework that takes quality seriously converges on a separate reviewer that cannot edit and must produce APPROVED/REJECTED with evidence.
*How to adapt:* Ship a `verify` skill with frontmatter `allowed-tools` excluding Write/Edit. Its contract: receive a structured completion request (original task / changes made / verification commands run), execute the verification itself (IDENTIFY→RUN→READ→VERIFY), and emit one of `DONE` / `DONE_WITH_CONCERNS` / `BLOCKED` plus file:line evidence. REJECTED loops back to fix → re-verify. Mirror gstack's "cannot quote a line → confidence suppressed." Make this skill callable identically by both Claude (subagent) and Codex (`/codex` adversarial pass treating overlap as high-confidence).

**P0-2. WHEN-only, measured, pushy-about-triggering description contract + machine-validated frontmatter.**
*Sources:* karpathy / superpowers (WHEN-only), native-anthropic (`quick_validate.py` schema; train/test trigger optimization; "pushy"), gstack (frontmatter contract + `skill-check.ts`).
*Why:* In a catalog of dozens of skills, correct selection is the bottleneck; a workflow-summarizing description causes documented body-skipping, and an unmeasured one under-triggers.
*How to adapt:* Define a strict frontmatter schema (`name` kebab-case ≤64, `description` ≤1024 no-angle-brackets, plus SDLC fields `phase`, `requires`, `produces`, `next`, `owner-role`, `model-tier`). Lint: the injected `description` must read as triggering conditions ("Use when…"), may be pushy about *when*, must not contain step/workflow verbs; a separate non-injected `whatItDoes` serves human catalogs. Reuse native-anthropic's `run_loop` train/test pattern as an **optional CI gate** for high-traffic skills (8-10 should-trigger near-synonyms + 8-10 cross-skill near-miss negatives, run 3×, fail PR on held-out test regression).

**P0-3. Mechanical enforcement backing every Iron-Law gate.**
*Sources:* OMC (Stop-hook `persistent-mode.mjs`; frontmatter tool-blocking), native-anthropic (validators/packager), gstack (`skill-check.ts` non-zero exit) — contrasted against superpowers/gstack honor-system prose.
*Why:* The gstack lesson is conclusive: a validator that checks commands but not gate-prose lets malformed skills ship. Rhetoric shapes defaults cheaply but cannot be the only guard on load-bearing transitions.
*How to adapt:* Pair each behavioral gate with a real check. (a) Completion: a turn-end hook (OMC pattern) that reads a per-task state file (`active`, `iteration`, `cap`) and re-injects while incomplete, with deadlock guards (never block context-limit or user-abort). (b) Schema/staleness: a `skill-check`-style validator that fails CI on bad frontmatter, missing required structural sections, and stale generated docs (`--dry-run`). (c) Tool boundaries: enforce verifier read-only and worker no-spawn via the harness's tool whitelist, not prose.

**P0-4. Generate skills from templates; never copy prose.**
*Sources:* gstack (`gen-skill-docs.ts` + `.tmpl` + trim mode + `--dry-run` staleness check); anti-pattern from spec-kit/speckit-applied/OMC duplication.
*Why:* The corpus's most pervasive maintainability defect is copy-pasted boilerplate (~500 duplicated lines in speckit-applied) that drifts. Templating fixes it and enables one-source multi-host (Claude + Codex) parity.
*How to adapt:* Author canonical `SKILL.md.tmpl` with shared includes (hook protocol, tier table, voice lock, status-enum block). Generate per-host outputs (Claude Code skill dirs; Codex/`AGENTS.md` variants) from one source. Ship a trim/catalog mode that emits only the WHEN-only lead + a "When to invoke" block for the always-resident tier, expanding full body only on invocation. Gate CI on generated-doc staleness.

### P1 — strong value

**P1-5. Phase-as-skill with declared prerequisites, produces/next contracts, and a deterministic prerequisite resolver.**
*Sources:* speckit-applied (`requires`/abort-with-remediation; `feature.json`), spec-kit (numbered artifacts + `check-prerequisites.sh` JSON).
*Why:* Lets a multi-agent SDLC distribute one atomic skill per phase that any agent picks up, with ordering surviving even without a central orchestrator.
*How to adapt:* Each skill's frontmatter declares `phase`, `requires: [<artifact|skill>]`, `produces: [<artifact>]`, `next: [<skill>]`. Ship a shared `resolve-prerequisites` helper (POSIX + PowerShell or a portable Python/Node script) returning absolute artifact paths + a missing-list as JSON; every skill calls it first and self-aborts with the exact remediation command. Persist cross-phase state in one pointer file (`work.json`: feature_directory, phase_status, produced_artifacts) decoupled from the git branch.

**P1-6. Tiered model routing + tiered verification driven by change metadata, with one source-of-truth table.**
*Sources:* OMC (`agent-tiers.md`, `verification-tiers.md` LIGHT/STANDARD/THOROUGH, deterministic path triggers).
*Why:* A principled, auditable cost/quality dial — cheap models for small well-tested diffs, expensive review only for large/security/architectural changes.
*How to adapt:* Define a `ChangeMetadata` struct (files, lines, hasSecurity, hasArch, testCoverage) and a pure `selectTier()` shared by every mode. Pin each role to a model in frontmatter. Auto-escalate on glob path patterns (`auth/**`, `.env*`, `schema.*` → THOROUGH). Keep exactly **one** tier table; skills reference it ("first action: read the tier doc"), never restate it — explicitly avoiding OMC's own duplication weakness. For Codex parity, express tiers as an abstract LOW/MED/HIGH that maps to each harness's model lineup.

**P1-7. Discipline-skill triad: Iron Law + Excuse|Reality table + Red-Flags STOP list, mined from real transcripts.**
*Sources:* superpowers (the canonical shape), gstack (hard gate + BAD/GOOD pairs + voice lock).
*Why:* SDLC discipline points (TDD, verify-before-complete, no-fully-qualified-names) are exactly where agents rationalize under pressure; redundant counters resist whichever escape the agent reaches for.
*How to adapt:* Make three sections **required** for any `type: discipline` skill in the template: a code-fenced one-line Iron Law, a two-column Excuse|Reality table, and a "Red Flags — STOP" list ending in one collapsing instruction. **Populate the rows from baseline pressure-test transcripts, not imagination.** Add gstack's voice lock (ban AI filler vocabulary) and at least one BAD/GOOD file:line pair to every output-producing skill, anchored on a concrete calibration example. (Do *not* mandate a persona identity first-line — that gstack claim was unverified.)

**P1-8. PRD-as-JSON with machine-checkable acceptance criteria and `passes` flags.**
*Sources:* OMC (`ralph-init` `prd.json`), spec-kit/speckit-applied (traceability requirements → tasks → coverage).
*Why:* Turns vague intent into trackable, independently-completable units whose AC embed verifiable gates (typecheck/tests), enabling progress tracking and resumability.
*How to adapt:* The intake phase emits `prd.json` of user stories (`id`, `acceptanceCriteria` that MUST include "typecheck passes"/"tests pass", `priority`, `passes:false`). Order foundational stories (types/schema/DB) before UI. Flip `passes:true` only on fresh verification evidence (ties to P0-1). Combine with spec-kit's coverage-table traceability so the analyzer can flag any requirement with zero covering tasks.

**P1-9. Read-only cross-artifact analyzer with severity model + coverage matrix as the pre-implement gate.**
*Sources:* spec-kit / speckit-applied (`analyze.md` STRICTLY READ-ONLY, six passes, CRITICAL/HIGH/MEDIUM/LOW, ≤50 findings, requirement→task coverage), gstack (parallel specialist fan-out + dedup + confidence gating).
*Why:* A non-destructive pre-flight catches drift, zero-coverage requirements, and policy violations before code — the cheapest place to fix them.
*How to adapt:* Ship an `analyze` skill with a hard read-only contract, a fixed severity model (CRITICAL = policy/coverage blocker), deterministic finding IDs (reproducible re-runs), a findings cap to bound tokens, and a coverage table mapping every requirement to its tasks. Its output (coverage % + critical count) becomes the gate signal that blocks `implement` on CRITICAL. For heavy reviews, fan out parallel specialist reviewers (testing/security/perf) and merge with dedup + confidence thresholds (gstack), then a cross-model adversarial pass (Claude vs Codex), treating overlap as high-confidence.

### P2 — refinements

**P2-10. Uniform before_/after_ lifecycle-hook protocol with optional-vs-mandatory semantics — referenced, not inlined.**
*Sources:* speckit-applied (the protocol), spec-kit (`extensions.yml` + workflow gates). *Anti-pattern source for the fix:* their own duplication.
*How to adapt:* Factor the hook protocol into ONE shared reference; each skill says "run the before_<phase> hooks protocol" instead of inlining it. Keep optional (offer to user/agent) vs mandatory (`EXECUTE_COMMAND`, block until result). Map mandatory after-hooks to synchronous sub-agent calls; optional hooks to suggested follow-ups. Validate that every named hook target skill actually exists (closing speckit's brittle dots→hyphens gap).

**P2-11. SQLite atomic task-claiming with heartbeats + lease recovery for fan-out.**
*Sources:* OMC (`swarm/SKILL.md` `UPDATE … WHERE status='pending'` `.immediate()`, 5-min lease).
*How to adapt:* For parallel multi-agent execution, back the shared task pool with SQLite using IMMEDIATE transactions for race-free claiming, a heartbeats table, and periodic cleanup releasing claims past a lease timeout. Derive a file-ownership map from the `[P]`/file-path task grammar so concurrent agents write disjoint files (conflict detection key = file path). Cap concurrency to the harness's background-agent limit.

**P2-12. Persistent per-project learnings corpus with schema validation and decay.**
*Sources:* gstack (`~/.gstack/projects/{slug}/learnings.jsonl`), OMC (notepad/project-memory).
*How to adapt:* Standardize a per-repo JSONL store (`skill`, `type`, `confidence`, `timestamp`, entry). Inject a preamble step that loads + searches it before recommendations ("Prior learning applied"); a post-skill reflection step appends only durable, non-obvious fixes. Add the schema validation and GC/decay gstack lacks (cap size, decay low-confidence entries) to prevent unbounded low-signal accumulation. Scope per slug so learnings don't cross-contaminate.

**P2-13. Worktree isolation: detect-first, native-tool-first, provenance-checked cleanup.**
*Sources:* superpowers (`using-git-worktrees` GIT_DIR≠GIT_COMMON detection + submodule guard; "only remove worktrees I created").
*How to adapt:* A shared infra skill any parallel mode calls first: detect existing worktrees (with submodule guard), verify the dir is gitignored, and on cleanup remove **only** worktrees under known-owned paths. Auto-create, never auto-destroy unowned state — the safe resolution to the auto-branch-vs-user-choice tension.

**P2-14. Bundle-the-repeated-script heuristic + three-bucket sidecar taxonomy.**
*Sources:* native-anthropic (`scripts/`+`references/`+`assets/`; "if ≥N transcripts wrote the same helper, bundle it"), karpathy (one dependency-free example; cross-reference don't force-load).
*How to adapt:* Mandate the sidecar taxonomy: `scripts/` for deterministic SDLC steps (lint, scaffold, schema-validate) invoked rather than re-derived in-context; `references/` loaded on demand; `assets/` for output templates. Mine agent transcripts across tickets and auto-suggest a `scripts/` helper when ≥N agents independently wrote the same code. Forbid `@`-style eager includes in the linter; resolve `requires:` lazily.

---

## What each framework should NOT contribute

**spec-kit — avoid:** the **placeholder constitution** anti-pattern (a 100%-`[PLACEHOLDER]` constitution silently passes the gate — any constitution gate must fail-closed when unfilled); brittle task-line string-matching as the implement interface (parse structured data, not regex on prose); plain-file state with no locking for concurrent agents; treating tests as OPTIONAL in core; and the copy-pasted ~55-line hook block.

**speckit-applied — avoid:** the **~500 lines of duplicated hook prose** across 9 skills (generate it — P0-4); shipping skills that are **inert without an unbootstrapped runtime** and providing no skill to verify/bootstrap that runtime; underspecified skills whose body contradicts their frontmatter promise (`taskstoissues` "dependency-ordered" vs body "create a new issue"); inferring phase completion purely from file presence (a corrupt artifact passes prerequisite checks); and heavy human-in-the-loop Q&A with no designated autonomous answerer.

**superpowers — avoid:** **rhetoric as the sole enforcement** (nothing technically blocks a false "tests pass" claim — back every law with a mechanical check, P0-3); **idiosyncratic cultural prescriptions** tied to one human's `CLAUDE.md` (banned-gratitude phrases, the "Circle K" safe-word) — keep the *structure*, drop the personality; mandatory complete-inline-code plans with zero placeholders and only manual drift-checking; and the unbounded review cost of 2-3 reviewer dispatches per task on large plans (scale review effort to change profile instead).

**OMC — avoid:** **prose-as-engine** — pipeline branching, loop constructs, and merge strategies described as if executed but actually LLM-followed conventions (don't present advisory orchestration as guaranteed behavior); **duplicated tier tables** that drift from the supposed source of truth (P1-6); **delegate-everything** for trivial reversible edits (latency/cost with no quality gain); coupling correctness to the model correctly importing a runtime TS module (`import from ./swarm`); and overly long multi-thousand-word `SKILL.md` mode files that violate progressive-disclosure budgets.

**karpathy — avoid:** **under-specification by over-trusting the model** ("Claude is already smart" wrongly omits context fragile/deterministic tasks genuinely need — high-freedom prose is wrong where steps must be exact); WHEN-only descriptions taken so far they **under-trigger** (measure, don't assume — P0-2); checklist-over-prose that **strips the WHY** (the official guidance's "yellow flag" on ALL-CAPS MUSTs is right — explain reasoning so the model generalizes); and the philosophy's silence on **governance metadata and packaging** (a distribution system needs version/owner/compatibility and a `.skill`-style artifact).

**native-anthropic — avoid:** the **CLI/SDK-coupled eval machinery** as a hard dependency (Python + `claude -p` stream-json parsing + env-stripping is brittle and needs an API key — make the full pipeline opt-in for high-value skills, P2 hybrid); **viewer-coupled JSON schemas** that silently render empty on a renamed field with no pre-render validation (validate schemas before consuming them); the **internally inconsistent description guidance** (pushy/what-it-does vs third-person — pick the WHEN-only resolution in P0-2); and shipping a meta-skill with **no first-party worked eval example** to copy from.

**gstack — avoid:** the **unverified persona-first-line** ("You are Claude Code…") — do not mandate an identity first-line on gstack's authority (the claim was fabricated); a **validator that checks commands but not the load-bearing gate/persona prose** (validate the structural sections that actually carry the discipline, P0-3); **founder-workflow-specific personas** (CEO/office-hours/YC questions) baking in startup assumptions that don't transfer; **heavy bespoke OS-coupled tooling** (custom browser CLI, iOS CoreDevice tunnel) that inflates install surface; a **learnings store with no schema validation or GC** (add both, P2-12); and relying on single-context persona-switching where role state bleeds — prefer isolated agents for independent verification.
