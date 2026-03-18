# Secrets Management

Crux stores all credentials in your OS keystore — never in config files. There is no insecure-but-easier path.

## Storing Secrets

```bash
# Interactive (prompts for value)
crux secret set wikijs WIKIJS_API_KEY

# Direct (for scripts)
crux secret set wikijs WIKIJS_API_KEY "sk-abc123..."
```

## Retrieving Secrets

```bash
crux secret get wikijs WIKIJS_API_KEY
```

Output is masked by default for safety.

## Listing Secrets

```bash
# All secrets (values hidden)
crux secret list

# Filter by MCP
crux secret list wikijs
```

## Deleting Secrets

```bash
crux secret delete wikijs WIKIJS_API_KEY
```

## Backends

Crux automatically selects the best backend for your platform:

| Platform | Backend | Storage |
|----------|---------|---------|
| **macOS** | Keychain | macOS Keychain via `security` CLI |
| **Linux (desktop)** | Secret Service | freedesktop.org Secret Service via `secretstorage` |
| **Linux (headless)** | age-encrypted | `~/.crux/secrets.age` encrypted with [age](https://age-encryption.org/) |

### macOS Keychain

Uses the built-in `security` CLI. Secrets are stored as generic passwords with the service name `crux.<mcp-name>`.

```bash
# What Crux stores:
# Service: crux.wikijs
# Account: WIKIJS_API_KEY
# Password: <your secret value>
```

### Linux Secret Service

Uses `secretstorage` (D-Bus interface to GNOME Keyring, KDE Wallet, etc.). Requires a running Secret Service daemon.

If no Secret Service is available, Crux automatically falls back to the age-encrypted backend.

### age-encrypted

For headless Linux servers without a desktop environment. Generates an age identity at `~/.crux/age-identity.key` and encrypts all secrets into `~/.crux/secrets.age`.

## How Secrets Reach MCPs

When `crux sync` generates a launcher script for an MCP that needs authentication, the script contains a keystore *lookup command* — not the secret value:

=== "macOS"

    ```bash
    #!/bin/bash
    export WIKIJS_API_KEY=$(security find-generic-password -s crux.wikijs -a WIKIJS_API_KEY -w)
    exec node ~/.crux/mcps/wikijs/build/index.js
    ```

=== "Linux"

    ```bash
    #!/bin/bash
    export WIKIJS_API_KEY=$(secret-tool lookup service crux.wikijs key WIKIJS_API_KEY)
    exec node ~/.crux/mcps/wikijs/build/index.js
    ```

The secret is fetched at runtime when the MCP server starts. It never exists in any file on disk.

## Security Index

Crux maintains a **secrets index** at `~/.crux/secrets.json` that tracks which keys exist for which MCPs — but never stores values:

```json
{
  "wikijs": ["WIKIJS_API_KEY"],
  "github": ["GITHUB_TOKEN"]
}
```

This index is used by pre-flight checks to verify all required secrets are present before starting a sandbox run.
