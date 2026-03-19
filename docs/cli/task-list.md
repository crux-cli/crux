# crux task list

Show past and active sandbox runs.

## Usage

```bash
crux task list
```

## Description

Lists recent task runs with their status, start time, and sandbox directory path. Useful for finding a specific run's output or identifying runs that are still active.

## Output

```
ID          STATUS     STARTED              PROMPT
run-a1b2c3  completed  2026-03-19 14:02:01  Research MCP security
run-d4e5f6  running    2026-03-19 14:45:30  Summarize repo changes
run-g7h8i9  failed     2026-03-18 09:11:00  Debug filesystem issue
```

## Examples

```bash
crux task list
```
