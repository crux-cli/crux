# Project Scoping

Projects are Crux's core abstraction for per-directory MCP management. Each project declares exactly which MCPs and skills it needs.

## Creating a Project

```bash
crux project create my-project
cd my-project
```

Or initialize in the current directory:

```bash
crux project create
```

This creates a `crux.json`:

```json
{
  "name": "my-project",
  "mcps": [],
  "skills": []
}
```

Commit `crux.json` to git. It's your project's MCP manifest.

## Installing MCPs

```bash
crux project install wikijs filesystem
```

This:

1. Adds the names to `crux.json`
2. Runs `crux project sync` to generate `.mcp.json`
3. Creates launcher scripts for MCPs that need authentication

## Uninstalling MCPs

```bash
crux project uninstall wikijs
```

Removes from `crux.json` and re-syncs.

## Syncing

If you edit `crux.json` manually, regenerate the Claude Code config:

```bash
crux project sync
```

Sync all tracked projects at once:

```bash
crux project sync --all
```

## What `crux project sync` Generates

Given this `crux.json`:

```json
{
  "name": "homelab",
  "mcps": ["wikijs", "filesystem"],
  "skills": []
}
```

Crux generates:

**`.mcp.json`** — the file Claude Code reads:

```json
{
  "mcpServers": {
    "wikijs": {
      "command": "/Users/you/.crux/launchers/wikijs.sh",
      "args": []
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"]
    }
  }
}
```

**`~/.crux/launchers/wikijs.sh`** — fetches secrets at runtime:

```bash
#!/bin/bash
export WIKIJS_API_KEY=$(security find-generic-password -s crux.wikijs -a WIKIJS_API_KEY -w)
exec node /Users/you/.crux/mcps/wikijs/build/index.js
```

## Reproducibility

When a teammate clones your repo:

```bash
git clone https://github.com/you/homelab.git
cd homelab
crux project install  # reads crux.json, syncs everything
crux mcp auth wikijs WIKIJS_API_KEY  # enter their own key
crux project status  # verify everything works
```

The `crux.json` is the source of truth. The generated `.mcp.json` and launcher scripts are local artifacts.

## Project Tracking

Crux tracks all initialized projects in `~/.crux/projects.json`. This enables `crux project sync --all` and `crux project status --all`.

Stale projects (deleted directories) are detected and cleaned up automatically.
