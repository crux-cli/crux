# Crux — AI Agent Control Plane

Crux is a CLI tool for managing MCP servers, skills, and agent sandboxes.

## Available Commands

- `crux search <query>` — Search the marketplace for MCPs and skills
- `crux add <name>` — Install an MCP or skill from the marketplace
- `crux remove <name>` — Uninstall an MCP or skill
- `crux sync` — Synchronise installed MCPs into `.mcp.json` for Claude Code
- `crux doctor` — Run health checks on all installed MCPs
- `crux run <task>` — Execute a task in an isolated sandbox with selected MCPs
- `crux secret set <mcp> <key> <value>` — Store an API key securely
- `crux secret get <mcp> <key>` — Retrieve a stored secret
- `crux setup` — Initialise or migrate the Crux home directory
- `crux version` — Show version and check for updates
- `crux upgrade` — Update installed MCPs and skills to latest versions

## Usage Notes

- Run `crux setup` first to initialise the `~/.crux/` directory.
- Use `crux search` to discover MCPs, then `crux add` to install them.
- After adding MCPs, run `crux sync` to update your Claude Code configuration.
- Use `crux doctor` to diagnose connectivity or authentication issues.
- Secrets are stored in the system keychain (macOS) or secret-service (Linux).
