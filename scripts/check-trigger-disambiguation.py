#!/usr/bin/env python3
"""Trigger-disambiguation guard for quivo.

`test-skill.sh [4/5]` only checks that a trigger prompt FILE exists. It does NOT
check whether that prompt actually points at its own skill rather than colliding
with an adjacent skill (e.g. research-analyze vs spec-analyze, research-pipeline
vs pipeline). Real triggering is decided by an LLM matching the prompt against
skill *descriptions*, which we can't run in CI — so this is a deterministic
proxy: score each trigger prompt against every skill's description by
IDF-weighted shared-token overlap, and assert the prompt's OWN skill ranks #1.

It catches the regression the panel flagged: a prompt whose wording matches a
sibling skill's description as well as (or better than) its own. It is a
heuristic, not an LLM judge — treat a failure as "descriptions/prompt need a
sharper boundary keyword", and a pass as "no gross keyword collision".

Exit 0 if every prompt ranks its own skill within the top 3 (near-siblings that
aren't the unique #1 are reported as advisory warnings, not failures); exit 1
only on a HARD collision — a prompt whose own skill isn't even top-3, i.e. a
broken or colliding description. Pure stdlib.

Usage:
  python3 scripts/check-trigger-disambiguation.py
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import yaml

SKILLS_DIR = Path("skills")
PROMPTS_DIR = Path("tests/skill-triggering/prompts")
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)^---\s*\n", re.DOTALL | re.MULTILINE)

# Ultra-common structural words that carry no disambiguating signal.
# (IDF already down-weights frequent tokens; this is belt-and-suspenders.)
STOP = {
    "사용", "생성", "때", "등", "및", "또는", "한", "할", "수", "있", "본", "그",
    "이", "저", "것", "를", "을", "는", "은", "이때", "관련", "단계", "스킬",
    "context", "slug", "md", "use", "when", "the", "for", "and", "to", "of",
    "a", "an", "with", "this", "skill", "atom",
}

TOKEN = re.compile(r"[가-힣]{2,}|[a-zA-Z][a-zA-Z0-9+\-]{1,}")
HANGUL_RUN = re.compile(r"[가-힣]{2,}")


def tokens(text: str) -> set[str]:
    """Word tokens + Hangul char n-grams. Korean attaches particles
    (도입할지 vs 도입), so exact word overlap is weak; char bi/tri-grams recover
    the shared stem. IDF later down-weights the common fragments."""
    low = text.lower()
    out = set()
    for t in TOKEN.findall(low):
        if t in STOP or len(t) < 2:
            continue
        out.add(t)
    # Hangul char n-grams (2,3) to bridge particle/inflection mismatch
    for run in HANGUL_RUN.findall(low):
        for n in (2, 3):
            for i in range(len(run) - n + 1):
                out.add(run[i:i + n])
    return out


def load() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    descs: dict[str, set[str]] = {}
    prompts: dict[str, set[str]] = {}
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        name = skill_md.parent.name
        text = skill_md.read_text(encoding="utf-8")
        m = FRONTMATTER.match(text)
        if not m:
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        descs[name] = tokens(str(fm.get("description", "")))
        pf = PROMPTS_DIR / f"{name}.txt"
        if pf.exists():
            prompts[name] = tokens(pf.read_text(encoding="utf-8"))
    return descs, prompts


def idf(descs: dict[str, set[str]]) -> dict[str, float]:
    n = len(descs)
    df: dict[str, int] = {}
    for toks in descs.values():
        for t in toks:
            df[t] = df.get(t, 0) + 1
    return {t: math.log((n + 1) / (c + 0.5)) for t, c in df.items()}


def score(prompt: set[str], desc: set[str], weights: dict[str, float]) -> float:
    return sum(weights.get(t, 0.0) for t in (prompt & desc))


def main() -> int:
    descs, prompts = load()
    if not prompts:
        print("No trigger prompts found.", file=sys.stderr)
        return 0
    weights = idf(descs)

    # Two tiers (heuristic guard, not an LLM judge):
    #   HARD FAIL  → own skill not in top-3, or matches nothing → likely real
    #                collision / broken description → block (exit 1).
    #   WARN       → own skill in top-3 but not the unique #1 → close sibling,
    #                surface for review but do not block (margin can be noise).
    hard = 0
    warn = 0
    for name in sorted(prompts):
        p = prompts[name]
        ranked = sorted(
            ((score(p, descs[s], weights), s) for s in descs),
            key=lambda x: (-x[0], x[1]),
        )
        own = next(i for i, (_, s) in enumerate(ranked) if s == name)
        own_score = ranked[own][0]
        top_score = ranked[0][0]
        runner = ranked[1] if len(ranked) > 1 else (0.0, "-")
        unique_first = ranked[0][1] == name and (len(ranked) < 2 or ranked[1][0] < top_score)
        if unique_first:
            print(f"  ✓ {name}: #1 ({own_score:.1f}) vs {runner[1]}({runner[0]:.1f})")
        elif own <= 2 and own_score > 0:
            warn += 1
            top3 = ", ".join(f"{s}({sc:.1f})" for sc, s in ranked[:3])
            print(f"  ⚠ {name}: #{own + 1} near-sibling (not unique #1) — {top3}")
        else:
            hard += 1
            top3 = ", ".join(f"{s}({sc:.1f})" for sc, s in ranked[:3])
            print(f"  ✗ {name}: own desc ranked #{own + 1} (score {own_score:.1f}) — top: {top3}")

    print()
    print(f"trigger-disambiguation: {len(prompts)} prompts · hard-collisions {hard} · near-siblings(warn) {warn}")
    if hard:
        print(f"✗ {hard} prompt(s) do not even rank their own skill in top-3 — fix description/prompt.")
        return 1
    print("✓ no hard collisions (every prompt ranks its own skill in top-3). near-siblings are advisory.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
