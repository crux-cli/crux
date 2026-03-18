# crux init

Create a new project with a `crux.json` manifest.

## Usage

```bash
crux init [name]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `name` | Project name (defaults to current directory name) |

## Description

Creates a `crux.json` file in the current directory and registers the project in `~/.crux/projects.json` for tracking.

## Examples

```bash
# Initialize with explicit name
crux init homelab-assistant

# Initialize using current directory name
crux init
```
