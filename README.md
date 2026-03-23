# Crux

**Agentic Tool Manager for Claude Code.**

[![CI](https://github.com/crux-cli/crux/actions/workflows/ci.yml/badge.svg)](https://github.com/crux-cli/crux/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/crux-cli)](https://pypi.org/project/crux-cli/)
[![Docs](https://img.shields.io/badge/docs-crux--cli.github.io-blue)](https://crux-cli.github.io/crux)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

Crux is a CLI tool for **macOS** and **Linux** that brings package-management to your **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** agentic workflows. Add MCP servers and skills to a local registry, scope them per project, and keep credentials in your OS keychain — never in files.

### Highlights

- **One registry, every project** — add MCPs and skills once from npm, PyPI, GitHub, or local sources. No more copy-pasting `.mcp.json`.
- **Secrets in your keychain** — API keys live in macOS Keychain, Linux Secret Service, or an age-encrypted vault. Launcher scripts fetch them at runtime.
- **Scoped per project** — each project declares its tools in `crux.json`. Agents see only what's declared — fewer tools means better outputs.
- **Sandboxed execution** — `crux run` creates isolated environments with pre-flight validation. Misconfigurations are caught before your agent starts.
- **Health monitoring** — `crux status` probes every MCP via JSON-RPC. `crux doctor` validates your environment and auto-fixes what it can.
- **Discover & search** — search the official MCP registry from your terminal and add servers with one command.

## Install

**As a Claude Code plugin** (recommended):

```bash
claude plugin add crux-cli/crux
```

**Or via curl:**

```bash
curl -LsSf https://raw.githubusercontent.com/crux-cli/crux/main/install.sh | sh
```

Or if you already have [uv](https://docs.astral.sh/uv/): `uv tool install crux-cli && crux setup`

## Get started in three steps

**1. Build your registry** — add MCP servers and skills from any source:

```bash
crux add mcp filesystem --npx @modelcontextprotocol/server-filesystem
crux add mcp wikijs --github jaalbin24/wikijs-mcp-server
crux add skill autoresearch --github user/autoresearch-skill
```

**2. Store credentials securely** — API keys go in your OS keychain:

```bash
crux secret set wikijs WIKIJS_API_KEY
crux secret set github GITHUB_TOKEN
```

**3. Use in a project or a one-off sandbox:**

*Project mode* — declare what each project needs in a `crux.json` manifest:

```bash
crux init homelab-assistant && cd homelab-assistant
crux install wikijs filesystem autoresearch
crux status
```

*Sandbox mode* — run an agent with a specific set of tools, without a full project:

```bash
crux run "Update the wiki with latest research" \
  --mcps wikijs --skills autoresearch
```

## Replaces manual management of

| What | Without Crux | With Crux |
|------|-------------|-----------|
| **MCP config** | Hand-edited `.mcp.json` per project | `crux.json` manifest + `crux sync` |
| **Credentials** | Plaintext `.env` files committed to git | OS keychain, fetched at runtime |
| **Tool scoping** | Every agent sees every tool | Each project declares its own subset |
| **Skills** | Files manually copied between machines | Registry with `crux add skill` |

## Commands

```
Setup:
  crux setup                  Initialize ~/.crux and environment
  crux doctor                 Diagnose and auto-fix environment issues

Registry:
  crux add mcp <name>         Register an MCP (npm, PyPI, GitHub, local)
  crux add skill <name>       Register a skill
  crux remove <name>          Unregister an MCP or skill
  crux list                   List everything in the registry
  crux search <query>         Search the official MCP Registry
  crux upgrade [<name>]       Update cloned sources to latest

Project:
  crux init [<name>]          Create a project with crux.json
  crux install <name...>      Add MCPs/skills to project and sync
  crux uninstall <name...>    Remove MCPs/skills from project and sync
  crux sync [--all]           Generate .mcp.json from crux.json
  crux status [--all]         Show MCP server health

Secrets:
  crux secret set <mcp> <key> Store a secret in OS keystore
  crux secret get <mcp> <key> Retrieve a secret
  crux secret list [<mcp>]    List stored secrets (values masked)

Sandbox:
  crux run <task>             Execute agent with scoped MCP access
  crux run --file <manifest>  Execute from a reusable run manifest
  crux run list               List recent runs
  crux run clean              Remove completed sandboxes
```

## Security

Crux takes an opinionated stance: **there is no insecure-but-easier path.**

- Secrets never appear in any file on disk — only in your OS keystore
- Launcher scripts contain keystore lookup commands, not credential values
- Generated `.mcp.json` never contains secrets
- Each sandbox gets only the MCPs explicitly declared for that run
- Path traversal protections on all file operations

## Documentation

Full docs, guides, and API reference at [crux-cli.github.io/crux](https://crux-cli.github.io/crux).

## Development

```bash
git clone https://github.com/crux-cli/crux
cd crux
uv sync --extra dev
uv run pytest tests/ -v
```

## License

[MIT](LICENSE)
