# crux secret

Manage MCP secrets stored in your OS keystore.

## Usage

```bash
crux secret <subcommand> [options]
```

## Subcommands

### set

Store a secret in the OS keystore.

```bash
crux secret set <mcp> <key> [value]
```

| Argument | Description |
|----------|-------------|
| `mcp` | MCP name |
| `key` | Environment variable name |
| `value` | Secret value (omit to be prompted securely) |

### get

Retrieve a secret.

```bash
crux secret get <mcp> <key>
```

### list

List stored secrets (values are masked).

```bash
crux secret list [mcp]
```

| Argument | Description |
|----------|-------------|
| `mcp` | Filter by MCP name (optional) |

### delete

Remove a secret from the keystore.

```bash
crux secret delete <mcp> <key>
```

## Examples

```bash
# Store a secret (prompted)
crux secret set wikijs WIKIJS_API_KEY

# Store a secret (direct)
crux secret set wikijs WIKIJS_API_KEY "sk-abc123"

# Retrieve
crux secret get wikijs WIKIJS_API_KEY

# List all
crux secret list

# List for specific MCP
crux secret list wikijs

# Delete
crux secret delete wikijs WIKIJS_API_KEY
```
