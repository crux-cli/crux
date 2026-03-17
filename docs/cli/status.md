# crux status

Show MCP server health for the current project.

## Usage

```bash
crux status [options]
```

## Options

| Option | Description |
|--------|-------------|
| `--all` | Show status for all tracked projects |

## Description

Probes each MCP server in the current project via JSON-RPC handshake and displays a rich table with status, protocol version, and tool count.

## Examples

```bash
# Current project
crux status

# All tracked projects
crux status --all
```
