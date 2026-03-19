# crux project create

Create a new project with a `crux.json` manifest.

## Usage

```bash
crux project create [name] [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `name` | Project name (defaults to current directory name) |

## Options

| Option | Description |
|--------|-------------|
| `--mcp <names>` | Space-separated MCP server names to include |
| `--skill <names>` | Space-separated skill names to include |

## Description

Creates a `crux.json` file in the current directory and registers the project in `~/.crux/projects.json` for tracking. The manifest pins which MCPs and skills are scoped to this project.

## Examples

```bash
# Create with current directory name
crux project create

# Create with explicit name
crux project create homelab-assistant

# Create with MCPs pre-populated
crux project create research-bot --mcp filesystem wikijs github

# Create with MCPs and skills
crux project create analyst --mcp filesystem --skill research
```
