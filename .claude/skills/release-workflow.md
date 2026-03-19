---
name: release-workflow
description: Create PR, merge after CI, tag release, deploy docs. Use when completing a feature branch and releasing a new version.
---

# Release Workflow

Steps to ship a feature branch: PR → merge → release → docs deploy.

## Prerequisites

- On a feature branch with all work committed
- All tests passing locally (`PYTHONPATH=src pytest tests/`)
- Target version number known (e.g., `1.0.1`)

## Steps

### 1. Create Pull Request

```bash
# Push branch and create PR
git push -u origin HEAD
gh pr create --title "<short title>" --body "$(cat <<'EOF'
## Summary
<bullet points>

## Test plan
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Lint passes (ruff check + format)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 2. Wait for CI

```bash
# Watch CI status (polls every 30s)
gh pr checks --watch

# Or check manually
gh pr checks
```

### 3. Merge PR

```bash
# Squash merge to keep history clean
gh pr merge --squash --delete-branch
```

### 4. Tag Release

```bash
# Pull merged main
git checkout main
git pull

# Tag with version
git tag v<VERSION>
git push origin v<VERSION>
```

This triggers `.github/workflows/release.yml` which:
- Runs CI gate
- Builds sdist + wheel
- Publishes to PyPI (trusted publisher)
- Creates GitHub Release with auto-changelog

### 5. Verify Release Pipeline

```bash
# Watch release workflow
gh run list --workflow=release.yml --limit=1
gh run watch  # watches most recent run
```

### 6. Deploy Docs

The docs pipeline triggers automatically on:
- Push to main (paths: docs/**, mkdocs.yml, src/crux_cli/**)
- Release published

If it doesn't auto-trigger:
```bash
gh workflow run docs.yml
```

Verify:
```bash
gh run list --workflow=docs.yml --limit=1
gh run watch
```

### 7. Verify Everything

```bash
# Check PyPI
pip index versions crux-cli

# Check docs site
open https://crux-cli.github.io/crux/

# Check GitHub release
gh release view v<VERSION>
```

## Bump Version

Before tagging, update the version in `pyproject.toml`:

```bash
# Edit pyproject.toml: version = "<VERSION>"
# Commit and push to main before tagging
```

## Rollback

If something goes wrong:
```bash
# Delete tag (if not yet published to PyPI)
git tag -d v<VERSION>
git push origin :refs/tags/v<VERSION>

# Revert merge commit on main
git revert <merge-commit-sha>
git push
```
