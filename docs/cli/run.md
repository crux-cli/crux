# crux run

Run an agent in an isolated sandbox with scoped MCP access.

## Usage

```bash
crux run <task> [options]
crux run --file <manifest.json>
crux run list
crux run clean [--force]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `task` | Task string describing what the agent should do |

## Options

| Option | Description |
|--------|-------------|
| `--mcps <name...>` | MCPs to enable in the sandbox |
| `--file <path>` | Load configuration from a manifest JSON file |
| `--keep` | Preserve sandbox directory after completion |
| `--no-stream` | Collect output instead of streaming |
| `--force` | Skip confirmation for clean subcommand |

## Subcommands

### list

List recent sandbox runs with status and metadata.

```bash
crux run list
```

### clean

Remove completed sandbox directories.

```bash
crux run clean
crux run clean --force
```

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
# Ad-hoc run
crux run "Research MCP security" --mcps wikijs filesystem

# From manifest
crux run --file tasks/research.json

# Keep sandbox for debugging
crux run "Debug issue" --mcps filesystem --keep

# List runs
crux run list

# Clean up
crux run clean --force
```
