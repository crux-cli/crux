---
name: release-version
description: "Bump version on main, tag, run release pipeline, then deploy docs. Auto-increments patch if no version given."
args: "[version] — optional version number (e.g., 1.0.2). If omitted, increments the patch version by 1."
---

# Release Version

Bump the version in `pyproject.toml` and `.claude-plugin/plugin.json` on main, tag the release, run the release pipeline, and deploy docs.

## Step 0: Resolve Version

If a version argument was provided, use it. Otherwise, auto-increment:

```bash
# Read current version from pyproject.toml
CURRENT=$(grep -m1 '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "Current version: $CURRENT"
```

If no version argument:
- Parse `CURRENT` as `MAJOR.MINOR.PATCH`
- Increment `PATCH` by 1
- Set `VERSION` to `MAJOR.MINOR.(PATCH+1)`

Example: `1.0.1` → `1.0.2`

Verify `VERSION` is greater than `CURRENT`. If not, abort.

## Step 1: Ensure Clean Main

```bash
git checkout main
git pull origin main
git status
```

Working tree must be clean. If not, abort with a message.

## Step 2: Bump Version

Update `pyproject.toml`:

```python
version = "<VERSION>"
```

Update `.claude-plugin/plugin.json`:

```json
"version": "<VERSION>"
```

Both files must have the same version string.

Commit and push directly to main:

```bash
git add pyproject.toml .claude-plugin/plugin.json
git commit -m "chore: bump version to <VERSION>"
git push origin main
```

## Step 3: Tag and Push

```bash
git tag v<VERSION>
git push origin v<VERSION>
```

This triggers `.github/workflows/release.yml` which:
- Runs full CI gate
- Builds sdist + wheel
- Publishes to PyPI
- Creates GitHub Release

## Step 4: Wait for Release Pipeline

```bash
# Find the run triggered by the tag
gh run list --workflow=release.yml --limit=1
gh run watch
```

If the release pipeline fails:
1. Read failure logs: `gh run view <run-id> --log-failed`
2. Report the failure and stop. Do NOT proceed to docs.

## Step 5: Deploy Docs

The docs pipeline does not auto-trigger from GitHub Actions releases. Dispatch manually:

```bash
gh workflow run docs.yml -f version=<VERSION>
```

Wait for docs deployment:

```bash
gh run list --workflow=docs.yml --limit=1
gh run watch
```

## Step 6: Verify

```bash
# PyPI
pip index versions crux-cli

# GitHub Release
gh release view v<VERSION>

# Docs
echo "Docs: https://crux-cli.github.io/crux/"
```

Report the version, PyPI status, and docs URL.

## Rollback

If tagged but release pipeline failed:

```bash
git tag -d v<VERSION>
git push origin :refs/tags/v<VERSION>
```

If already published to PyPI, publish a patch fix instead — PyPI versions cannot be deleted.

## Notes

- This skill operates directly on main — no branch or PR involved
- The release pipeline requires a PyPI trusted publisher configured in GitHub repo settings
- The docs pipeline uses `mike` for versioned documentation
- Always verify the release pipeline succeeds before deploying docs
