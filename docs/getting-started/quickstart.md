# Quick Start

Set up a project with scoped MCP access in 30 seconds.

## 1. Add MCPs to Your Registry

Register MCP servers from npm, PyPI, GitHub, or local sources. You only do this once per MCP — they're available across all your projects.

```bash
# npm packages
crux add mcp filesystem --npm @modelcontextprotocol/server-filesystem

# GitHub repos
crux add mcp wikijs --github jaalbin24/wikijs-mcp-server

# PyPI packages
crux add mcp my-tool --uv my-mcp-tool
```

See what's available in the official registry:

```bash
crux search github
crux search filesystem
```

## 2. Store Secrets Securely

API keys go in your OS keychain — never in config files.

```bash
crux secret set wikijs WIKIJS_API_KEY
# → prompts securely, stores in macOS Keychain / Linux Secret Service
```

## 3. Create a Project

```bash
crux init homelab-assistant
cd homelab-assistant
```

This creates a `crux.json` file — your project's MCP manifest. Commit it to git.

## 4. Install MCPs into Your Project

```bash
crux install wikijs filesystem
```

This:

1. Adds `wikijs` and `filesystem` to your `crux.json`
2. Runs `crux sync` to generate the `.mcp.json` that Claude Code expects
3. Creates launcher scripts that fetch secrets from your keychain at runtime

## 5. Check Status

```bash
crux status
```

Shows a table of each MCP's health — whether it can start, its protocol version, and available tools.

## What Just Happened?

Your project now has:

| File | Purpose | Git? |
|------|---------|------|
| `crux.json` | Declares which MCPs this project uses | Committed |
| `.mcp.json` | Generated config for Claude Code | Gitignored |

When a teammate clones your repo, they run `crux install` and get the same setup — including keychain-based secrets on their machine.

## Next Steps

- [Run an agent in a sandbox](../guides/sandbox.md) — isolated execution with only the MCPs you specify
- [Manage secrets](../guides/secrets.md) — multi-backend keystore system
- [Health monitoring](../guides/health.md) — diagnose MCP server issues
- [Core concepts](concepts.md) — understand the architecture
