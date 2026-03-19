# crux mcp upgrade

Update cloned MCP server sources.

## Usage

```bash
crux mcp upgrade [names...] [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `names` | One or more MCP names to upgrade (upgrades all if omitted) |

## Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would be upgraded without making changes |

## Description

Pulls the latest commits for GitHub-cloned MCPs and re-runs their build command if one is configured. Has no effect on npx/uvx MCPs (those always resolve at runtime).

## Examples

```bash
# Upgrade all cloned MCPs
crux mcp upgrade

# Upgrade a specific MCP
crux mcp upgrade wikijs

# Upgrade multiple MCPs
crux mcp upgrade wikijs github-mcp

# Preview what would be upgraded
crux mcp upgrade --dry-run
```
