#!/usr/bin/env bash
# Unit tests for guarded-push.sh (script-level guards only, no real git push).
# Run from the repo root: bash tests/test_guarded_push.sh

set -uo pipefail

SCRIPT="scripts/guarded-push.sh"
PASS=0
FAIL=0

check() {
  local desc="$1"; shift
  local expected_exit="$1"; shift
  # Run in a subshell so set -e doesn't kill the test runner
  (set +e; "$@" 2>/dev/null; echo $?) > /tmp/tgh_exit 2>&1
  actual_exit=$(cat /tmp/tgh_exit)
  if [ "$actual_exit" = "$expected_exit" ]; then
    echo "PASS: $desc"
    PASS=$((PASS+1))
  else
    echo "FAIL: $desc (expected exit $expected_exit, got $actual_exit)"
    FAIL=$((FAIL+1))
  fi
}

# ---- Missing arguments ----
check "no args → non-zero" 1 bash "$SCRIPT"
check "only one arg → non-zero" 1 bash "$SCRIPT" "MoveRDC/webplat-425-merge-queue-demo"

# ---- Invalid tag patterns ----
check "tag with spaces → non-zero"     1 bash "$SCRIPT" "MoveRDC/webplat-425-merge-queue-demo" "poc 1"
check "tag with semicolon → non-zero"  1 bash "$SCRIPT" "MoveRDC/webplat-425-merge-queue-demo" "poc-1;"
check "tag letters only → non-zero"    1 bash "$SCRIPT" "MoveRDC/webplat-425-merge-queue-demo" "poc-abc"
check "empty tag → non-zero"           1 bash "$SCRIPT" "MoveRDC/webplat-425-merge-queue-demo" ""
check "numeric only → non-zero"        1 bash "$SCRIPT" "MoveRDC/webplat-425-merge-queue-demo" "123"
check "valid tag poc-2 passes regex"   0 bash -c 'echo "poc-2" | grep -qE "^poc-[0-9]+$"'
check "valid tag poc-99 passes regex"  0 bash -c 'echo "poc-99" | grep -qE "^poc-[0-9]+$"'

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
