# crux mcp search

Search the official MCP Registry.

## Usage

```bash
crux mcp search <query> [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `query` | Search query (e.g., `github`, `slack`, `filesystem`) |

## Options

| Option | Description |
|--------|-------------|
| `--limit <N>` | Maximum results to return (default: 20) |
| `--add` | Interactively add a result to your registry |

## Examples

```bash
# Search for GitHub-related MCPs
crux mcp search github

# Limit results
crux mcp search filesystem --limit 5

# Search and add interactively
crux mcp search slack --add
```
