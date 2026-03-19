# Health Monitoring

Crux provides two levels of health checking: per-MCP probing and full environment diagnostics.

## MCP Server Status

```bash
crux project status
```

Probes each MCP in the current project via JSON-RPC handshake. For each server, Crux:

1. Starts the MCP server process
2. Sends an `initialize` request (MCP protocol)
3. Sends a `tools/list` request
4. Reports status, protocol version, and tool count

### Status Across All Projects

```bash
crux project status --all
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
| **Crux on PATH** | The `crux` binary is accessible |

`crux doctor` auto-fixes what it can — creating missing directories, installing the bundled skill, and reporting actionable fix commands for everything else.

## Initial Setup

If you are setting up Crux for the first time or re-initializing your environment:

```bash
crux init
```

This bootstraps the `~/.crux/` directory structure, installs the bundled skill, and verifies all external dependencies are in place.
