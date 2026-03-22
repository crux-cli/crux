# Crux — Agentic Tool Manager for Claude Code

Crux is a CLI tool for managing MCP servers, skills, and agent tasks.

## Available Commands

### MCP Servers
- `crux mcp search <query>` — Search the MCP Registry
- `crux mcp add <name> --npx <pkg>` — Register an MCP server
- `crux mcp remove <name>` — Unregister an MCP server
- `crux mcp list` — List registered MCP servers
- `crux mcp upgrade` — Update cloned MCP repos
- `crux mcp auth <name>` — Authenticate an MCP server
- `crux mcp auth` — Show authentication status for all MCPs
- `crux mcp status` — Probe all registered MCP servers

### Skills
- `crux skill add <name> --github <repo>` — Register a skill
- `crux skill remove <name>` — Unregister a skill
- `crux skill list` — List registered skills

### Projects
- `crux project create [name]` — Create a new project with crux.json
- `crux project install <name>` — Add MCPs/skills to current project
- `crux project uninstall <name>` — Remove MCPs/skills from project
- `crux project sync` — Generate .mcp.json from crux.json
- `crux project status` — Show project health (MCPs, skills, auth)

### Tasks
- `crux task run <prompt>` — Execute a task in an isolated sandbox
- `crux task init` — Scaffold a run.json template
- `crux task list` — Show past/active runs
- `crux task clean` — Remove completed sandboxes

### System
- `crux init` — Initialize the crux environment
- `crux doctor` — Check crux environment health
- `crux version` — Show version and check for updates

## Usage Notes

- Run `crux init` first to set up the `~/.crux/` directory.
- Use `crux mcp search` to discover MCPs, then `crux mcp add` to register them.
- Use `--keychain VAR1,VAR2` with `crux mcp add` to declare and prompt for auth inline.
- Use `crux mcp auth <name>` to re-authenticate or rotate credentials later.
- Use `crux project create` to start a project, then `crux project install` to add MCPs.
- Secrets are stored in the system keychain (macOS) or secret-service (Linux).
