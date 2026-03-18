# crux sync

Generate `.mcp.json` from the project's `crux.json` manifest.

## Usage

```bash
crux sync [options]
```

## Options

| Option | Description |
|--------|-------------|
| `--all` | Sync all tracked projects |

## Description

Reads the current project's `crux.json` and generates:

- `.mcp.json` with scoped MCP server entries
- Launcher scripts for MCPs that require authentication
- Skill file copies

## Examples

```bash
# Sync current project
crux sync

# Sync all tracked projects
crux sync --all
```
