#!/usr/bin/env bash
# Run one skill triggering test.
#
# Verifies that a natural-language user prompt causes Claude Code to
# auto-trigger the named skill (via its frontmatter description match).
#
# Usage:
#   ./run-test.sh <skill-name> <prompt-file> [retries]
#
# Example:
#   ./run-test.sh author-skill ./prompts/author-skill.txt 3
#
# Exit codes:
#   0  skill triggered on at least one attempt
#   1  skill did not trigger after all attempts
#   2  bad arguments / missing files
#
# Requires: claude CLI in PATH.

set -u

SKILL="${1:-}"
PROMPT_FILE="${2:-}"
RETRIES="${3:-3}"

if [[ -z "$SKILL" || -z "$PROMPT_FILE" ]]; then
  echo "Usage: $0 <skill-name> <prompt-file> [retries]" >&2
  exit 2
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Prompt file not found: $PROMPT_FILE" >&2
  exit 2
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "claude CLI not found in PATH" >&2
  exit 2
fi

PROMPT=$(cat "$PROMPT_FILE")

# Loose-match detector: skill name in output (mention or invocation marker).
# Tighten this later by parsing transcript JSON or tool-use blocks.
detect_trigger() {
  local output="$1"
  echo "$output" | grep -qE "(/${SKILL}\\b|${SKILL}\\.SKILL|Skill[(\"][[:space:]]*${SKILL}|\\.claude/skills/${SKILL}/)"
}

for attempt in $(seq 1 "$RETRIES"); do
  echo "[$SKILL] attempt $attempt/$RETRIES"
  set +e
  OUTPUT=$(claude -p "$PROMPT" 2>&1)
  set -e
  if detect_trigger "$OUTPUT"; then
    echo "[$SKILL] PASS on attempt $attempt"
    exit 0
  fi
  # Brief pause to avoid rate-limit thrash
  sleep 2
done

echo "[$SKILL] FAIL: skill not triggered after $RETRIES attempts"
echo "---- last output (truncated to 40 lines) ----"
echo "$OUTPUT" | head -40
exit 1
