# crux mcp auth

Authenticate MCP servers by storing or refreshing credentials.

## Usage

```bash
crux mcp auth [name] [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `name` | MCP server name to authenticate (required unless `--all`) |

## Options

| Option | Description |
|--------|-------------|
| `--all` | Authenticate all MCPs that have auth configured |
| `--refresh` | Force re-authentication even if credentials exist |

## Auth Types

`crux mcp auth` handles all supported authentication methods. The auth type is determined by how the MCP was registered.

### Keychain

Secrets are stored in the OS keystore (macOS Keychain, Linux Secret Service, Windows Credential Manager). Set when the MCP was registered with `--keychain`.

```bash
# Store credentials for an MCP using keychain auth
crux mcp auth github
```

You are prompted for each env var listed in `--keychain`. Values are stored in the OS keystore and injected at runtime.

### External CLI

Some MCPs authenticate via an external CLI tool (e.g., `gh auth login`, `aws configure`). Crux delegates to the tool and verifies the result.

```bash
crux mcp auth gh-mcp
# → runs: gh auth login
```

### Setup Command

MCPs registered with `--setup-cmd` run that command during auth. Useful for browser-based flows or interactive installers.

```bash
crux mcp auth my-oauth-mcp
# → runs the configured setup-cmd
```

### Bearer Token

MCPs that accept a static bearer token store it in the keystore under the configured env var name. Prompted interactively.

```bash
crux mcp auth linear
# Prompts: LINEAR_API_KEY: ****
```

### OAuth

For MCPs with a configured OAuth flow, crux opens a browser and handles the callback to obtain and store tokens.

```bash
crux mcp auth google-drive
# → opens browser for OAuth consent
```

## Examples

```bash
# Authenticate a specific MCP
crux mcp auth github

# Authenticate all MCPs that need credentials
crux mcp auth --all

# Re-authenticate (replace existing credentials)
crux mcp auth github --refresh

# Authenticate all, replacing stale credentials
crux mcp auth --all --refresh
```
