# crux upgrade

Update cloned MCP/skill source repositories to their latest version.

## Usage

```bash
crux upgrade [names...] [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `names` | Specific names to upgrade (default: all cloned sources) |

## Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would be updated without making changes |

## Examples

```bash
# Upgrade all cloned sources
crux upgrade

# Upgrade specific MCPs
crux upgrade wikijs github

# Preview changes
crux upgrade --dry-run
```
