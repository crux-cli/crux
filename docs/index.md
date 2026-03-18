---
hide:
  - navigation
  - toc
---

# Crux

## The package manager for AI agent tooling

---

### Your research agent just called the trading API.

You didn't mean for that to happen. But all 30 of your MCP servers are globally visible to every agent. The wiki bot has filesystem write access. The coding assistant sees your home automation MCPs. And the API key for your trading account? It's sitting in a `.env` file that was committed to git three weeks ago.

**This is what MCP management looks like without Crux.**

The ecosystem has 10,000+ MCP servers and 60,000+ skills. But there's no way to manage them. Every project gets the same 50 MCPs dumped into its context. Setting up a new project means copy-pasting `.mcp.json` by hand. Credentials leak. Agents hallucinate tool calls to services they shouldn't know exist.

---

### Scenario 1: Set up a new project in 30 seconds

You're building a homelab assistant. It needs wiki access and filesystem tools — nothing else.

```bash
# Add tools to your personal registry (you do this once, ever)
crux add mcp filesystem --npx @modelcontextprotocol/server-filesystem
crux add mcp wikijs --github jaalbin24/wikijs-mcp-server
crux add skill autoresearch --github user/autoresearch-skill

# Store the wiki API key in your OS keychain — not in a file
crux secret set wikijs WIKIJS_API_KEY

# Create the project — it gets exactly what it needs
crux init homelab-assistant && cd homelab-assistant
crux install wikijs filesystem autoresearch
```

Done. Your project has a `crux.json` (committed to git) and a generated `.mcp.json` (gitignored). The wiki MCP launches via a script that fetches the API key from your keychain at runtime. No secret ever touches a file.

When a teammate clones the repo, they run `crux install` and get the same setup — with their own credentials from their own keychain. Like `npm install`, but for AI tooling.

---

### Scenario 2: Run an agent with controlled access

Your research agent should access the wiki and a research skill. Not the filesystem. Not GitHub. Definitely not the trading API.

```bash
crux run "Find papers on MCP security and update the wiki" \
  --mcps wikijs \
  --skills autoresearch
```

Crux creates an isolated sandbox with only the declared tools. Before execution, it runs pre-flight checks — every MCP exists, every secret is stored, every source is built. If something's wrong, you get the exact command to fix it. No wasted agent time on mid-run failures.

---

### Scenario 3: A teammate joins your project

They clone the repo. They see `crux.json` listing the MCPs and skills the project needs. They run:

```bash
crux install
crux secret set wikijs WIKIJS_API_KEY   # their own key
crux status                              # verify everything works
```

No Slack message asking "which MCPs does this project use?" No digging through config files. No 30-minute setup. The manifest is the documentation.

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

**Registry** — Add MCPs and skills once from npm, PyPI, GitHub, or local sources. One source of truth across all your projects. No more copy-pasting `.mcp.json`.

**Secrets** — API keys live in your OS keychain (macOS Keychain, Linux Secret Service, or age-encrypted vault). Generated launcher scripts fetch them at runtime. Nothing is ever written to disk.

**Sync engine** — `crux sync` reads your project's `crux.json` and generates the `.mcp.json` that Claude Code expects, with only the tools you declared. Each project gets its own scoped config.

---

## Why scoping matters

**An agent with 5 relevant tools outperforms one drowning in 50.**

This isn't just a security claim — it's a quality lever. When you reduce the tools in an agent's context window:

- **Outputs improve** — the model focuses on tools that matter for the task
- **Hallucinated tool calls drop** — no accidental calls to the trading API from your wiki bot
- **Security tightens** — each agent's blast radius is limited to what it actually needs
- **Execution speeds up** — smaller tool lists mean faster MCP initialization

---

## Install

```bash
curl -LsSf https://raw.githubusercontent.com/crux-cli/crux/main/install.sh | sh
```

Or with uv: `uv tool install crux-cli && crux setup`

[:octicons-arrow-right-24: Full installation guide](getting-started/installation.md)

---

## The full lifecycle

| What you do | How Crux helps | Command |
|-------------|---------------|---------|
| Find an MCP you want to use | Search the official registry, add from npm/PyPI/GitHub | `crux search`, `crux add` |
| Start a new project | Declare which MCPs and skills it needs | `crux init`, `crux install` |
| Store API keys securely | OS keychain — never in config files | `crux secret set` |
| Run an agent with controlled access | Isolated sandbox with only declared tools | `crux run` |
| Check if everything is healthy | Probe MCP servers, diagnose issues | `crux status`, `crux doctor` |

<div class="grid cards" markdown>

-   [:octicons-arrow-right-24: Getting Started](getting-started/installation.md)
-   [:octicons-arrow-right-24: CLI Reference](cli/index.md)
-   [:octicons-arrow-right-24: Guides](guides/index.md)
-   [:octicons-arrow-right-24: API Reference](api/index.md)

</div>
