# Why Crux

## The MCP management crisis

The MCP ecosystem has exploded — 10,000+ servers, 60,000+ skills, and counting. But there's no way to manage them at scale.

Meet Alex, a developer building multi-agent workflows. They have 30+ MCPs across 8 projects, API keys for 15 services scattered across config files, and a research agent that once accidentally called the trading API because all MCPs were globally visible. Setting up a new project means copying `.mcp.json` by hand, editing it for 30 minutes, and hoping nothing leaks.

Alex's story isn't unusual. Every developer building with AI agents hits the same wall.

## Five problems that compound

| # | Problem | What happens at scale |
|---|---------|----------------------|
| 1 | **Configuration sprawl** | 20 projects x 50 MCPs = 20 hand-maintained `.mcp.json` files. Add a new MCP? Edit every project. |
| 2 | **Credential leakage** | 48% of MCP servers recommend storing API keys in plaintext. Keys end up committed to git, leaked in logs. |
| 3 | **No scoping** | Every agent sees every tool. A coding assistant gets home automation MCPs. A wiki bot gets filesystem write access. More tools = more noise = worse outputs. |
| 4 | **No reproducibility** | You can't `git clone` a project and get its MCP setup. There's no `npm install` for AI tooling. |
| 5 | **Skills are unmanaged** | 60,000+ Claude Code skills exist as files you manually copy between machines. No versioning, no scoping, no package management. |

## Scoping is a quality lever

This is the core insight behind Crux: **limiting what an agent can see makes it better at what it does.**

An agent with 5 relevant tools consistently outperforms one with 50 irrelevant ones:

- **Better outputs** — the model focuses on tools that matter for the task
- **Fewer hallucinated tool calls** — no accidental calls to your trading API from a wiki bot
- **Tighter security** — each agent's blast radius is limited to what it actually needs
- **Faster execution** — smaller tool lists mean faster MCP initialization and less context overhead

Scoping isn't a restriction. It's an optimization.

## What Crux does

Crux applies patterns you already know — `package.json`, `direnv`, Homebrew — to AI agent tooling:

| Pattern | Analogy | What Crux does |
|---------|---------|---------------|
| **Tool registry** | Homebrew / mise | Install, upgrade, and manage MCPs and skills from any source |
| **Project manifest** | package.json + npm | Per-project declarative config, git-versionable, reproducible |
| **Secret binding** | direnv + OS keystore | Credentials bound to MCPs, never in files, resolved at runtime |
| **Sandboxed execution** | *(new)* | Run an agent with exactly the MCPs it needs and nothing else |

## What Crux is NOT

- **Not a marketplace.** There is no Crux-hosted registry. Use Smithery, PulseMCP, or the official MCP registry to *discover* tools. Crux manages what you've already chosen.
- **Not a cloud service.** All configuration lives on your machine.
- **Not competing with MCP discovery platforms.** Crux starts where discovery ends.

## Why not just...

| Alternative | What's missing |
|------------|---------------|
| Edit `.mcp.json` by hand | No scoping, no secrets management, config drift across projects, no reproducibility |
| Smithery / PulseMCP | Discovery platforms — they help you *find* MCPs, not *manage* them |
| Docker MCP Gateway | Container isolation only — no registry, no per-project scoping, no credential management |
| MCPM | Profile-based — no project-level manifest, no keystore secrets, no sandboxed execution |

## The full lifecycle

**Curate → Scope → Secure → Execute → Monitor**

1. **Curate** — Build a personal registry of MCPs and skills. Add from npm, PyPI, GitHub, or local sources. One source of truth across all projects.
2. **Scope** — Each project declares exactly which MCPs and skills it needs in `crux.json`. Agents only see what's declared.
3. **Secure** — Credentials live in your OS keystore. Launcher scripts fetch them at runtime. Nothing is ever written to disk.
4. **Execute** — `crux run` creates sandboxes where agents only access declared MCPs. Pre-flight checks catch misconfigurations before execution.
5. **Monitor** — `crux status` probes every MCP via JSON-RPC. `crux doctor` validates your entire environment and auto-fixes what it can.
