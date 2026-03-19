# crux skill add

Register a new skill in the global registry.

## Usage

```bash
crux skill add <name> [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `name` | Name for the skill registry entry |

## Options

| Option | Description |
|--------|-------------|
| `--github <user/repo>` | GitHub repository to clone |
| `--local <path>` | Local directory path |
| `--tags <tags>` | Comma-separated tags |
| `--build-cmd <cmd>` | Build command to run after cloning |

## Examples

```bash
# Skill from GitHub
crux skill add research --github user/research-skill

# Local skill
crux skill add my-skill --local /path/to/skill

# With tags
crux skill add research --github user/research-skill --tags research,web
```
