# Authentication

Crux stores all credentials in your OS keystore — never in config files. There is no insecure-but-easier path.

The primary command for managing authentication is `crux mcp auth`.

## Auth Types

Crux supports several authentication methods depending on how an MCP server expects credentials:

| Type | When to use |
|------|-------------|
| `keychain` | API keys and tokens stored in the OS keystore |
| `external-cli` | Credentials fetched by an external CLI tool (e.g., `gh auth token`) |
| `setup-cmd` | A one-time setup command that configures the MCP itself |
| `bearer` | HTTP Bearer tokens passed in request headers |
| `oauth` | OAuth 2.0 flows managed by Crux |

Declare the auth type when adding an MCP. When `--keychain` is used, you are prompted for credentials inline:

```bash
crux mcp add github --npx @modelcontextprotocol/server-github --keychain GITHUB_TOKEN
# → Enter GITHUB_TOKEN: ****
# → ✓ Stored GITHUB_TOKEN
# → ✓ Authenticated 'github'
```

To re-authenticate or rotate credentials later, use `crux mcp auth`:

```bash
crux mcp auth github
```

## Storing Credentials

### Keychain (API Keys and Tokens)

Credentials are prompted inline during `crux mcp add --keychain`. To re-authenticate:

```bash
crux mcp auth wikijs
```

### Bearer Tokens

```bash
crux mcp auth my-api MY_API_TOKEN "Bearer eyJ..."
```

Bearer tokens are stored in the keystore and injected into the MCP launcher as an `Authorization` header value.

### OAuth

For MCPs that support OAuth 2.0:

```bash
crux mcp auth my-oauth-mcp --oauth
```

Crux opens the authorization URL in your browser, handles the redirect, and stores the resulting tokens. Refresh tokens are managed automatically.

### External CLI

For MCPs that delegate to an external CLI for authentication (e.g., the GitHub CLI):

```bash
crux mcp add github --npx @modelcontextprotocol/server-github --external-cli "gh auth token"
```

No separate `crux mcp auth` call is needed — the external command is called at MCP startup.

### Setup Command

For MCPs with existing `setup-cmd` auth type in the registry, authenticate via:

```bash
crux mcp auth my-tool
# → runs the configured setup command
```

## Viewing and Managing Credentials

```bash
# List all stored credentials (values hidden)
crux mcp auth --list

# Filter by MCP
crux mcp auth --list wikijs

# Remove a credential
crux mcp auth --delete wikijs WIKIJS_API_KEY
```

## Backends

Crux automatically selects the best backend for your platform:

| Platform | Backend | Storage |
|----------|---------|---------|
| **macOS** | Keychain | macOS Keychain via `security` CLI |
| **Linux (desktop)** | Secret Service | freedesktop.org Secret Service via `secretstorage` |
| **Linux (headless)** | age-encrypted | `~/.crux/secrets.age` encrypted with [age](https://age-encryption.org/) |

### macOS Keychain

Uses the built-in `security` CLI. Credentials are stored as generic passwords with the service name `crux.<mcp-name>`.

```bash
# What Crux stores:
# Service: crux.wikijs
# Account: WIKIJS_API_KEY
# Password: <your credential value>
```

### Linux Secret Service

Uses `secretstorage` (D-Bus interface to GNOME Keyring, KDE Wallet, etc.). Requires a running Secret Service daemon.

If no Secret Service is available, Crux automatically falls back to the age-encrypted backend.

### age-encrypted

For headless Linux servers without a desktop environment. Generates an age identity at `~/.crux/age-identity.key` and encrypts all credentials into `~/.crux/secrets.age`.

## How Credentials Reach MCPs

When `crux project sync` generates `.mcp.json`, authenticated MCPs reference a shared launcher script (`~/.crux/launchers/keychain-auth.sh`). The `.mcp.json` entry contains only *names* — never credential values:

```json
{
  "command": "~/.crux/launchers/keychain-auth.sh",
  "args": ["node", "~/.crux/mcps/wikijs/build/index.js"],
  "env": {
    "CRUX_MCP_NAME": "wikijs",
    "CRUX_AUTH_ENV_VARS": "WIKIJS_API_KEY"
  }
}
```

At runtime, the shared launcher detects the platform and fetches each credential from the OS keystore:

- **macOS**: `security find-generic-password -s crux.wikijs -a WIKIJS_API_KEY -w`
- **Linux**: `secret-tool lookup service crux.wikijs username WIKIJS_API_KEY`

The credential is fetched at runtime when the MCP server starts. It never exists in any file on disk.

## Credential Index

Crux maintains a **credential index** at `~/.crux/secrets.json` that tracks which keys exist for which MCPs — but never stores values:

```json
{
  "wikijs": ["WIKIJS_API_KEY"],
  "github": ["GITHUB_TOKEN"]
}
```

This index is used by pre-flight checks to verify all required credentials are present before starting a sandbox run.
