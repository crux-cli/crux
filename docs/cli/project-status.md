# crux project status

Show health and configuration of the current project.

## Usage

```bash
crux project status [options]
```

## Options

| Option | Description |
|--------|-------------|
| `--all` | Show status for all tracked projects |

## Description

Reports whether the current project's `crux.json` is in sync with its `.mcp.json`, lists configured MCPs and skills, and flags any missing global registry entries.

## Output

```
Project: homelab-assistant
  crux.json: ✓
  .mcp.json: ✓ (in sync)
  MCPs:      filesystem ✓  wikijs ✓  github ✓
  Skills:    research ✓
```

## Examples

```bash
# Status of current project
crux project status

# Status of all tracked projects
crux project status --all
```
