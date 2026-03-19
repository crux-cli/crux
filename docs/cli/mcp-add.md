# crux mcp add

Register a new MCP server in the global registry.

## Usage

```bash
crux mcp add <name> [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `name` | Name for the registry entry |

## Options

| Option | Description |
|--------|-------------|
| `--npx <package>` | npm package to run via npx |
| `--uvx <package>` | PyPI package to run via uvx |
| `--github <user/repo>` | GitHub repository to clone |
| `--local <path>` | Local directory path |
| `--command <cmd>` | Command to run the MCP server |
| `--args <args>` | Arguments for the command (space-separated) |
| `--tags <tags>` | Comma-separated tags |
| `--keychain <vars>` | Comma-separated env var names for keychain auth |
| `--build-cmd <cmd>` | Build command to run after cloning |
| `--setup-cmd <cmd>` | Setup command to run after registration |

## Examples

```bash
# npm package
crux mcp add filesystem --npx @modelcontextprotocol/server-filesystem

# GitHub repo with build step
crux mcp add wikijs --github jaalbin24/wikijs-mcp-server \
  --build-cmd "npm install && npm run build"

# GitHub repo with keychain auth
crux mcp add github --npx @modelcontextprotocol/server-github \
  --keychain GITHUB_TOKEN

# PyPI package
crux mcp add my-tool --uvx my-mcp-tool

# Local path
crux mcp add dev-server --local /path/to/server
```
