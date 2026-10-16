# webplat-425-merge-queue-demo

**Purpose**: Disposable private repository to validate whether a dedicated GitHub App can push directly to a protected branch while ordinary PRs use GitHub's merge queue.

This is a GitHub-only functionality experiment — no ArgoCD, Kubernetes, AWS, CircleCI, or real Helm execution.

## What this tests

1. Application and dependency PRs require checks + merge queue.
2. A dedicated test GitHub App can bypass those requirements for direct dummy tag updates.
3. A bot push during queue validation does not lose either change.
4. A failed queue check still blocks the affected PR even with a concurrent bot success.

## Structure

```
.github/workflows/poc-check.yml       # Required check for PRs and merge queue
.github/workflows/poc-bot-write.yml   # Manual bot push (workflow_dispatch only)
mq-poc/application.txt                # Fixture: app-style change target
mq-poc/dependencies.json              # Fixture: dependency-style change target
mq-poc/values.yaml                    # Fixture: bot writer target (image tag only)
scripts/                              # Writer guard and orchestration scripts
config/                               # Proposed branch ruleset JSON
tests/                                # Local unit tests for scripts
evidence/                             # Sanitized test results
```

## Evidence

See `evidence/results.md` after live testing is complete.

## Scope limits

- This repo only. No production repos touched.
- No external CI, no deployments, no Kubernetes.
- Bot writes go only to `mq-poc/values.yaml` → `rollout.containers[0].image.tag`.
