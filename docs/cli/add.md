# crux add

Register a new MCP or skill in the global registry.

## Usage

```bash
crux add <type> <name> [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `type` | Type to register: `mcp` or `skill` |
| `name` | Name for the registry entry |

## Options

| Option | Description |
|--------|-------------|
| `--npx <package>` | npm package to run via npx |
| `--uvx <package>` | PyPI package to run via uvx |
| `--github <user/repo>` | GitHub repository |
| `--local <path>` | Local directory path |
| `--command <cmd>` | Command to run the MCP |
| `--args <args>` | Arguments for the command (space-separated) |
| `--tags <tags>` | Comma-separated tags |
| `--keychain <vars>` | Comma-separated env var names for keychain auth |
| `--build-cmd <cmd>` | Build command to run after cloning |
| `--setup-cmd <cmd>` | Setup command to run after registration |

## Examples

```bash
# npm package
crux add mcp filesystem --npx @modelcontextprotocol/server-filesystem

# GitHub repo with build step
crux add mcp wikijs --github jaalbin24/wikijs-mcp-server \
  --build-cmd "npm install && npm run build"

# GitHub repo with auth
crux add mcp github --npx @modelcontextprotocol/server-github \
  --keychain GITHUB_TOKEN

# PyPI package
crux add mcp my-tool --uvx my-mcp-tool

# Local path
crux add mcp dev-server --local /path/to/server

# Skill from GitHub
crux add skill research --github user/research-skill
```
