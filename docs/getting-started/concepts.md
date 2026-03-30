# Core Concepts

Understanding Crux's architecture and key abstractions.

## Registry

The **registry** (`~/.crux/registry.json`) is your personal catalog of all MCP servers and skills you've registered. It's machine-wide — shared across all your projects.

```bash
crux add mcp filesystem --npm @modelcontextprotocol/server-filesystem
crux add mcp wikijs --github jaalbin24/wikijs-mcp-server
crux list
```

Each registry entry stores:

- **Source**: where to find the MCP (npm, PyPI, GitHub, local path)
- **Transport**: how to communicate (stdio, SSE)
- **Auth**: which environment variables the MCP expects (keys stored separately in keychain)
- **Build**: optional build command for GitHub-sourced MCPs
- **Tags**: for organization and filtering

## Projects

A **project** is a directory with a `crux.json` file. It declares exactly which MCPs and skills the project needs — nothing more.

```json
{
  "name": "homelab-assistant",
  "mcps": ["wikijs", "filesystem"],
  "skills": []
}
```

`crux sync` reads this manifest and generates the `.mcp.json` that Claude Code expects, with only the declared MCPs. The `crux.json` is committed to git; the `.mcp.json` is gitignored.

## Scoping

**Scoping** is the core principle: each project (or sandbox run) sees only the tools it needs.

Without scoping, every agent sees every MCP you've ever configured. This causes:

- **Noise**: 50 tools in the context window when 5 are relevant
- **Worse outputs**: agents hallucinate calls to irrelevant tools
- **Security risk**: a wiki bot can access your trading API

With Crux, each project declares its MCPs in `crux.json`. The generated `.mcp.json` contains only those entries.

## Secrets

Crux stores credentials in your **OS keystore** — never in files.

| Platform | Backend |
|----------|---------|
| macOS | Keychain (`security` CLI) |
| Linux (desktop) | Secret Service (`secretstorage`) |
| Linux (headless) | age-encrypted file (`~/.crux/secrets.age`) |

When `crux sync` generates launcher scripts, they contain commands to fetch secrets at runtime:

```bash
# macOS launcher (generated)
export WIKIJS_API_KEY=$(security find-generic-password -s crux.wikijs -a WIKIJS_API_KEY -w)
```

The secret value never touches a file. The launcher script only contains the *lookup command*.

## Sandbox

A **sandbox** is an isolated execution environment for running agents. It gets its own `.mcp.json` with only the MCPs you specify.

```bash
crux run "Research MCP security papers" --mcps wikijs filesystem
```

Before execution, Crux runs **pre-flight checks**:

1. All MCPs exist in the registry
2. All required secrets are stored
3. All GitHub/local sources are cloned and built
4. Timeout values are valid
5. Launcher scripts have correct permissions
6. Environment variable names are valid

If anything fails, you get the exact command to fix it — before wasting agent time.

## Health Monitoring

`crux status` probes each MCP server via **JSON-RPC handshake** — it actually starts the server, performs the MCP protocol initialize sequence, and reports:

- Whether the server starts successfully
- Protocol version
- Number of available tools
- Error details if something fails

`crux doctor` goes further — validating your entire Crux environment (directories, config, dependencies, registry integrity) and auto-fixing what it can.

## File Layout

```
~/.crux/
├── config.toml          # User configuration
├── registry.json        # MCP and skill registry
├── projects.json        # Tracked project paths
├── secrets.json         # Secret key index (values in keychain)
├── mcps/                # Cloned MCP source repos
├── launchers/           # Generated launcher scripts
├── skills/              # Installed skills
└── sandbox/             # Sandbox run directories
    └── 20260317-a3f2/
        ├── .mcp.json
        ├── workspace/
        └── run-meta.json
```
