# crux skill remove

Unregister a skill from the global registry.

## Usage

```bash
crux skill remove <name>
```

## Arguments

| Argument | Description |
|----------|-------------|
| `name` | Name of the registered skill to remove |

## Description

Removes the skill entry from `~/.crux/skills.json`. Does not delete cloned source directories.

## Examples

```bash
# Remove a registered skill
crux skill remove research

# Remove a local skill
crux skill remove my-skill
```
