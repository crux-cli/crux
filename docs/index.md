---
hide:
  - navigation
  - toc
---

# Crux

## Manage your MCP servers and skills like packages

Crux is a CLI tool that brings package-management to your Claude Code workflows. You add MCP servers and skills to a local registry, declare which ones each project needs, and Crux generates the config — with credentials stored in your OS keychain, not in files.

It runs on **your machine** (macOS or Linux), works with **Claude Code**, and installs in one command.

```bash
curl -LsSf https://raw.githubusercontent.com/crux-cli/crux/main/install.sh | sh
```

---

## What Crux does for you

### Stop editing `.mcp.json` by hand

Every Claude Code project needs a `.mcp.json` listing its MCP servers. Without Crux, you maintain these files manually — copy-pasting entries between projects, updating each one when you add a new tool, hoping the JSON stays valid.

With Crux, you build a personal registry of all your MCP servers and skills. Each project declares what it needs in a simple manifest. Crux generates the rest.

```bash
# Add tools to your registry once — use them in any project
crux add mcp filesystem --npx @modelcontextprotocol/server-filesystem
crux add mcp github --npx @modelcontextprotocol/server-github
crux add mcp wikijs --github jaalbin24/wikijs-mcp-server
crux add skill autoresearch --github user/autoresearch-skill

# Search the official MCP registry to discover new tools
crux search "database"
```

Your registry lives at `~/.crux/registry.json` — one source of truth for every tool you use across all your projects.

---

### Keep API keys out of your config files

48% of MCP servers recommend storing API keys in plaintext config files. Keys end up in `.env` files, committed to git, leaked in logs.

Crux stores every credential in your **OS keychain** — macOS Keychain, Linux Secret Service, or an age-encrypted vault. When an MCP server needs an API key, Crux generates a launcher script that fetches it from the keychain at runtime. The secret never exists in any file on disk.

```bash
# Store credentials securely — prompted, never echoed
crux secret set wikijs WIKIJS_API_KEY
crux secret set github GITHUB_TOKEN

# See what's stored (values always masked)
crux secret list
```

---

### Give each project exactly the tools it needs

A coding assistant doesn't need your home automation MCPs. A wiki bot doesn't need filesystem write access. But without scoping, every agent sees every tool — leading to worse outputs, hallucinated tool calls, and unnecessary security exposure.

Crux lets each project declare its own subset of tools:

```bash
# Start a new project
crux init homelab-assistant && cd homelab-assistant

# Install only what this project needs
crux install wikijs filesystem autoresearch

# Check that everything is working
crux status
```

This creates a `crux.json` — your project's tool manifest:

```json
{
  "name": "homelab-assistant",
  "mcps": ["wikijs", "filesystem"],
  "skills": ["autoresearch"]
}
```

Commit `crux.json` to git. The generated `.mcp.json` is gitignored — it's a local artifact that Crux rebuilds with `crux sync`.

**Why this matters for quality:** an agent with 5 relevant tools consistently outperforms one with 50 irrelevant ones. Less noise in the context window means better outputs and fewer hallucinated tool calls.

---

### Run agents with controlled tool access

Sometimes you want to run an agent with a specific, limited set of tools — without setting up a full project. Crux sandboxes let you do exactly that.

```bash
# This agent can only access wikijs — nothing else
crux run "Summarize the latest MCP security research and update the wiki" \
  --mcps wikijs \
  --skills autoresearch
```

Before execution, Crux runs **pre-flight checks**: every MCP exists in your registry, every required secret is stored, every GitHub source is cloned and built. If something is missing, you get the exact command to fix it — before wasting agent time on a mid-run failure.

Save run configurations as reusable manifests:

```json title="tasks/weekly-research.json"
{
  "name": "weekly-research",
  "task": "Search for latest MCP security papers and update the wiki",
  "mcps": ["wikijs"],
  "skills": ["autoresearch"],
  "timeout_minutes": 30
}
```

```bash
crux run --file tasks/weekly-research.json
```

---

### Know when something is broken

MCP servers fail silently. A config typo, a missing dependency, an expired token — you don't find out until your agent fails mid-task.

```bash
# Probe every MCP server in your project via JSON-RPC handshake
crux status

# Full environment health check with auto-fix
crux doctor
```

`crux status` actually starts each MCP server, performs the protocol handshake, and reports whether it responded — along with its protocol version and available tools. `crux doctor` checks your entire Crux environment (directories, config, dependencies, registry integrity) and fixes what it can automatically.

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

---

## Security

Crux takes an opinionated stance: **there is no insecure-but-easier path.**

- Secrets never appear in any file on disk — only in your OS keystore
- Launcher scripts contain keystore lookup commands, not credential values
- Generated `.mcp.json` never contains secrets
- Each sandbox gets only the MCPs explicitly declared for that run
- Path traversal protections on all file operations

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
