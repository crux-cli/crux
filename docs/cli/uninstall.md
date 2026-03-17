# crux uninstall

Remove MCPs or skills from the current project and sync.

## Usage

```bash
crux uninstall <name> [name...]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `names` | Names of MCPs or skills to uninstall (one or more) |

## Description

Removes the specified MCPs/skills from the current project's `crux.json` and runs `crux sync` to regenerate `.mcp.json`.

## Examples

```bash
crux uninstall wikijs
crux uninstall wikijs filesystem
```
