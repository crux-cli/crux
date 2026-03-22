---
name: create-pr
description: "Create a PR from the current branch with a structured description optimized for automated review."
args: "[--draft] — optional flag to create as draft PR."
---

# Create PR

Create a pull request from the current branch with a structured description that enables thorough automated review via `/review-pr`.

## Prerequisites

Verify before proceeding:

1. You are on a feature branch (not main)
2. All work is committed (`git status` is clean)
3. Branch is pushed to remote

If any prerequisite fails, fix it before continuing.

## Step 1: Gather Context

```bash
# Current branch and base
BRANCH=$(git branch --show-current)
BASE="main"

# All commits on this branch
git log ${BASE}..HEAD --oneline

# Full diff stats
git diff ${BASE}...HEAD --stat

# Changed files
gh api repos/:owner/:repo/compare/${BASE}...${BRANCH} --jq '.files[].filename'
```

## Step 2: Analyze Changes

Categorize every changed file into:

- **Source code**: `src/` changes — what logic changed and why
- **Tests**: `tests/` changes — what's covered, what test strategy was used
- **Docs**: `docs/`, `README.md`, `CHANGELOG.md` — what documentation was updated
- **Config**: `pyproject.toml`, workflow files, config — what infrastructure changed
- **Skills**: `.claude/skills/` — what skills were added or modified

## Step 3: Build PR Description

Use this exact format. Every section is required. The `/review-pr` skill parses these sections.

```markdown
## Summary

<1-3 sentences: what this PR does and why>

## Changes

### Source
- <file>: <what changed and why>

### Tests
- <file>: <what's tested>

### Docs
- <file>: <what was updated>
(Write "No doc changes" if none — reviewer will check if docs SHOULD have been updated)

### Config
- <file>: <what changed>
(Write "No config changes" if none)

## Breaking Changes

<List any breaking changes to CLI flags, public APIs, or behavior. Write "None" if none.>

## Security Considerations

<List any security-relevant changes: auth, secrets, shell commands, user input handling. Write "None" if none.>

## Test Plan

- [ ] All unit tests pass (`uv run pytest tests/unit/ -v`)
- [ ] All integration tests pass (`uv run pytest tests/integration/ -v`)
- [ ] Ruff clean (`uv run ruff check src/ tests/`)
- [ ] Coverage maintained (>90%)
- [ ] No secrets in committed files
<Add any PR-specific test steps>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Step 4: Push and Create PR

```bash
# Push branch if not already pushed
git push -u origin HEAD

# Create the PR (use --draft if argument was passed)
gh pr create --title "<short title under 70 chars>" --body "<structured body from Step 3>"
```

The title should follow this convention:
- `feat: <description>` — new feature
- `fix: <description>` — bug fix
- `refactor: <description>` — refactoring
- `docs: <description>` — documentation only
- `chore: <description>` — maintenance, deps, config

## Step 5: Verify

```bash
gh pr view --web
```

Confirm the PR was created with the full structured description.

## Notes

- The structured format enables `/review-pr` to efficiently locate what changed, what's tested, and what docs need checking
- Always fill in "Breaking Changes" and "Security Considerations" even if "None" — the reviewer checks these sections exist
- If the PR is large (>500 lines), add a "Review Guide" section suggesting which files to review first
