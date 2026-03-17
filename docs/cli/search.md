# crux search

Search the official MCP Registry.

## Usage

```bash
crux search <query> [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `query` | Search query (e.g., `github`, `slack`, `filesystem`) |

## Options

| Option | Description |
|--------|-------------|
| `--limit <N>` | Maximum results (default: 20) |
| `--add` | Interactively add a result to your registry |

## Examples

```bash
# Search for GitHub-related MCPs
crux search github

# Limit results
crux search filesystem --limit 5

# Search and add interactively
crux search slack --add
```
