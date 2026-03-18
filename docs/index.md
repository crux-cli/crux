---
hide:
  - navigation
  - toc
---

# Crux

## The package manager for AI agent tooling

Your agents use dozens of MCP servers and skills. Crux manages them the way `npm` manages packages — one manifest, scoped per project, credentials never in files.

<div class="grid cards" markdown>

-   :material-package-variant:{ .lg .middle } __One registry, every project__

    ---

    Add MCPs from npm, PyPI, or GitHub once. Every project draws from the same source of truth — no more copy-pasting `.mcp.json` between repos.

    [:octicons-arrow-right-24: Registry](guides/registry.md)

-   :material-shield-lock:{ .lg .middle } __Secrets that never touch disk__

    ---

    API keys live in your OS keychain. Launcher scripts fetch them at runtime. Nothing is ever written to a config file.

    [:octicons-arrow-right-24: Secrets](guides/secrets.md)

-   :material-file-document-check:{ .lg .middle } __Declarative project manifests__

    ---

    `crux.json` declares what each project needs. `crux sync` generates the rest. Clone, install, done — like `package.json` for AI tooling.

    [:octicons-arrow-right-24: Projects](guides/projects.md)

-   :material-cube-outline:{ .lg .middle } __Scoped, sandboxed execution__

    ---

    Each agent sees only the tools it needs. Less noise in the context window means better outputs and fewer hallucinated tool calls.

    [:octicons-arrow-right-24: Sandbox](guides/sandbox.md)

</div>

---

## The problem Crux solves

You have 30 MCP servers across 8 projects. Each project needs a different subset. Your research agent accidentally called the trading API because all MCPs were globally visible. API keys sit in `.env` files committed to git. Setting up a new project means 30 minutes of config editing.

**Crux fixes this with one workflow:**

```bash
# Build your personal tool registry (once, ever)
crux add mcp filesystem --npx @modelcontextprotocol/server-filesystem
crux add mcp wikijs --github jaalbin24/wikijs-mcp-server
crux add skill autoresearch --github user/autoresearch-skill

# Credentials go in your OS keychain — never in files
crux secret set wikijs WIKIJS_API_KEY

# Each project declares exactly what it needs
crux init homelab-assistant && cd homelab-assistant
crux install wikijs filesystem autoresearch
```

That's it. Your project has a `crux.json` (committed to git) and a generated `.mcp.json` (gitignored). When a teammate clones the repo, they run `crux install` and get the same setup — with their own credentials from their own keychain.

---

## Architecture

``` mermaid
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
        REG["Registry<br/><code>~/.crux/registry.json</code><br/>MCPs + Skills"]
        SEC["Secrets<br/>OS Keychain<br/><em>never in files</em>"]
        SYN["Sync Engine<br/><code>crux sync</code><br/>Generates .mcp.json + launchers"]
    end

    subgraph Projects["Your Projects"]
        direction TB
        P1["<strong>Project A</strong><br/><code>crux.json</code>: wikijs, filesystem<br/>→ .mcp.json <em>(2 MCPs)</em>"]
        P2["<strong>Project B</strong><br/><code>crux.json</code>: github, memory<br/>→ .mcp.json <em>(2 MCPs)</em>"]
        P3["<strong>Sandbox Run</strong><br/><code>crux run --mcps ...</code><br/>→ scoped .mcp.json"]
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

    style Discovery fill:#e8eaf6,stroke:#5c6bc0,color:#1a237e
    style Crux fill:#f3e5f5,stroke:#8e24aa,color:#4a148c
    style Projects fill:#e8f5e9,stroke:#43a047,color:#1b5e20
    style REG fill:#ede7f6,stroke:#7e57c2,color:#311b92
    style SEC fill:#fce4ec,stroke:#e53935,color:#b71c1c
    style SYN fill:#ede7f6,stroke:#7e57c2,color:#311b92
    style S1 fill:#e8eaf6,stroke:#5c6bc0,color:#1a237e
    style S2 fill:#e8eaf6,stroke:#5c6bc0,color:#1a237e
    style S3 fill:#e8eaf6,stroke:#5c6bc0,color:#1a237e
    style S4 fill:#e8eaf6,stroke:#5c6bc0,color:#1a237e
    style P1 fill:#e8f5e9,stroke:#43a047,color:#1b5e20
    style P2 fill:#e8f5e9,stroke:#43a047,color:#1b5e20
    style P3 fill:#e8f5e9,stroke:#43a047,color:#1b5e20
```

---

## Why scoping matters

Scoping isn't just organization — it's a **quality lever**.

An agent with 5 relevant tools consistently outperforms one drowning in 50 irrelevant ones. Less noise in the context window means:

- **Better outputs** — the model focuses on relevant tools
- **Fewer hallucinated tool calls** — no accidental calls to the trading API from your wiki bot
- **Tighter security** — each agent's blast radius is limited to what it actually needs
- **Faster execution** — smaller tool lists mean faster MCP initialization

---

## Install

```bash
curl -LsSf https://raw.githubusercontent.com/crux-cli/crux/main/install.sh | sh
```

Or with uv: `uv tool install crux-cli && crux setup`

[:octicons-arrow-right-24: Full installation guide](getting-started/installation.md)

---

## The full lifecycle

**Curate** :material-arrow-right: **Scope** :material-arrow-right: **Secure** :material-arrow-right: **Execute** :material-arrow-right: **Monitor**

| Stage | What Crux does | Command |
|-------|---------------|---------|
| **Curate** | Build a personal registry of MCPs and skills from any source | `crux add`, `crux search` |
| **Scope** | Each project declares exactly what it needs in `crux.json` | `crux init`, `crux install` |
| **Secure** | Credentials in OS keychain, fetched at runtime by launcher scripts | `crux secret set` |
| **Execute** | Run agents in sandboxes with only the declared MCPs | `crux run` |
| **Monitor** | Health-check MCP servers, diagnose and auto-fix issues | `crux status`, `crux doctor` |
