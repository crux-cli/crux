# crux project install

Add MCP servers or skills to the current project.

## Usage

```bash
crux project install <name> [name...]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `name` | One or more MCP server or skill names to add to the project |

## Description

Adds the specified MCPs or skills to the current project's `crux.json`. The names must already be registered globally (see `crux mcp add` or `crux skill add`). Run `crux project sync` after to regenerate `.mcp.json`.

## Examples

```bash
# Add a single MCP
crux project install filesystem

# Add multiple MCPs at once
crux project install filesystem wikijs github

# Add a skill
crux project install research
```
