#!/usr/bin/env bash
# Pre-PR validation runner for quivo.
#
# Runs all checks required before merging a new or modified skill:
#   1. lint-skills.py — frontmatter + body sections
#   2. skill.yaml present + version matches SKILL.md frontmatter
#   3. manifest.json entry present + sha256 matches release-bundled skill files
#   4. tests/skill-triggering/prompts/<name>.txt present
#   5. quivo init dry-run — Claude + Codex output generation
#
# Usage:
#   scripts/test-skill.sh                 # check ALL skills
#   scripts/test-skill.sh <skill-name>    # check one skill
#
# Exit code: 0 if all pass, 1 if any fail.

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SKILL_FILTER="${1:-}"

if [[ -n "$SKILL_FILTER" && ! -d "skills/$SKILL_FILTER" ]]; then
  echo "ERROR: skills/$SKILL_FILTER not found" >&2
  exit 2
fi

FAIL=0
WARN=0

say_ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
say_fail() { printf '  \033[31m✗\033[0m %s\n' "$1"; FAIL=$((FAIL+1)); }
say_warn() { printf '  \033[33m!\033[0m %s\n' "$1"; WARN=$((WARN+1)); }

# ---- 1. lint-skills.py ----
echo "[1/5] lint-skills.py"
if ! command -v python3 >/dev/null 2>&1; then
  say_fail "python3 not in PATH"
else
  LINT_TARGET=""
  if [[ -n "$SKILL_FILTER" ]]; then
    # lint-skills.py takes a dir; we make a tmp dir with just the target
    # to limit output. Simpler: run on all and grep.
    LINT_OUT=$(python3 scripts/lint-skills.py 2>&1)
    if echo "$LINT_OUT" | grep -qE "^FAIL .*skills/${SKILL_FILTER}/"; then
      echo "$LINT_OUT" | grep -A20 "^FAIL .*skills/${SKILL_FILTER}/" | sed 's/^/    /'
      say_fail "lint failed for $SKILL_FILTER"
    else
      say_ok "lint passed for $SKILL_FILTER"
    fi
  else
    if python3 scripts/lint-skills.py | tee /tmp/lint.out | grep -q "^Summary: .*0 failed"; then
      say_ok "lint passed (all skills)"
    else
      say_fail "lint failed — see output above"
      grep "^FAIL" /tmp/lint.out | sed 's/^/    /' || true
    fi
  fi
fi

# ---- helpers ----
list_skills() {
  if [[ -n "$SKILL_FILTER" ]]; then
    echo "$SKILL_FILTER"
  else
    # Only subdirectories under skills/ are considered skills.
    # Files like skills/VERSION are siblings to skill dirs and are skipped.
    find skills -mindepth 1 -maxdepth 1 -type d -not -name '.*' \
      -exec basename {} \; | sort
  fi
}

frontmatter_field() {
  # Extract a top-level scalar field from SKILL.md frontmatter.
  local file="$1" field="$2"
  python3 -c "
import sys, yaml, re
text = open(sys.argv[1], encoding='utf-8').read()
m = re.match(r'\A---\s*\n(.*?)^---\s*\n', text, re.DOTALL | re.MULTILINE)
if not m:
    sys.exit(1)
data = yaml.safe_load(m.group(1))
v = data.get(sys.argv[2])
if v is None:
    sys.exit(2)
print(v if isinstance(v, (str, int, float)) else repr(v))
" "$file" "$field" 2>/dev/null
}

# ---- 2. skill.yaml present + version match ----
echo ""
echo "[2/5] skill.yaml consistency"
for s in $(list_skills); do
  if [[ ! -f "skills/$s/skill.yaml" ]]; then
    say_fail "skills/$s/skill.yaml missing"
    continue
  fi
  YAML_VER=$(python3 -c "import yaml; print(yaml.safe_load(open('skills/$s/skill.yaml')).get('version',''))" 2>/dev/null)
  MD_VER=$(frontmatter_field "skills/$s/SKILL.md" version)
  if [[ -z "$YAML_VER" || -z "$MD_VER" ]]; then
    say_fail "skills/$s: version missing in skill.yaml or SKILL.md"
  elif [[ "$YAML_VER" != "$MD_VER" ]]; then
    say_fail "skills/$s: version mismatch — skill.yaml=$YAML_VER  SKILL.md=$MD_VER"
  else
    say_ok "skills/$s version $YAML_VER"
  fi
done

# ---- 3. manifest.json entry + sha256 ----
echo ""
echo "[3/5] manifest.json sha256"
if [[ ! -f manifest.json ]]; then
  say_fail "manifest.json missing"
else
  for s in $(list_skills); do
    EXPECTED=$(python3 -c "
import hashlib, sys
from pathlib import Path
combined = b''
for fname in sorted(['skill.yaml', 'SKILL.md', 'setup.sh', 'setup.ps1']):
    fpath = Path('skills/$s') / fname
    if fpath.exists():
        combined += fpath.read_bytes()
h = hashlib.sha256(combined).hexdigest()
print(h)
" 2>/dev/null)
    ACTUAL=$(python3 -c "
import json, sys
m = json.load(open('manifest.json'))
for sk in m['skills']:
    if sk['name'] == '$s':
        print(sk.get('sha256',''))
        sys.exit(0)
" 2>/dev/null)
    if [[ -z "$ACTUAL" ]]; then
      say_fail "manifest.json: $s not registered"
    elif [[ "$ACTUAL" != "$EXPECTED" ]]; then
      say_fail "manifest.json: $s sha256 stale (expected ${EXPECTED:0:12}…, got ${ACTUAL:0:12}…)"
    else
      say_ok "skills/$s manifest sha256 ${ACTUAL:0:12}…"
    fi
  done
fi

# ---- 4. trigger prompt exists ----
echo ""
echo "[4/5] skill-triggering prompts + disambiguation"
for s in $(list_skills); do
  if [[ -f "tests/skill-triggering/prompts/$s.txt" ]]; then
    BYTES=$(wc -c < "tests/skill-triggering/prompts/$s.txt")
    if [[ "$BYTES" -lt 20 ]]; then
      say_warn "skills/$s prompt very short ($BYTES bytes)"
    else
      say_ok "tests/skill-triggering/prompts/$s.txt"
    fi
  else
    say_fail "tests/skill-triggering/prompts/$s.txt missing"
  fi
done

# disambiguation: prompt must rank its OWN skill (catches collisions, not just file presence)
if command -v python3 >/dev/null 2>&1 && [[ -f scripts/check-trigger-disambiguation.py ]]; then
  DIS_OUT=$(python3 scripts/check-trigger-disambiguation.py 2>&1); DIS_RC=$?
  DIS_SUM=$(echo "$DIS_OUT" | grep -E "^trigger-disambiguation:")
  if [[ "$DIS_RC" -ne 0 ]]; then
    echo "$DIS_OUT" | grep -E "^  ✗" | sed 's/^/    /'
    say_fail "trigger disambiguation hard collision — $DIS_SUM"
  elif [[ -n "$SKILL_FILTER" ]]; then
    OWN=$(echo "$DIS_OUT" | grep -E "^  [✓⚠] ${SKILL_FILTER}:")
    [[ -n "$OWN" ]] && echo "   ${OWN}"
    if echo "$OWN" | grep -q "⚠"; then
      say_warn "trigger disambiguation: ${SKILL_FILTER} is a near-sibling (advisory, not blocking)"
    else
      say_ok "trigger disambiguation: ${SKILL_FILTER} ranks its own skill #1"
    fi
  else
    say_ok "trigger disambiguation ($DIS_SUM)"
  fi
fi

# ---- 5. quivo init dry-run (smoke test) ----
echo ""
echo "[5/5] quivo init dry-run"
if ! command -v uv >/dev/null 2>&1; then
  say_warn "uv not in PATH — skipping quivo init smoke test"
else
  TMPDIR_OUT=$(mktemp -d)
  set +e
  uv run --no-project --with typer --with rich --with pyyaml --with httpx --with packaging \
    python -c "
import sys, os, json
sys.path.insert(0, 'src')
os.environ['QUIVO_LOCAL_SKILLS'] = os.getcwd()
from pathlib import Path
from quivo.cli import app
from typer.testing import CliRunner
runner = CliRunner()
result = runner.invoke(app, ['init', '--agent', 'both', '--dir', '$TMPDIR_OUT', '--force'])
if result.exit_code != 0:
    sys.exit(1)
claude_policy = Path('$TMPDIR_OUT/.claude/skills/req-intake/SKILL.md').read_text(encoding='utf-8')
codex_policy = Path('$TMPDIR_OUT/.codex/prompts/req-intake.md').read_text(encoding='utf-8')
codex_contract = Path('$TMPDIR_OUT/.codex/scripts/req-intake/SKILL.md').read_text(encoding='utf-8')
ok = (
    '## Company Policy (from .quivo/policy.md)' in claude_policy
    and '## Company Policy (from .quivo/policy.md)' in codex_policy
    and codex_contract.startswith('---')
    and 'outputs:' in codex_contract
    and '## Company Policy (from .quivo/policy.md)' in codex_contract
)
sys.exit(0 if ok else 1)
" >/dev/null 2>&1
  STATUS=$?
  set -e
  if [[ "$STATUS" -eq 0 ]]; then
    CLAUDE_COUNT=$(ls "$TMPDIR_OUT/.claude/skills/" 2>/dev/null | wc -l | tr -d ' ')
    CODEX_COUNT=$(ls "$TMPDIR_OUT/.codex/prompts/" 2>/dev/null | wc -l | tr -d ' ')
    say_ok "quivo init: claude=$CLAUDE_COUNT  codex=$CODEX_COUNT"
  else
    say_fail "quivo init dry-run failed"
  fi
  rm -rf "$TMPDIR_OUT"
fi

# ---- Summary ----
echo ""
echo "============================================================"
if [[ "$FAIL" -eq 0 ]]; then
  echo "✓ All checks passed (warnings: $WARN)"
  exit 0
else
  echo "✗ $FAIL check(s) failed (warnings: $WARN)"
  exit 1
fi
