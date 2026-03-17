# Why Crux

The MCP ecosystem has exploded — 10,000+ servers, 60,000+ skills, and counting. But there's no way to manage them.

## The Problem

Without Crux, managing MCPs at scale looks like this:

| Pain | What happens |
|------|-------------|
| **Configuration sprawl** | 20 projects x 50 MCPs = 20 hand-maintained `.mcp.json` files. Add a new MCP? Edit every project. |
| **Credential leakage** | 48% of MCP servers recommend storing API keys in plaintext. Keys end up committed to git, leaked in logs. |
| **No scoping** | Every agent sees every tool. A coding assistant gets your home automation MCPs. A wiki bot gets filesystem write access. More tools = more noise = worse outputs. |
| **No reproducibility** | You can't `git clone` a project and get its MCP setup. There's no `npm install` for AI tooling. |
| **Skills are unmanaged** | 60,000+ Claude Code skills exist as files you manually copy between machines. No versioning. No scoping. No package management. |

## Scoping Is a Quality Lever

**An agent with 5 relevant tools outperforms one drowning in 50 irrelevant ones.** Less noise in the context window means better outputs, fewer hallucinated tool calls, and tighter security.

## Why Not Just...

| Alternative | What's missing |
|------------|---------------|
| Edit `.mcp.json` by hand | No scoping, no secrets management, config drift across projects, no reproducibility |
| Smithery / PulseMCP | Discovery platforms — they help you *find* MCPs, not *manage* them across projects |
| Docker MCP Gateway | Container isolation only — no registry, no per-project scoping, no credential management |
| MCPM | Profile-based — no project-level manifest, no keystore secrets, no sandboxed execution |

## Crux Is the Full Lifecycle

**Curate → Scope → Secure → Execute → Monitor.**

- **Registry**: Add MCPs and skills once from npm, PyPI, GitHub, or local sources. One source of truth across all projects.
- **Project scoping**: Each project declares exactly which MCPs and skills it needs in `crux.json`. No ambient access.
- **Secrets**: Credentials live in your OS keystore. Generated launcher scripts fetch them at runtime. Nothing is ever written to disk.
- **Sandboxed execution**: `crux run` creates isolated environments where agents only see the MCPs you declare.
- **Health monitoring**: `crux status` probes every MCP via JSON-RPC. `crux doctor` validates your entire environment.

## Security Stance

Crux takes an opinionated stance: **there is no insecure-but-easier path.**

- Secrets never appear in any file on disk — only in your OS keystore
- Launcher scripts contain keystore lookup commands, not credential values
- Generated `.mcp.json` never contains secrets
- Each sandbox gets only the MCPs explicitly declared for that run
- Path traversal protections on all file operations
