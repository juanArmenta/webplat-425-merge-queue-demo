# POC Results — webplat-425-merge-queue-demo

**Status**: Pre-creation — no GitHub activity yet.

---

## Repository

| Field | Value |
|---|---|
| Proposed owner | MoveRDC |
| Proposed name | webplat-425-merge-queue-demo |
| Repository ID | _pending creation_ |
| Visibility | private |
| Effective rules | _pending verification post-creation_ |
| Bypass identities | _pending Approval B_ |

---

## Test cases

| Case | Status | Notes |
|---|---|---|
| Baseline application PR | not run | |
| Non-bypass direct push | not run | |
| Bot push during validation | not run | |
| Dependency-style PR | not run | |
| Failed queue check | not run | |
| Finite burst (3 tags) | not run | |
| Dummy rollback | not run | |
| Writer guard | not run | |

---

## Workflow versions

| Workflow | File | Last commit SHA |
|---|---|---|
| poc-check | .github/workflows/poc-check.yml | _pending_ |
| poc-bot-write | .github/workflows/poc-bot-write.yml | _pending_ |

---

## Unverified items

- GitHub Actions SHA pinning for `actions/create-github-app-token@v1` — must be resolved before Approval B
- Org-level workflow policy — whether external Actions are allowed in MoveRDC
- Whether any org-level rulesets layer on top of repo rulesets
- GITHUB_TOKEN scope available on workflow runs (expected: default read-only for this repo)

---

_Updated as phases complete._
