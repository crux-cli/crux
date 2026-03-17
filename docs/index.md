---
hide:
  - navigation
---

# Crux

**Your AI agents have access to 10,000+ MCP servers. They should only see five.**

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } __Install in seconds__

    ---

    One command to install. Works on macOS and Linux.

    [:octicons-arrow-right-24: Installation](getting-started/installation.md)

-   :material-rocket-launch:{ .lg .middle } __Get started in 30 seconds__

    ---

    Add MCPs, create a project, install tools — done.

    [:octicons-arrow-right-24: Quick Start](getting-started/quickstart.md)

-   :material-shield-lock:{ .lg .middle } __Secure by default__

    ---

    Secrets in your OS keychain. Never in files. No insecure-but-easier path.

    [:octicons-arrow-right-24: Secrets Management](guides/secrets.md)

-   :material-cube-outline:{ .lg .middle } __Sandboxed execution__

    ---

    Run agents with exactly the MCPs they need. Nothing more.

    [:octicons-arrow-right-24: Sandbox Guide](guides/sandbox.md)

</div>

---

Crux is the **control plane** that sits between your MCP ecosystem and your AI agents. One registry. Per-project scoping. Secrets in your OS keychain — never in files. Sandboxed execution. Full lifecycle management for every tool your agents touch.

> Think `package.json` for AI tooling — declare what each project needs, and Crux handles the rest.

```bash
# Add MCPs to your personal registry (once, ever)
crux add mcp filesystem --npx @modelcontextprotocol/server-filesystem
crux add mcp wikijs --github jaalbin24/wikijs-mcp-server

# Store credentials in your OS keychain — not in files
crux secret set wikijs WIKIJS_API_KEY

# Create a project — it gets exactly what it needs
crux init homelab-assistant && cd homelab-assistant
crux install wikijs filesystem
crux status
```

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
