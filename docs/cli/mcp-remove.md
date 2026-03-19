# crux mcp remove

Unregister an MCP server from the global registry.

## Usage

```bash
crux mcp remove <name>
```

## Arguments

| Argument | Description |
|----------|-------------|
| `name` | Name of the registered MCP server to remove |

## Description

Removes the MCP entry from `~/.crux/mcps.json`. Does not delete cloned source directories — use `crux doctor` to identify orphaned sources.

## Examples

```bash
# Remove a registered MCP
crux mcp remove filesystem

# Remove a GitHub-cloned MCP
crux mcp remove wikijs
```
