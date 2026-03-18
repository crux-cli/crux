# crux install

Add MCPs or skills to the current project and sync.

## Usage

```bash
crux install <name> [name...]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `names` | Names of MCPs or skills to install (one or more) |

## Description

Adds the specified MCPs/skills to the current project's `crux.json` and runs `crux sync` to regenerate `.mcp.json`.

## Examples

```bash
# Install a single MCP
crux install filesystem

# Install multiple MCPs
crux install wikijs filesystem github

# Install after cloning a repo with crux.json
cd my-project
crux install
```
