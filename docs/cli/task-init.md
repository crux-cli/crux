# crux task init

Scaffold a `run.json` template for a repeatable task.

## Usage

```bash
crux task init [name]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `name` | Name for the task manifest (defaults to `run`) |

## Description

Creates a `run.json` file in the current directory with a template structure. Edit the file to configure the task prompt, MCPs, skills, and timeout before running with `crux task run --file run.json`.

## Examples

```bash
# Create run.json in current directory
crux task init

# Create a named manifest
crux task init weekly-research
# → creates weekly-research.json
```
