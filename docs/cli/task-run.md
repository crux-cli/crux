# crux task run

Run an agent in an isolated sandbox with scoped MCP access.

## Usage

```bash
crux task run <prompt> [options]
crux task run --file <run.json>
```

## Arguments

| Argument | Description |
|----------|-------------|
| `prompt` | Task string describing what the agent should do |

## Options

| Option | Description |
|--------|-------------|
| `--mcp <names>` | Space-separated MCP server names to enable in the sandbox |
| `--file <path>` | Load task configuration from a `run.json` manifest |
| `--keep` | Preserve sandbox directory after completion |
| `--no-stream` | Collect output instead of streaming it |

## Run Manifest Format

```json
{
  "name": "weekly-research",
  "task": "Search for latest MCP security papers",
  "mcps": ["wikijs", "filesystem"],
  "skills": ["autoresearch"],
  "timeout_minutes": 30
}
```

## Examples

```bash
# Ad-hoc run with MCPs
crux task run "Research MCP security" --mcp wikijs filesystem

# From a run.json manifest
crux task run --file tasks/research.json

# Keep sandbox for debugging
crux task run "Debug issue" --mcp filesystem --keep

# Collect all output at end instead of streaming
crux task run "Summarize repo" --mcp filesystem --no-stream
```
