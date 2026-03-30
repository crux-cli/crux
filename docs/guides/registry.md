# Registry Management

The registry is your personal catalog of MCP servers and skills. Add once, use in any project.

## Adding MCPs

Register MCP servers from different sources:

=== "npm"

    Installs the package globally via `npm install -g`, then registers it:

    ```bash
    crux mcp add filesystem --npm @modelcontextprotocol/server-filesystem
    crux mcp add github --npm @modelcontextprotocol/server-github
    ```

=== "PyPI"

    Installs the tool permanently via `uv tool install`, then registers it:

    ```bash
    crux mcp add my-tool --uv my-mcp-package
    ```

=== "GitHub"

    Clones the repo and auto-detects dependencies (`package.json`, `pyproject.toml`, or `requirements.txt`):

    ```bash
    crux mcp add wikijs --github jaalbin24/wikijs-mcp-server
    ```

    GitHub sources are cloned to `~/.crux/mcps/`. Dependencies are installed automatically. Use `--build-cmd` only for custom build steps beyond what auto-detection handles:

    ```bash
    crux mcp add custom --github user/repo --build-cmd "make build"
    ```

=== "Local"

    Copies the directory and auto-detects dependencies:

    ```bash
    crux mcp add my-local-mcp --local /path/to/mcp-server
    ```

### Adding with Authentication

If the MCP requires API keys, declare them with `--keychain`:

```bash
crux mcp add wikijs --github jaalbin24/wikijs-mcp-server --keychain WIKIJS_API_KEY
```

This tells Crux that `wikijs` expects the `WIKIJS_API_KEY` environment variable. The actual value is stored separately via `crux mcp auth`.

### Adding with Tags

Organize your MCPs with tags:

```bash
crux mcp add filesystem --npm @modelcontextprotocol/server-filesystem --tags "core,filesystem"
```

## Adding Skills

```bash
crux skill add my-skill --local /path/to/skill
crux skill add shared-skill --github user/skill-repo
```

## Listing the Registry

```bash
# List everything
crux mcp list

# JSON output (for scripts)
crux mcp list --json

# Filter by type
crux mcp list --type mcp
crux mcp list --type skill
```

## Searching the Official Registry

Search the official MCP Registry at registry.modelcontextprotocol.io:

```bash
crux mcp search github
crux mcp search "file system"
crux mcp search slack --limit 5
```

Results include suggested `crux mcp add` commands you can copy-paste.

## Upgrading Sources

Update GitHub-cloned MCPs to their latest version:

```bash
# Upgrade all cloned sources
crux mcp upgrade

# Upgrade specific MCPs
crux mcp upgrade wikijs github

# Preview without making changes
crux mcp upgrade --dry-run
```

## Removing Entries

```bash
crux mcp remove wikijs
crux skill remove my-skill
```

!!! warning
    Removing an MCP from the registry doesn't remove it from projects that reference it. Run `crux project sync` in those projects afterward.
