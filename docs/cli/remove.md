# crux remove

Unregister an MCP or skill from the global registry.

## Usage

```bash
crux remove <name>
```

## Arguments

| Argument | Description |
|----------|-------------|
| `name` | Name of the MCP or skill to remove |

## Examples

```bash
crux remove wikijs
```

!!! warning
    Removing an MCP from the registry doesn't remove it from projects that reference it. Run `crux sync` in affected projects afterward.
