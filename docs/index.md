---
hide:
  - navigation
  - toc
---

# Crux

## Manage your MCP servers and skills like packages

Crux is a CLI tool for **macOS** and **Linux** that brings package-management to your **Claude Code** agentic workflows. Add MCP servers and skills to a local registry, declare which ones each project needs, and let Crux generate the config — with credentials in your OS keychain, never in files.

```bash
curl -LsSf https://raw.githubusercontent.com/crux-cli/crux/main/install.sh | sh
```

---

### Do you feel you're not taking full advantage of Claude Code?

The MCP ecosystem has 10,000+ servers and 60,000+ skills that can supercharge your agentic workflows. But discovering, configuring, and managing them across projects is a chore. You add one MCP, it works — then you need it in another project, and another, and you're copy-pasting JSON between repos. Skills are files you manually drop into directories. There's no `install`, no `upgrade`, no single place to manage it all.

**Crux gives you a personal registry.** Add an MCP or skill once — from npm, PyPI, GitHub, or a local path — and it's available to every project on your machine.

```bash
crux add mcp filesystem --npx @modelcontextprotocol/server-filesystem
crux add mcp github --npx @modelcontextprotocol/server-github
crux add mcp wikijs --github jaalbin24/wikijs-mcp-server
crux add skill autoresearch --github user/autoresearch-skill
crux search "database"   # discover more from the official registry
```

---

### Do you feel overwhelmed managing MCP servers, skills, and projects?

You have 20 projects. Each one needs a different combination of MCPs and skills. Maintaining 20 hand-edited `.mcp.json` files is unsustainable — and when you add a new tool to your workflow, you have to update every project that needs it.

**Crux scopes tools per project.** Each project gets a `crux.json` manifest declaring exactly what it needs. `crux sync` generates the `.mcp.json` Claude Code expects. Add a tool to one project without touching the others.

```bash
crux init homelab-assistant && cd homelab-assistant
crux install wikijs filesystem autoresearch
crux status   # verify every MCP is healthy
```

Your `crux.json` is clean and declarative:

```json
{
  "name": "homelab-assistant",
  "mcps": ["wikijs", "filesystem"],
  "skills": ["autoresearch"]
}
```

Commit it to git. The generated `.mcp.json` is gitignored — Crux rebuilds it from the manifest.

---

### Do you feel afraid of exploring ideas due to the risk agentic AI poses if misconfigured?

When every agent can see every tool, one misconfiguration can have outsized consequences. A research task accidentally triggers a write to production. An agent meant for your wiki has access to your cloud infrastructure. API keys sitting in plaintext `.env` files get committed to git.

**Crux isolates and secures.** Credentials live in your OS keychain — never in config files. Sandboxed runs give agents access to only the tools you explicitly declare. Pre-flight checks catch misconfigurations before execution starts.

```bash
# Secrets go in your OS keychain — macOS Keychain, Linux Secret Service, or age-encrypted vault
crux secret set wikijs WIKIJS_API_KEY
crux secret set github GITHUB_TOKEN

# Run an agent with only the tools it needs — nothing else
crux run "Summarize MCP security research and update the wiki" \
  --mcps wikijs \
  --skills autoresearch

# Full environment health check
crux doctor
```

---

## Before and after

### Without Crux

``` mermaid
%%{init: {'theme': 'neutral'}}%%
graph TB
    subgraph Claude["Claude Code"]
        direction TB
        G["Global .mcp.json\n<em>ALL 30 MCPs visible to every agent</em>"]
        PA[".mcp.json in Project A\n<em>hand-edited, copy-pasted</em>"]
        PB[".mcp.json in Project B\n<em>hand-edited, copy-pasted</em>"]
    end

    subgraph Problems["What goes wrong"]
        direction TB
        X1["🔓 API keys in plaintext\n.env files committed to git"]
        X2["📋 Config drift\neach project diverges over time"]
        X3["🎯 No scoping\nevery agent sees every tool"]
        X4["📁 Skills unmanaged\nfiles manually copied between machines"]
    end

    G --- X1
    G --- X3
    PA --- X2
    PB --- X2
    G --- X4
```

### With Crux

``` mermaid
%%{init: {'theme': 'neutral'}}%%
graph TB
    subgraph Crux["Crux Control Plane"]
        direction TB
        REG["Registry\none source of truth\nMCPs + Skills"]
        SEC["OS Keychain\nsecrets never in files"]
        SYN["Sync Engine\ngenerates scoped .mcp.json"]
    end

    subgraph Projects["Claude Code Projects"]
        direction TB
        PA["Project A\ncrux.json: wikijs, filesystem\n→ scoped .mcp.json <em>(2 MCPs)</em>"]
        PB["Project B\ncrux.json: github, memory\n→ scoped .mcp.json <em>(2 MCPs)</em>"]
        SB["Sandbox Run\ncrux run --mcps wikijs\n→ isolated .mcp.json <em>(1 MCP)</em>"]
    end

    REG --> SYN
    SEC --> SYN
    SYN --> PA
    SYN --> PB
    SYN --> SB
```

Each project sees **only** its declared tools. Secrets are fetched from the keychain at runtime. No config drift. No ambient access.

---

## How it works

``` mermaid
%%{init: {'theme': 'neutral'}}%%
graph LR
    subgraph Discovery["Discovery Sources"]
        direction TB
        S1["Official MCP Registry"]
        S2["npm / PyPI"]
        S3["GitHub Repos"]
        S4["Local Sources"]
    end

    subgraph Crux["Crux Control Plane"]
        direction TB
        REG["Registry\nMCPs + Skills"]
        SEC["Secrets\nOS Keychain"]
        SYN["Sync Engine\nGenerates .mcp.json"]
    end

    subgraph Projects["Your Projects"]
        direction TB
        P1["Project A\nwikijs, filesystem"]
        P2["Project B\ngithub, memory"]
        P3["Sandbox Run\nscoped access"]
    end

    S1 --> REG
    S2 --> REG
    S3 --> REG
    S4 --> REG
    REG --> SYN
    SEC --> SYN
    SYN --> P1
    SYN --> P2
    SYN --> P3
```

**Registry** — Add MCPs and skills once from npm, PyPI, GitHub, or local sources. One source of truth across all your projects.

**Secrets** — API keys live in your OS keychain (macOS Keychain, Linux Secret Service, or age-encrypted vault). Launcher scripts fetch them at runtime. Nothing is written to disk.

**Sync engine** — `crux sync` reads your project's `crux.json` and generates the `.mcp.json` that Claude Code expects, with only the tools you declared.

**Sandboxed execution** — `crux run` creates isolated environments where agents only see the MCPs you declare. Pre-flight validation catches misconfigurations before execution starts.

**Health monitoring** — `crux status` probes every MCP via JSON-RPC handshake. `crux doctor` validates your entire environment and auto-fixes what it can.

---

## Get started

```bash
curl -LsSf https://raw.githubusercontent.com/crux-cli/crux/main/install.sh | sh
```

Or with uv: `uv tool install crux-cli && crux setup`

<div class="grid cards" markdown>

-   [:octicons-arrow-right-24: Installation guide](getting-started/installation.md)
-   [:octicons-arrow-right-24: Quick start](getting-started/quickstart.md)
-   [:octicons-arrow-right-24: CLI reference](cli/index.md)
-   [:octicons-arrow-right-24: API reference](api/index.md)

</div>
