# Crux

**Your AI agents have access to 10,000+ MCP servers. They should only see five.**

[![CI](https://github.com/crux-cli/crux/actions/workflows/ci.yml/badge.svg)](https://github.com/crux-cli/crux/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/crux-cli)](https://pypi.org/project/crux-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

The MCP ecosystem has exploded — 10,000+ servers, 60,000+ skills, and counting. But there's no way to manage them. API keys sit in plaintext config files. Every project gets the same 50 MCPs dumped into its context, whether it needs them or not. Your research agent can accidentally call your trading API. Setting up a new project means copy-pasting `.mcp.json` and praying nothing leaks.

**Crux is the control plane that sits between your MCP ecosystem and your AI agents.** One registry. Per-project scoping. Secrets in your OS keychain — never in files. Sandboxed execution. Full lifecycle management for every tool your agents touch.

> Think `package.json` for AI tooling — declare what each project needs, and Crux handles the rest.

## The Problem Crux Solves

Without Crux, managing MCPs at scale looks like this:

| Pain | What happens |
|------|-------------|
| **Configuration sprawl** | 20 projects × 50 MCPs = 20 hand-maintained `.mcp.json` files. Add a new MCP? Edit every project. |
| **Credential leakage** | 48% of MCP servers recommend storing API keys in plaintext. Keys end up committed to git, leaked in logs. |
| **No scoping** | Every agent sees every tool. A coding assistant gets your home automation MCPs. A wiki bot gets filesystem write access. More tools = more noise = worse outputs. |
| **No reproducibility** | You can't `git clone` a project and get its MCP setup. There's no `npm install` for AI tooling. |
| **Skills are unmanaged** | 60,000+ Claude Code skills exist as files you manually copy between machines. No versioning. No scoping. No package management. |

**Scoping isn't just organization — it's a quality lever.** An agent with 5 relevant tools outperforms one drowning in 50 irrelevant ones. Less noise in the context window means better outputs, fewer hallucinated tool calls, and tighter security.
## Install

```bash
curl -LsSf https://raw.githubusercontent.com/crux-cli/crux/main/install.sh | sh
```

The installer checks for [uv](https://docs.astral.sh/uv/), installs it if missing, pulls `crux-cli` from PyPI, initialises `~/.crux/`, and tells you exactly what to do next (PATH fix, skill install).

**Alternatively**, if you already have uv:

```bash
uv tool install crux-cli
crux setup
```

## Workflow: Set Up a Project in 30 Seconds

You have a homelab assistant that needs wiki access and filesystem tools — nothing else.

```bash
# Add MCPs to your personal registry (once, ever)
crux add mcp filesystem --npx @modelcontextprotocol/server-filesystem
crux add mcp wikijs --github jaalbin24/wikijs-mcp-server

# Store credentials in your OS keychain — not in files
crux secret set wikijs WIKIJS_API_KEY
# → prompts securely, stores in macOS Keychain / Linux Secret Service

# Create a project — it gets exactly what it needs
crux init homelab-assistant && cd homelab-assistant
crux install wikijs filesystem
crux status
```

That's it. Your project now has a `crux.json` (committed to git) and a generated `.mcp.json` (gitignored) ready for Claude Code. The wiki MCP launches via a generated script that fetches your API key from the keychain at runtime. No secrets ever touch a file.

## Workflow: Run an Agent in a Sandbox

Your research agent should only access the wiki and a research skill — no filesystem, no GitHub, no trading APIs.

```bash
# Ad-hoc sandboxed run
crux run "Find papers on MCP security and update the wiki" \
  --mcps wikijs filesystem \
  --skills autoresearch

# Or save it as a reusable manifest (committed to git)
cat > tasks/weekly-research.json << 'EOF'
{
  "name": "weekly-research",
  "task": "Search for latest MCP security papers, summarize, update wiki",
  "mcps": ["wikijs", "filesystem"],
  "skills": ["autoresearch"],
  "timeout_minutes": 30
}
EOF

crux run --file tasks/weekly-research.json
```

Before execution, Crux runs pre-flight checks — every MCP exists, every secret is stored, every source is built. If something's missing, you get the exact command to fix it. No wasted agent time on mid-run failures.

## How It Works

```
  You discover MCPs           Crux manages them             Your agents use them
┌──────────────────┐    ┌───────────────────────┐    ┌──────────────────────┐
│  Smithery        │    │  crux add             │    │                      │
│  Official Reg.   │───▶│  ┌─ registry.json ──┐ │    │  Project A           │
│  GitHub          │    │  │ wikijs, github,   │ │    │  crux.json:          │
│  npm / PyPI      │    │  │ filesystem, slack │ │    │    wikijs, filesystem │
└──────────────────┘    │  │ memory, trading   │ │    │  → .mcp.json (2 MCPs)│
                        │  └───────────────────┘ │    │                      │
                        │                        │    │  Project B           │
                        │  crux secret set       │    │  crux.json:          │
                        │  ┌─ OS Keychain ─────┐ │    │    github, memory    │
                        │  │ API keys, tokens  │ │    │  → .mcp.json (2 MCPs)│
                        │  │ (never in files)  │ │    │                      │
                        │  └───────────────────┘ │    │  Sandbox Run         │
                        │                        │    │  crux run --mcps ... │
                        │  crux sync / crux run  │    │  → scoped .mcp.json  │
                        └───────────────────────┘    └──────────────────────┘
```

**Registry** — Add MCPs and skills once from npm, PyPI, GitHub, or local sources. One source of truth across all projects.

**Project scoping** — Each project declares exactly which MCPs and skills it needs in `crux.json`. `crux sync` generates the `.mcp.json` Claude Code expects. No ambient access.

**Secrets** — Credentials live in your OS keystore (macOS Keychain, Linux Secret Service, or age-encrypted vault). Generated launcher scripts fetch them at runtime. Nothing is ever written to disk.

**Sandboxed execution** — `crux run` creates isolated environments where agents only see the MCPs you declare. Pre-flight validation catches misconfigurations before execution starts.

**Health monitoring** — `crux status` probes every MCP via JSON-RPC handshake. `crux doctor` validates your entire environment and auto-fixes what it can.

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
- `crux doctor` warns if it detects plaintext credentials anywhere in your config
- Path traversal protections on all file operations

In an ecosystem where [48% of MCP servers recommend plaintext credential storage](https://www.stackone.com/blog/mcp-security-risks), Crux makes secure-by-default the only option.

## Why Not Just...

| Alternative | What's missing |
|------------|---------------|
| Edit `.mcp.json` by hand | No scoping, no secrets management, config drift across projects, no reproducibility |
| Smithery / PulseMCP | Discovery platforms — they help you *find* MCPs, not *manage* them across projects |
| Docker MCP Gateway | Container isolation only — no registry, no per-project scoping, no credential management |
| MCPM | Profile-based — no project-level manifest, no keystore secrets, no sandboxed execution |

Crux is the full lifecycle: **curate → scope → secure → execute → monitor.**
## Development

```bash
git clone https://github.com/crux-cli/crux
cd crux
uv sync --extra dev
uv run pytest tests/ -v
uv run ruff check src/crux_cli/ tests/
```

## Documentation

Full docs, guides, and API reference at [docs.crux.dev](https://docs.crux.dev) *(coming soon)*.

## License

[MIT](LICENSE)
