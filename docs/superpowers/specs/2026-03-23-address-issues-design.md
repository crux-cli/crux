# Address Issues Skill — Design Spec

**Date:** 2026-03-23
**Status:** Approved

## Summary

A skill that iterates all open GitHub issues on the current repo, triages each one, and for addressable issues: reproduces the problem, implements a fix with tests on a dedicated branch, creates a PR via `/create-pr`, and reviews it via `/review-pr` with up to 2 fix-retry cycles.

## Flow

```
For each open issue:
  1. Triage → bug / feature / docs / chore / skip
  2. If skip → comment on issue with reason, move to next
  3. Gather context (issue body, linked files, related code)
  4. Reproduce (run tests, follow repro steps from issue)
  5. If repro fails → comment on issue, move to next
  6. Create branch: <category>/issue-<number>
  7. Implement fix + add/update tests
  8. Commit, push, invoke /create-pr
  9. Invoke /review-pr
  10. If critical findings → fix and re-review (max 2 retries)
  11. Move to next issue
```

## Branch Naming

Based on triage category:

| Category | Branch prefix | Example |
|----------|--------------|---------|
| Bug | `fix/` | `fix/issue-42` |
| Feature | `feat/` | `feat/issue-42` |
| Docs | `docs/` | `docs/issue-42` |
| Chore | `chore/` | `chore/issue-42` |

## Triage Criteria

Each issue is categorized by reading the title, body, and labels. Issues that meet any of the following are marked **skip**:

- Too large or ambiguous to address in a single PR
- Requires external service access or infrastructure changes
- Requires human design decisions (e.g., UX, architecture)
- Duplicate of another issue already being addressed

Skipped issues receive a comment: *"This issue requires human attention — [reason]. Skipping automated resolution."*

## Reproduction

For bugs: attempt to reproduce using steps from the issue body, running existing tests, or writing a minimal repro script. For features/docs/chore: verify current behavior to establish a baseline.

If reproduction fails, comment on the issue: *"Attempted to reproduce this issue but was unable to. [details of what was tried]. Please provide additional reproduction steps if possible."* Then move to the next issue.

## Review Retry Loop

After `/review-pr` runs:

1. If approved or warnings-only → done, move to next issue
2. If critical findings → read review comments, attempt fixes on the same branch, push, re-invoke `/review-pr`
3. Maximum 2 retry attempts — after that, leave the PR as-is for human review

## PR Linking

Every PR body includes `Closes #<issue-number>` so merging auto-closes the issue.

## Dependencies

- `gh` CLI authenticated with repo access
- `/create-pr` skill
- `/review-pr` skill
