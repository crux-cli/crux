# crux mcp status

Probe all registered MCP servers and report their health.

## Usage

```bash
crux mcp status
```

## Description

Attempts to start each registered MCP server, verifies it responds to the MCP handshake, and reports pass/fail status. Useful for catching broken installs, missing secrets, or outdated builds before a task run.

## Output

```
✓ filesystem       npx   responding
✓ github           npx   responding
✗ wikijs           github  failed to start
  → build artifact missing, run: crux mcp upgrade wikijs
✓ linear           npx   responding
```

## Examples

```bash
crux mcp status
```
