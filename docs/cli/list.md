# crux list

List all MCPs and skills in the global registry.

## Usage

```bash
crux list [options]
```

## Options

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |
| `--type <type>` | Filter by type: `mcp` or `skill` |

## Examples

```bash
# List everything
crux list

# JSON output for scripting
crux list --json

# Only MCPs
crux list --type mcp

# Only skills
crux list --type skill
```
