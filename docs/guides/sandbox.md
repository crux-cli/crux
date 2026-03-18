# Sandboxed Execution

Run agents in isolated environments with exactly the MCPs they need — nothing more.

## Ad-hoc Runs

```bash
crux run "Find papers on MCP security and update the wiki" \
  --mcps wikijs filesystem
```

This:

1. Runs pre-flight checks (MCPs exist, secrets stored, sources built)
2. Creates an isolated sandbox at `~/.crux/sandbox/<run-id>/`
3. Generates a scoped `.mcp.json` with only the declared MCPs
4. Launches the agent with that config
5. Cleans up on completion

## Run Manifests

Save reusable run configurations as JSON files:

```json title="tasks/weekly-research.json"
{
  "name": "weekly-research",
  "task": "Search for latest MCP security papers, summarize, update wiki",
  "mcps": ["wikijs", "filesystem"],
  "skills": ["autoresearch"],
  "timeout_minutes": 30
}
```

Execute:

```bash
crux run --file tasks/weekly-research.json
```

Commit manifests to git for reproducible, shared run definitions.

## Pre-flight Checks

Before any sandbox run, Crux validates:

| Check | What it verifies |
|-------|-----------------|
| **MCP existence** | All declared MCPs are in the registry |
| **Secrets stored** | All auth-required secrets are in the keystore |
| **Sources built** | GitHub/local MCPs are cloned and built |
| **Timeout valid** | Timeout format is correct |
| **Permissions** | Launcher scripts are executable |
| **Env vars** | Environment variable names are valid |

If any check fails, you get the exact command to fix it:

```
Pre-flight failed:
  ✗ Secret 'WIKIJS_API_KEY' not found for MCP 'wikijs'
    Fix: crux secret set wikijs WIKIJS_API_KEY
```

## Managing Runs

### List Recent Runs

```bash
crux run list
```

Shows run ID, status, task, MCPs, and timestamps.

### Keep Sandbox for Debugging

```bash
crux run "debug this" --mcps filesystem --keep
```

The `--keep` flag preserves the sandbox directory after completion for inspection.

### Clean Up

```bash
# Remove completed sandboxes
crux run clean

# Force clean without confirmation
crux run clean --force
```

## Options

| Flag | Description |
|------|-------------|
| `--mcps <name...>` | MCPs to enable in the sandbox |
| `--file <path>` | Load configuration from a manifest file |
| `--keep` | Preserve sandbox after run |
| `--no-stream` | Collect output instead of streaming |
| `--force` | Skip confirmation for clean |
