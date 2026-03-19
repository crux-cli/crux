---
name: release-workflow
description: "Ship a feature branch: PR → CI → merge → release → docs. Invoke with: /release-workflow <version>"
args: "<version> — the release version number (e.g., 1.0.2). Required."
---

# Release Workflow

Ship a feature branch to production: PR → CI → merge → tag → PyPI → docs.

**Version argument:** The version number is passed as the first argument (e.g., `/release-workflow 1.0.2`). All steps below use this version.

## Prerequisites

Before running this workflow, verify:
1. You are on a feature branch (not main)
2. All work is committed (`git status` is clean)
3. All tests pass locally: `PYTHONPATH=src pytest tests/`
4. The version number follows semver and is greater than the current version in `pyproject.toml`

## Step 1: Bump Version

Update `pyproject.toml` with the release version:

```python
# In pyproject.toml, change:
version = "<VERSION>"
```

Commit:
```bash
git add pyproject.toml
git commit -m "chore: bump version to <VERSION>"
```

## Step 2: Push Branch & Create PR

```bash
git push -u origin HEAD
gh pr create --title "<PR title from branch context>" --body "$(cat <<'EOF'
## Summary
<summarize changes from git log>

## Test plan
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Lint passes (ruff check + format)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## Step 3: Wait for CI

```bash
gh pr checks --watch
```

All checks must pass. If any fail:
1. Read the failure logs: `gh run view <run-id> --log-failed`
2. Fix the issue on the feature branch
3. Push and re-check

## Step 4: Merge PR

```bash
gh pr merge --squash --delete-branch
```

## Step 5: Tag Release

```bash
git checkout main
git pull
git tag v<VERSION>
git push origin v<VERSION>
```

This triggers `.github/workflows/release.yml` which:
- Runs full CI gate (validate, lint, security, unit tests, integration tests)
- Builds sdist + wheel
- Publishes to PyPI via trusted publisher
- Creates GitHub Release with auto-generated changelog

## Step 6: Verify Release Pipeline

```bash
gh run list --workflow=release.yml --limit=1
gh run watch
```

Wait for completion. If it fails:
- CI gate failure: check test output
- Build failure: check `uv build` / `twine check` output
- PyPI publish failure: check trusted publisher config in repo settings

## Step 7: Verify Docs Deployment

The docs pipeline auto-triggers on push to main. Verify:

```bash
gh run list --workflow=docs.yml --limit=1
gh run watch
```

If it didn't auto-trigger:
```bash
gh workflow run docs.yml
```

## Step 8: Final Verification

```bash
# PyPI package
pip index versions crux-cli

# GitHub release page
gh release view v<VERSION>

# Docs site
open https://crux-cli.github.io/crux/
```

## Rollback

If something goes wrong after tagging but before PyPI publish:
```bash
git tag -d v<VERSION>
git push origin :refs/tags/v<VERSION>
```

If already published to PyPI, you cannot delete the version. Instead:
```bash
# Revert the merge on main
git revert <merge-commit-sha>
git push

# Publish a patch version with the fix
```

## Notes

- The release pipeline requires a PyPI trusted publisher configured in GitHub repo settings
- The docs pipeline uses `mike` for versioned documentation
- Squash merge keeps main history clean — one commit per feature
- Always verify locally before creating the PR
