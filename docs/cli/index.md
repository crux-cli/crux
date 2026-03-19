# CLI Reference

Complete reference for all `crux` commands.

## System

| Command | Description |
|---------|-------------|
| [`crux init`](init.md) | Initialize `~/.crux/` and environment |
| [`crux doctor`](doctor.md) | Diagnose environment issues |
| [`crux version`](version.md) | Show crux-cli version |

## MCP Servers

| Command | Description |
|---------|-------------|
| [`crux mcp add`](mcp-add.md) | Register a new MCP server |
| [`crux mcp remove`](mcp-remove.md) | Unregister an MCP server |
| [`crux mcp list`](mcp-list.md) | List registered MCP servers |
| [`crux mcp search`](mcp-search.md) | Search the official MCP Registry |
| [`crux mcp upgrade`](mcp-upgrade.md) | Update cloned sources |
| [`crux mcp auth`](mcp-auth.md) | Authenticate MCP servers |
| [`crux mcp status`](mcp-status.md) | Probe all registered MCP servers |

## Skills

| Command | Description |
|---------|-------------|
| [`crux skill add`](skill-add.md) | Register a new skill |
| [`crux skill remove`](skill-remove.md) | Unregister a skill |
| [`crux skill list`](skill-list.md) | List registered skills |

## Projects

| Command | Description |
|---------|-------------|
| [`crux project create`](project-create.md) | Create a project with `crux.json` |
| [`crux project install`](project-install.md) | Add MCPs/skills to project |
| [`crux project uninstall`](project-uninstall.md) | Remove MCPs/skills from project |
| [`crux project sync`](project-sync.md) | Generate `.mcp.json` from `crux.json` |
| [`crux project status`](project-status.md) | Show project health |

## Tasks

| Command | Description |
|---------|-------------|
| [`crux task run`](task-run.md) | Run an agent in an isolated sandbox |
| [`crux task init`](task-init.md) | Scaffold a `run.json` template |
| [`crux task list`](task-list.md) | Show past/active runs |
| [`crux task clean`](task-clean.md) | Remove completed sandboxes |
