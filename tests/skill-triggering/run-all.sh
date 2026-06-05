#!/usr/bin/env bash
# Iterate every prompt in prompts/ and run the trigger test.
#
# Usage:
#   ./run-all.sh             # default 3 retries
#   RETRIES=5 ./run-all.sh   # override retries
#
# Each prompts/<skill-name>.txt expects a matching skills/<skill-name>/.
# Skills without a prompt file are skipped (with WARN).
#
# Exit code: 0 if all passed, 1 if any failed.
#
# WARNING: This invokes the live claude CLI per attempt — costs real tokens.
# Run manually (e.g., before release) rather than on every PR.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPTS_DIR="$SCRIPT_DIR/prompts"
RETRIES="${RETRIES:-3}"

if [[ ! -d "$PROMPTS_DIR" ]]; then
  echo "Prompts dir not found: $PROMPTS_DIR" >&2
  exit 2
fi

shopt -s nullglob
prompts=("$PROMPTS_DIR"/*.txt)
shopt -u nullglob

if [[ ${#prompts[@]} -eq 0 ]]; then
  echo "No prompts found in $PROMPTS_DIR/" >&2
  exit 0
fi

PASSED=0
FAILED=0
RESULTS=()

for prompt_file in "${prompts[@]}"; do
  skill=$(basename "$prompt_file" .txt)
  echo ""
  echo "============================================================"
  echo "Testing: $skill"
  echo "============================================================"
  if "$SCRIPT_DIR/run-test.sh" "$skill" "$prompt_file" "$RETRIES"; then
    PASSED=$((PASSED + 1))
    RESULTS+=("PASS  $skill")
  else
    FAILED=$((FAILED + 1))
    RESULTS+=("FAIL  $skill")
  fi
done

echo ""
echo "============================================================"
echo "Summary"
echo "============================================================"
printf '%s\n' "${RESULTS[@]}"
echo ""
echo "Total: $((PASSED + FAILED))   Passed: $PASSED   Failed: $FAILED"

[[ $FAILED -eq 0 ]] || exit 1
