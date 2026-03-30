# crux mcp add

Install and register a new MCP server in the global registry.

When you add an MCP, Crux installs its dependencies before registering it. This catches broken packages, missing dependencies, and build failures immediately — not when an agent tries to use the server mid-task.

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
| `--npm <package>` | npm package (runs `npm install -g` to install globally) |
| `--uv <package>` | PyPI package (runs `uv tool install` to install permanently) |
| `--github <user/repo>` | GitHub repository (clones and auto-installs dependencies) |
| `--local <path>` | Local directory path (copies and auto-installs dependencies) |
| `--command <cmd>` | Command to run the MCP server |
| `--args <args>` | Arguments for the command (space-separated) |
| `--tags <tags>` | Comma-separated tags |
| `--keychain <vars>` | Comma-separated env var names for keychain auth (prompts inline) |
| `--build-cmd <cmd>` | Build command to run after cloning |
| `--skip-validation` | Skip package installation and dependency checks |

## What happens during `mcp add`

### npm packages (`--npm`)

Runs `npm install -g <package>` to install the package globally. If the package doesn't exist (E404), fails to download, or is incompatible with your platform, the error is reported immediately and the MCP is not registered.

### PyPI packages (`--uv`)

Runs `uv tool install <package>` to permanently install the tool. If the package doesn't exist, all versions are yanked, or it fails to build (e.g., C extension on wrong Python version), the error is reported immediately.

### GitHub repos (`--github`)

Clones the repo, then auto-detects the project type and installs dependencies:

- `package.json` found: runs `npm install`, then `npm run build` if a build script exists
- `pyproject.toml` found: runs `uv sync`
- `requirements.txt` found: runs `uv venv && uv pip install -r requirements.txt`

If dependency installation fails, the cloned directory is cleaned up and the MCP is not registered.

### Local directories (`--local`)

Copies the directory to `~/.crux/mcps/<name>/`, then runs the same dependency auto-detection as GitHub repos.

### `--skip-validation`

Bypasses installation and dependency checks entirely. The MCP is registered with just the metadata. Use this when:

- The MCP requires authentication before it can be installed
- You're working offline and will install later
- You're using a private registry that Crux can't access

## Examples

```bash
# npm package — installs globally, then registers
crux mcp add filesystem --npm @modelcontextprotocol/server-filesystem

# PyPI package — installs via uv tool, then registers
crux mcp add my-tool --uv my-mcp-tool

# GitHub repo — clones, installs deps, builds, then registers
crux mcp add wikijs --github jaalbin24/wikijs-mcp-server

# With keychain auth (prompts for credentials inline)
crux mcp add github --npm @modelcontextprotocol/server-github \
  --keychain GITHUB_TOKEN

# Skip installation (register only)
crux mcp add my-private-mcp --npm @private/mcp-server --skip-validation

# Local path
crux mcp add dev-server --local /path/to/server
```
