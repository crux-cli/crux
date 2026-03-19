# crux project uninstall

Remove MCP servers or skills from the current project.

## Usage

```bash
crux project uninstall <name> [name...]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `name` | One or more MCP server or skill names to remove from the project |

## Description

Removes the specified MCPs or skills from the current project's `crux.json`. Does not affect the global registry. Run `crux project sync` after to regenerate `.mcp.json`.

## Examples

```bash
# Remove a single MCP
crux project uninstall filesystem

# Remove multiple entries
crux project uninstall wikijs github

# Remove a skill
crux project uninstall research
```
