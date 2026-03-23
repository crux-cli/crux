---
name: address-issues
description: "Iterate all open GitHub issues: triage, reproduce, fix with tests, create PR, review. Fully automated issue resolution."
args: ""
---

# Address Issues

Iterate all open GitHub issues on the current repo. For each issue: triage, gather context, reproduce, implement a fix with tests, create a PR via `/create-pr`, and review via `/review-pr`.

## Step 0: Fetch All Open Issues

```bash
gh issue list --state open --json number,title,body,labels --limit 100
```

Process each issue sequentially through Steps 1–7. Return to main branch before starting each issue.

```bash
git checkout main && git pull
```

## Step 1: Triage

Read the issue title, body, and labels. Classify into one of:

| Category | Description | Branch prefix |
|----------|-------------|---------------|
| **bug** | Something is broken or behaving incorrectly | `fix/` |
| **feature** | New functionality or enhancement | `feat/` |
| **docs** | Documentation improvement or correction | `docs/` |
| **chore** | Maintenance, deps, config, refactoring | `chore/` |
| **skip** | Too large, ambiguous, needs human decision, or requires external access | — |

### If skip:

Post a comment explaining why, then move to the next issue:

```bash
gh issue comment <NUMBER> --body "This issue requires human attention — <reason>. Skipping automated resolution."
```

## Step 2: Gather Context

Read the issue thoroughly. Identify:

- **Affected files**: which source files, tests, or docs are relevant
- **Repro steps**: how to trigger the issue (from the issue body or inferred)
- **Related code**: read the relevant source files to understand current behavior
- **Linked issues/PRs**: check for related context

```bash
gh issue view <NUMBER> --json title,body,labels,comments
```

Read all affected source files to understand the code before making changes.

## Step 3: Reproduce

Verify the issue is real before attempting a fix.

**For bugs:**
- Follow the repro steps from the issue
- Run existing tests that cover the affected code
- Write a minimal failing test if no repro steps are provided

```bash
# Run relevant tests
uv run pytest tests/ -k "<relevant_test_pattern>" -v
```

**For features/docs/chore:**
- Verify the current state (missing feature, outdated docs, etc.)
- Establish a baseline of current behavior

### If reproduction fails:

Post a comment and move to the next issue:

```bash
gh issue comment <NUMBER> --body "Attempted to reproduce this issue but was unable to.

**What was tried:**
- <list steps attempted>

Please provide additional reproduction steps if possible."
```

## Step 4: Create Branch and Implement Fix

Create a branch based on the triage category:

```bash
git checkout -b <prefix>/issue-<NUMBER>
# Examples: fix/issue-42, feat/issue-15, docs/issue-7
```

### Implementation guidelines:

- **Bug fixes**: fix the root cause, not just the symptom
- **Features**: implement the minimum viable version described in the issue
- **Docs**: update the relevant documentation files
- **Chore**: make the maintenance change described

### Tests:

Every fix MUST include tests:

- **Bug fix**: add a test that fails without the fix and passes with it
- **Feature**: add tests covering the new functionality and edge cases
- **Docs**: verify any code examples in docs are accurate
- **Chore**: update existing tests if behavior changed

Verify all tests pass:

```bash
uv run pytest tests/ -v
uv run ruff check src/ tests/
```

## Step 5: Commit and Push

```bash
git add <changed-files>
git commit -m "<prefix>: <concise description> (closes #<NUMBER>)"
git push -u origin HEAD
```

The commit message prefix should match the branch prefix (`fix:`, `feat:`, `docs:`, `chore:`).

## Step 6: Create PR

Invoke the `/create-pr` skill. Ensure the PR body includes `Closes #<NUMBER>` to auto-close the issue on merge.

## Step 7: Review PR

Invoke the `/review-pr` skill on the newly created PR.

### Review retry loop:

1. **Approved or warnings-only** → done. Move to the next issue.
2. **Critical findings** → read the review comments, fix the issues on the same branch:

```bash
# Fix the issues identified in review
# ... make changes ...
git add <files>
git commit -m "fix: address review feedback for #<NUMBER>"
git push
```

Then re-invoke `/review-pr`. Maximum **2 retry attempts**. After that, leave the PR as-is for human review.

## Step 8: Next Issue

Return to main and proceed to the next issue:

```bash
git checkout main && git pull
```

Repeat from Step 1 for the next issue.

## Summary Output

After processing all issues, output a summary table:

```markdown
| Issue | Title | Action | Result |
|-------|-------|--------|--------|
| #42 | Broken sync | fix | PR #51 created, approved |
| #15 | Add search | skip | Too large for automated fix |
| #7 | Typo in docs | docs | PR #52 created, approved |
| #3 | Crash on empty | fix | PR #53 created, review pending |
```

## Notes

- This skill requires `gh` CLI authenticated with repo access
- Each issue gets its own branch and PR — no combining issues
- Always return to main between issues to avoid cross-contamination
- The skill invokes `/create-pr` and `/review-pr` — those skills handle the details of PR formatting and review process
