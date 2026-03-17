# Registry Management

The registry is your personal catalog of MCP servers and skills. Add once, use in any project.

## Adding MCPs

Register MCP servers from different sources:

=== "npm (npx)"

    ```bash
    crux add mcp filesystem --npx @modelcontextprotocol/server-filesystem
    crux add mcp github --npx @modelcontextprotocol/server-github
    ```

=== "PyPI (uvx)"

    ```bash
    crux add mcp my-tool --uvx my-mcp-package
    ```

=== "GitHub"

    ```bash
    crux add mcp wikijs --github jaalbin24/wikijs-mcp-server
    ```

    GitHub sources are cloned to `~/.crux/mcps/`. If the MCP needs a build step:

    ```bash
    crux add mcp wikijs --github jaalbin24/wikijs-mcp-server --build-cmd "npm install && npm run build"
    ```

=== "Local"

    ```bash
    crux add mcp my-local-mcp --local /path/to/mcp-server
    ```

### Adding with Authentication

If the MCP requires API keys, declare them with `--keychain`:

```bash
crux add mcp wikijs --github jaalbin24/wikijs-mcp-server --keychain WIKIJS_API_KEY
```

This tells Crux that `wikijs` expects the `WIKIJS_API_KEY` environment variable. The actual value is stored separately via `crux secret set`.

### Adding with Tags

Organize your MCPs with tags:

```bash
crux add mcp filesystem --npx @modelcontextprotocol/server-filesystem --tags "core,filesystem"
```

## Adding Skills

```bash
crux add skill my-skill --local /path/to/skill
crux add skill shared-skill --github user/skill-repo
```

## Listing the Registry

```bash
# List everything
crux list

# JSON output (for scripts)
crux list --json

# Filter by type
crux list --type mcp
crux list --type skill
```

## Searching the Official Registry

Search the official MCP Registry at registry.modelcontextprotocol.io:

```bash
crux search github
crux search "file system"
crux search slack --limit 5
```

Results include suggested `crux add` commands you can copy-paste.

## Upgrading Sources

Update GitHub-cloned MCPs to their latest version:

```bash
# Upgrade all cloned sources
crux upgrade

# Upgrade specific MCPs
crux upgrade wikijs github

# Preview without making changes
crux upgrade --dry-run
```

## Removing Entries

```bash
crux remove wikijs
```

!!! warning
    Removing an MCP from the registry doesn't remove it from projects that reference it. Run `crux sync` in those projects afterward.
