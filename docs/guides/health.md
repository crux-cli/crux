# Health Monitoring

Crux provides two levels of health checking: per-MCP probing and full environment diagnostics.

## MCP Server Status

```bash
crux status
```

Probes each MCP in the current project via JSON-RPC handshake. For each server, Crux:

1. Starts the MCP server process
2. Sends an `initialize` request (MCP protocol)
3. Sends a `tools/list` request
4. Reports status, protocol version, and tool count

### Status Across All Projects

```bash
crux status --all
```

Probes MCPs across all tracked projects.

## Environment Doctor

```bash
crux doctor
```

Runs a comprehensive set of checks:

| Check | What it validates |
|-------|------------------|
| **Python version** | Python 3.11+ is available |
| **External tools** | `git`, `node`/`npx`, `uv` are on PATH |
| **Directory structure** | `~/.crux/` and subdirectories exist |
| **Registry integrity** | `registry.json` is valid and parseable |
| **MCP sources** | Cloned repos exist on disk |
| **Build artifacts** | MCPs with build commands have their outputs |
| **Secrets consistency** | MCPs requiring auth have corresponding secrets |
| **Crux on PATH** | The `crux` binary is accessible |

`crux doctor` auto-fixes what it can — creating missing directories, installing the bundled skill, and reporting actionable fix commands for everything else.
