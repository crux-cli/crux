# Crux

**Harness manager for Claude Code.**

[![CI](https://github.com/crux-cli/crux/actions/workflows/ci.yml/badge.svg)](https://github.com/crux-cli/crux/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/crux-cli)](https://pypi.org/project/crux-cli/)
[![Docs](https://img.shields.io/badge/docs-crux--cli.github.io-blue)](https://crux-cli.github.io/crux)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

Crux v2 manages **harnesses** — versioned bundles of agent configuration (`CLAUDE.md`, skills, MCPs, plugins, hooks) for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Activate a harness with `crux use`, and Crux deploys symlinks into the paths Claude Code already reads from.

### Highlights

- **Composition as a first-class object.** A harness is a single TOML bundle that names which skills, MCPs, and plugins make up a configuration. Reuse it across projects instead of copy-pasting.
- **Versioning and rollback.** `crux bump` snapshots the current harness as the next version. `crux use -` rolls back to the previous activation. Every version is preserved on disk.
- **No magic, just symlinks.** Activation places symlinks under `~/.claude/` (or `<cwd>/.claude/`) pointing into the registry. `ls -la` shows exactly what Crux deployed; non-Crux files are never touched.
- **Per-directory or per-user.** Drop a `crux.toml` pointer in a project to override the user-level default. Resolution walks up from the cwd, then falls back to `~/.crux/active.toml`.
- **Secrets in your keychain.** API keys live in macOS Keychain, Linux Secret Service, or an age-encrypted vault. Launcher scripts fetch them at runtime; nothing ever lands in `.mcp.json`.

## Install

```bash
curl -LsSf https://raw.githubusercontent.com/crux-cli/crux/main/install.sh | sh
crux setup
```

Or with [uv](https://docs.astral.sh/uv/): `uv tool install crux-cli && crux setup`.

## Quickstart

```bash
# One-time setup
crux setup

# Stock the registry with primitives
crux registry add mcp filesystem @modelcontextprotocol/server-filesystem --npm
crux registry add skill autoresearch user/autoresearch-skill --github

# Build a harness and pull primitives into its bundle
crux new coding
crux edit skills coding --add autoresearch
crux edit mcps coding --add filesystem

# Activate it for everything (user-level)
crux use coding --user

# Or override per project
cd ~/code/my-app
crux use coding
crux active                    # prints "coding@v1 (directory, …/crux.toml)"

# Iterate: bump produces v2, roll back with `use -`
crux bump coding
crux use coding@v2 --user
crux use - --user              # back to v1
```

## Concepts

| Primitive | What it is |
|-----------|------------|
| **MCP**     | A server providing tools to the agent. Source: npm, uvx, GitHub, local, or HTTP. |
| **Skill**   | A reusable capability bundle. Source: local directory or GitHub repo. |
| **Plugin**  | A third-party bundle (own CLAUDE.md, hooks, skills). Stored versioned. |
| **Harness** | A composition referencing the above + its own CLAUDE.md + its own hooks. |

Harnesses are stored at `~/.crux/registry/harnesses/<name>/<version>/` with a `bundle.toml`:

```toml
[harness]
name = "coding"
version = "v3"
description = "Tuned for careful refactors"

[skills]
include = ["autoresearch"]

[mcps]
include = ["filesystem", "wikijs"]

[plugins]
include = ["awesome-coding@v2"]

[hooks]
pre_tool_use = "hooks/pre.sh"
```

A pointer file names the active harness:

```toml
# <project>/crux.toml or ~/.crux/active.toml
harness = "coding@v3"
```

`@<version>` is optional — omitted means *latest*.

## Commands

```
Setup:
  crux setup                                  Initialize ~/.crux
  crux doctor                                 Diagnose the environment
  crux migrate [--name <name>]                Migrate cwd's crux.json (v1.x)

Registry:
  crux registry add mcp <name> <src> [--npm|--uvx|--github|--local|--http] [--keychain VAR,VAR]
  crux registry add skill <name> <src> [--github]
  crux registry add plugin <name> <src> [--version vN]
  crux registry remove <name> [--force]
  crux registry list

Secrets:
  crux secret set <mcp> <key> [--value V]
  crux secret list [<mcp>]
  crux secret remove <mcp> <key>

Harness lifecycle:
  crux new <name>                             Create at v1
  crux bump <name>                            Snapshot latest as vN+1
  crux list [<name>]                          List harnesses or versions
  crux show <name>[@<v>]                      Display a bundle

Harness editing:
  crux edit claude [<ref>]                    Open $EDITOR on CLAUDE.md
  crux edit skills  [<ref>] [--add N --remove N ...]
  crux edit mcps    [<ref>] [--add N --remove N ...]
  crux edit plugins [<ref>] [--add N --remove N ...]
  crux edit hooks   [<ref>]                   Open $EDITOR on hooks/

Activation:
  crux use <name>[@<v>] [--user]              Activate; rebuild symlinks
  crux use -          [--user]                Roll back to previous
  crux use --none     [--user]                Deactivate
  crux active                                 Show resolved active harness
```

## Migration from v1.x

```bash
cd my-v1-project
crux migrate
# crux.json -> harness@v1 + crux.toml pointer
```

The migration creates a harness named after the project (override with `--name`), seeds it with the MCPs and skills from `crux.json`, writes a directory-level pointer, and deletes the old `crux.json`. The harness is at `~/.crux/registry/harnesses/<name>/v1/`.

## Security

- Secrets live in your OS keystore, not in files on disk.
- Launcher scripts hold lookup commands, not credential values.
- Generated `.mcp.json` references env-var names, never the values.
- `crux use` refuses to overwrite any file or symlink it didn't place.

## Documentation

Full docs at [crux-cli.github.io/crux](https://crux-cli.github.io/crux).

## Development

```bash
git clone https://github.com/crux-cli/crux
cd crux
uv sync --extra dev
uv run pytest tests/ -v
```

## License

[MIT](LICENSE)
