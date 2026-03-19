# crux mcp list

List all registered MCP servers.

## Usage

```bash
crux mcp list [options]
```

## Options

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |

## Description

Displays all MCP servers registered in `~/.crux/mcps.json`, including their source type (npx, uvx, github, local), tags, and auth configuration.

## Examples

```bash
# List in table format
crux mcp list

# Output as JSON
crux mcp list --json
```
