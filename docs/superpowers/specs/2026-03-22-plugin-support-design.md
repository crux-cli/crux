# Crux as a Claude Code Plugin

**Date**: 2026-03-22
**Status**: Draft

## Problem

Crux is a standalone CLI tool installed via `curl | sh` or `uv tool install`. The Claude Code ecosystem is moving toward plugins as the primary distribution mechanism. Users expect to install tools via `claude plugin add`, not by running separate install scripts.

## Goals

1. Package crux as a Claude Code plugin so it can be installed via the standard plugin mechanism
2. Auto-install the crux CLI binary on first session if not already present
3. Keep the plugin version in sync with the CLI version
4. Update documentation to support both installation paths

## Non-Goals

- Crux does not manage plugin scoping. Claude Code handles plugin installation at user and repo levels natively.
- Crux does not add plugin discovery, install, update, or removal commands. Claude Code owns the full plugin lifecycle.
- No changes to crux's core functionality (MCP management, skill management, project sync).

## Design

### Plugin Manifest

Add `.claude-plugin/plugin.json` to the crux repo root:

```json
{
  "name": "crux",
  "displayName": "Crux",
  "description": "Agentic Tool Manager for Claude Code",
  "version": "1.0.2",
  "author": {
    "name": "crux-cli"
  },
  "homepage": "https://github.com/crux-cli/crux",
  "repository": "https://github.com/crux-cli/crux",
  "license": "MIT",
  "keywords": ["mcp", "tools", "skills", "plugins", "project-management"],
  "skills": "./src/crux_cli/data/skills/",
  "hooks": "./hooks/hooks.json"
}
```

Lives in the same repo as crux-cli (`crux-cli/crux`). Version matches `pyproject.toml`.

### Auto-Install Hook

`hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "command -v crux >/dev/null 2>&1 || { echo 'Installing crux-cli...'; curl -LsSf https://raw.githubusercontent.com/crux-cli/crux/main/install.sh | sh; }",
            "async": false
          }
        ]
      }
    ]
  }
}
```

Runs on every session start. If `crux` is already on PATH, it's a no-op (`command -v` returns immediately). If not, it installs via the public install script.

### Plugin Contents

The plugin distributes:

- **Skills**: `src/crux_cli/data/skills/crux/SKILL.md` — the crux command reference skill, giving Claude Code knowledge of all crux commands
- **Hooks**: `hooks/hooks.json` — auto-install hook that ensures the CLI is available

The repo-level skills (`.claude/skills/review-pr/`, `.claude/skills/create-pr/`, etc.) are project-specific and not part of the plugin distribution. They are only available in the crux repo itself.

### Version Sync

Plugin version and CLI version are the same number:

- `pyproject.toml` → `version = "1.0.2"` (CLI / PyPI)
- `.claude-plugin/plugin.json` → `"version": "1.0.2"` (plugin)

The `release-version` skill is updated to bump both files in the same commit. This ensures the plugin marketplace always shows the same version as the latest PyPI release.

### State Independence

Crux's state lives in `~/.crux/`, completely independent of `~/.claude/`. If the Claude Code directory is cleaned up, reset, or reinstalled:

- Crux's registry, config, secrets index, and project tracking are unaffected
- The plugin would need to be reinstalled in Claude Code, but `crux` CLI and all its data remain intact
- `crux init` / `crux doctor` can verify and repair the crux environment independently

### Documentation Updates

- `README.md`: Add "Install as Plugin" section as the primary installation method, with "Install via CLI" as an alternative
- `docs/getting-started/installation.md`: Add plugin installation path with instructions
- `docs/getting-started/quickstart.md`: Update to show plugin-based workflow as the default

### Marketplace Publishing

To make the plugin discoverable via `claude plugin search`, it needs to be listed in a marketplace. Options:

1. Submit to the official Claude plugins marketplace (if open for submissions)
2. Create a `crux-cli/claude-marketplace` repo with a `marketplace.json` pointing to the crux repo

The marketplace entry points to the crux repo. Claude Code clones the repo, reads `.claude-plugin/plugin.json`, and installs the plugin.

## Implementation Order

Each step includes tests for the functionality it introduces.

1. Add `.claude-plugin/plugin.json` to repo root
2. Add `hooks/hooks.json` with auto-install hook
3. Update `release-version` skill to bump both `pyproject.toml` and `.claude-plugin/plugin.json`
4. Update README and installation docs
5. Publish to marketplace (or create marketplace repo)
6. Test end-to-end: install plugin via Claude Code → verify auto-install hook → verify skill availability
