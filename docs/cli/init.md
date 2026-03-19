# crux init

Initialize the `~/.crux/` environment for first-time use.

## Usage

```bash
crux init
```

## Description

Sets up the `~/.crux/` directory structure and creates empty registry files if they do not already exist. Safe to re-run — existing registries are not overwritten.

Files created:

- `~/.crux/mcps.json` — global MCP registry
- `~/.crux/skills.json` — global skill registry
- `~/.crux/projects.json` — tracked projects list

Run this once after installing crux-cli. All other commands depend on this structure being present.

## Examples

```bash
# First-time setup
crux init
```
