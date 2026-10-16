#!/usr/bin/env bash
# Guarded push with bounded retry for non-fast-forward races.
#
# Usage:
#   guarded-push.sh <expected_repo> <new_tag>
#
# Environment:
#   GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL
#   must be set before calling (typically by the workflow).
#
# Exits 0 on success.
# Exits non-zero on guard failure or exhausted retries.
#
# Guards:
#   - Verifies current remote matches expected_repo (origin URL check)
#   - Verifies we are on main
#   - Validates new_tag format
#   - Validates only mq-poc/values.yaml changed after update
#   - Validates only rollout.containers[0].image.tag changed
#   - Never force-pushes

set -euo pipefail

EXPECTED_REPO="${1:-}"
NEW_TAG="${2:-}"
MAX_RETRIES=5
VALUES_FILE="mq-poc/values.yaml"

die() { echo "GUARD FAIL: $1" >&2; exit 1; }

# --- Input validation (no eval, no interpolation into shell source) ---
[ -n "$EXPECTED_REPO" ] || die "expected_repo argument is required"
[ -n "$NEW_TAG" ] || die "new_tag argument is required"

echo "$NEW_TAG" | grep -qE '^poc-[0-9]+$' \
  || die "new_tag '$NEW_TAG' does not match ^poc-[0-9]+$"

# --- Repository identity check ---
ACTUAL_REMOTE=$(git remote get-url origin 2>/dev/null || true)
# Normalize: strip .git suffix and https://github.com/ prefix for comparison
normalize() { echo "$1" | sed 's|\.git$||' | sed 's|https://github.com/||' | sed 's|git@github.com:||'; }
EXPECTED_NORM=$(normalize "$EXPECTED_REPO")
ACTUAL_NORM=$(normalize "$ACTUAL_REMOTE")
[ "$EXPECTED_NORM" = "$ACTUAL_NORM" ] \
  || die "Remote mismatch: expected '$EXPECTED_NORM', got '$ACTUAL_NORM'"

# --- Branch check ---
CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || true)
[ "$CURRENT_BRANCH" = "main" ] \
  || die "Not on main branch (got '$CURRENT_BRANCH')"

attempt=0
while [ $attempt -lt $MAX_RETRIES ]; do
  attempt=$((attempt + 1))
  echo "Attempt $attempt of $MAX_RETRIES ..."

  # Refresh from remote, rebase our working tree
  git fetch origin main
  git rebase origin/main

  # Check working tree is clean before our update
  if ! git diff --quiet || ! git diff --cached --quiet; then
    die "Dirty working tree before update — aborting"
  fi

  # Apply the values update
  python3 scripts/update-values.py "$VALUES_FILE" "$NEW_TAG"

  # Verify exactly one file changed
  CHANGED_FILES=$(git diff --name-only)
  CHANGED_COUNT=$(echo "$CHANGED_FILES" | grep -c . || true)
  [ "$CHANGED_COUNT" -eq 1 ] \
    || die "Expected 1 changed file, got $CHANGED_COUNT: $CHANGED_FILES"
  [ "$CHANGED_FILES" = "$VALUES_FILE" ] \
    || die "Changed file is '$CHANGED_FILES', expected '$VALUES_FILE'"

  # Verify the diff touches only the tag line
  TAG_LINE_CHANGES=$(git diff -- "$VALUES_FILE" | grep '^[+-]' | grep -v '^[+-][+-][+-]' | grep -v 'tag:')
  [ -z "$TAG_LINE_CHANGES" ] \
    || die "Diff contains changes outside 'tag:' line: $TAG_LINE_CHANGES"

  git add "$VALUES_FILE"
  git commit -m "chore(poc): update image tag to $NEW_TAG [bot]"

  # Attempt push (no force)
  if git push origin main; then
    echo "Push succeeded on attempt $attempt"
    exit 0
  else
    PUSH_EXIT=$?
    echo "Push failed (exit $PUSH_EXIT), may be non-fast-forward — will retry"
    # Undo the commit so we can rebase cleanly
    git reset --soft HEAD~1
    git checkout -- "$VALUES_FILE"
    sleep 5
  fi
done

die "Push failed after $MAX_RETRIES attempts"
