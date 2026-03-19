# crux task clean

Remove completed sandbox directories.

## Usage

```bash
crux task clean [options]
```

## Options

| Option | Description |
|--------|-------------|
| `--force` | Skip confirmation prompt |

## Description

Deletes the sandbox directories for all completed (non-running) task runs. Active runs are never removed. Use `crux task list` to review what will be deleted before running.

## Examples

```bash
# Clean with confirmation prompt
crux task clean

# Clean without prompting
crux task clean --force
```
