# crux setup

Initialize the Crux environment.

## Usage

```bash
crux setup [name]
```

## Description

Creates the `~/.crux/` directory structure and initializes configuration. If `name` is provided, runs the setup command for a specific MCP.

When run without arguments, performs the full setup:

1. Creates `~/.crux/` and subdirectories (`mcps/`, `launchers/`, `skills/`, `sandbox/`)
2. Writes `config.toml` with platform-appropriate defaults
3. Installs the bundled Crux skill to `~/.claude/skills/crux/`
4. Detects and reports missing external dependencies
5. Optionally migrates data from the old marketplace layout

## Arguments

| Argument | Description |
|----------|-------------|
| `name` | MCP name — run setup command for a specific MCP (optional) |

## Examples

```bash
# Full environment setup
crux setup

# Run setup for a specific MCP
crux setup wikijs
```
