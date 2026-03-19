# CLI Reorganization & Unified Authentication Design

**Date:** 2026-03-19
**Status:** Draft

## Problem Statement

Crux's CLI has grown organically, resulting in:

1. **Flat command namespace** — commands like `add`, `remove`, `list`, `search`, `init`, `install`, `sync`, `status`, `secret`, `run` sit at the top level with no grouping by resource type.
2. **Fragmented authentication** — auth is spread across `crux secret set/get/list/delete`, `crux setup <mcp>`, `--keychain` flag on `crux add`, `check_cmd`/`fix_cmd` in registry metadata, and auth checks in `crux doctor`. There is no single command that answers "authenticate this MCP."
3. **`doctor` overreach** — `crux doctor` checks both crux environment health AND MCP auth/secrets consistency. Expired tokens or missing API keys are not crux's fault — doctor should only diagnose crux itself.
4. **No HTTP transport support** — crux only manages stdio-based (subprocess) MCP servers. The MCP spec's OAuth 2.1 flow, Bearer tokens, and the entire HTTP Streamable transport are unsupported.
5. **`setup` confusion** — `crux setup` does two unrelated things: first-time crux init AND running an MCP's setup_cmd.

## Design Goals

- **Resource-first namespacing**: group commands by what they act on (`mcp`, `skill`, `project`, `task`)
- **Unified auth surface**: `crux mcp auth <name>` is the single command for all MCP authentication
- **Clean separation of concerns**: `doctor` only checks crux health; auth state lives under `mcp auth`
- **100% MCP auth coverage**: support every auth method in the MCP ecosystem
- **No backward compatibility shims**: clean break (no existing users)

---

## 1. New CLI Command Tree

### 1.1 Top-Level Commands

```
crux init               # First-time crux environment setup
crux doctor             # Crux-internal health check only
crux version [--check]  # Show version / check for updates
```

### 1.2 `crux mcp` — MCP Server Management

```
crux mcp add <name> [--npx|--uvx|--github|--local <src>]
                     [--command <cmd>] [--args <args>] [--tags <tags>]
                     [--build-cmd <cmd>] [--setup-cmd <cmd>]
                     [--keychain <var1,var2>]
crux mcp remove <name>
crux mcp list [--json]
crux mcp search <query> [--limit N] [--add]
crux mcp upgrade [names...] [--dry-run]
crux mcp auth <name>        # Detect auth method, run appropriate flow
crux mcp auth [--all]       # No name = show MCPs needing auth; --all = auth everything
crux mcp status             # Registry-wide: probe all registered MCPs
```

### 1.3 `crux skill` — Skill Management

```
crux skill add <name> [--github|--local <src>] [--tags <tags>] [--build-cmd <cmd>]
crux skill remove <name>
crux skill list [--json]
```

### 1.4 `crux project` — Project Management

```
crux project create [name] [--mcp <names>] [--skill <names>]
crux project install <name> [name...]
crux project uninstall <name> [name...]
crux project sync [--all]
crux project status [--all]     # MCPs (with auth state) + skills for project(s)
```

### 1.5 `crux task` — Sandbox & Agent Execution

```
crux task run <prompt> [--mcp <names>] [--file run.json] [--keep] [--no-stream]
crux task init [name]           # Scaffold run.json
crux task list                  # Past runs
crux task clean [--force]       # Cleanup sandboxes
```

### 1.6 Command Mapping (Old to New)

| Old Command | New Command | Notes |
|---|---|---|
| `crux setup` | `crux init` | First-time crux env setup only |
| `crux setup <mcp>` | Absorbed into `crux mcp add --setup-cmd` | Re-run via `crux mcp auth <name>` |
| `crux doctor` | `crux doctor` | Loses auth/secrets checks |
| `crux add mcp/skill` | `crux mcp add` / `crux skill add` | Resource-first |
| `crux remove` | `crux mcp remove` / `crux skill remove` | Split by type |
| `crux list` | `crux mcp list` / `crux skill list` | Split by type |
| `crux search` | `crux mcp search` | MCP-only (skills have no remote registry) |
| `crux upgrade` | `crux mcp upgrade` | MCP-only (skills follow same path) |
| `crux init` | `crux project create` | Renamed for clarity |
| `crux install` | `crux project install` | Under project namespace |
| `crux uninstall` | `crux project uninstall` | Under project namespace |
| `crux sync` | `crux project sync` | Under project namespace |
| `crux status` | `crux project status` | Under project namespace |
| `crux secret set/get/list/delete` | `crux mcp auth` | Unified auth surface |
| `crux run` | `crux task run` | Under task namespace |
| `crux run init/list/clean` | `crux task init/list/clean` | Under task namespace |

---

## 2. Unified Authentication System

### 2.1 Auth Types

Every MCP in the registry declares an `auth` block describing what authentication it needs. The unified `crux mcp auth` command reads this metadata and runs the appropriate flow.

| Auth Type | Description | Storage | New? |
|---|---|---|---|
| `keychain` | Environment variables stored in OS keychain | OS keychain | Existing |
| `external-cli` | External tool validates auth (e.g., `gh auth status`) | Managed by external tool | Existing (renamed from ad-hoc `check_cmd`) |
| `setup-cmd` | One-time interactive setup command | Varies | Existing |
| `bearer` | Static Bearer token / API key for HTTP header | OS keychain | **New** |
| `oauth` | OAuth 2.1 Authorization Code + PKCE | Token store (keychain + metadata) | **New** |
| `oauth-client-credentials` | OAuth 2.1 Client Credentials (machine-to-machine) | Token store | **New** |

### 2.2 Registry Auth Metadata Schema

```json
{
  "auth": {
    "type": "keychain | external-cli | setup-cmd | bearer | oauth | oauth-client-credentials",

    "env_vars": ["VAR1", "VAR2"],

    "check_cmd": ["gh", "auth", "status"],
    "fix_cmd": ["gh", "auth", "login"],
    "fix_description": "Authenticate with GitHub CLI",

    "setup_cmd": ["foo", "auth", "init"],

    "header_name": "Authorization",
    "header_prefix": "Bearer",
    "keychain_key": "API_TOKEN",

    "authorization_url": "https://example.com/oauth/authorize",
    "token_url": "https://example.com/oauth/token",
    "client_id": "crux-cli",
    "scopes": ["read", "write"],
    "discovery_url": "https://example.com/.well-known/oauth-authorization-server",

    "resource_url": "https://example.com/mcp"
  }
}
```

Fields are conditional on `type` — only relevant fields are present for each auth type.

### 2.3 `crux mcp auth` Behavior

#### `crux mcp auth <name>` — Authenticate a Single MCP

1. Look up MCP in registry, read `auth.type`
2. Dispatch to the appropriate auth handler:

**`keychain`:**
- For each `env_var` in `auth.env_vars`, prompt user for value (password-masked input)
- Store via `SecretsBackend.set(mcp_name, var, value)`
- Run `crux project sync` to regenerate launchers

**`external-cli`:**
- Run `auth.check_cmd` — if exit 0, print "Already authenticated"
- If exit != 0, run `auth.fix_cmd` (or print `fix_description`)
- Re-check after fix

**`setup-cmd`:**
- Run `auth.setup_cmd` interactively (inherit stdin/stdout)
- Report success/failure

**`bearer`:**
- Prompt for token (password-masked)
- Store in keychain under `crux.<mcp-name>` / `auth.keychain_key`
- Used by HTTP transport: injected as `auth.header_prefix <token>` in `auth.header_name` header

**`oauth`:**
- Discover authorization server (via `discovery_url` or `auth.authorization_url` + `auth.token_url`)
- Generate PKCE code verifier + challenge (S256)
- Start local HTTP server on ephemeral port for redirect
- Open browser to authorization URL with `response_type=code`, `client_id`, `redirect_uri`, `scope`, `code_challenge`, `resource` parameters
- Receive authorization code at redirect
- Exchange code for access token + refresh token at token URL
- Store tokens in keychain: `crux.<mcp-name>/access_token`, `crux.<mcp-name>/refresh_token`
- Store token metadata (expiry, scopes, issuer) in `~/.crux/tokens.json`

**`oauth-client-credentials`:**
- Read `client_id` and prompt for `client_secret` (or read from keychain if already stored)
- POST to `token_url` with `grant_type=client_credentials`, `scope`, `resource`
- Store access token in keychain, metadata in `~/.crux/tokens.json`

#### `crux mcp auth` (No Name) — Show Auth Status

Display a table of all registered MCPs that have auth requirements:

```
MCPs requiring authentication:

  Name          Auth Type       Status
  wikijs-mcp    keychain        Missing: WIKIJS_API_KEY
  github-mcp    external-cli    Not authenticated
  slack-mcp     oauth           Token expires in 2h
  linear-mcp    bearer          Authenticated
  jira-mcp      oauth           Refresh needed

Run: crux mcp auth <name>  to authenticate
     crux mcp auth --all   to authenticate all
```

Status is determined by:
- `keychain`: check secrets index for all required `env_vars`
- `external-cli`: run `check_cmd`, check exit code
- `setup-cmd`: no programmatic check — show "Run setup to configure"
- `bearer`: check keychain for stored token
- `oauth` / `oauth-client-credentials`: check `tokens.json` for valid (non-expired) access token; if expired but refresh token exists, show "Refresh needed"

#### `crux mcp auth --all` — Authenticate Everything

Iterate all MCPs needing auth, run the appropriate flow for each sequentially. Skip MCPs that are already authenticated. Print summary at end.

### 2.4 Token Refresh

For `oauth` and `oauth-client-credentials` auth types:

- **Automatic refresh at runtime**: When `crux project sync` generates launcher scripts for HTTP-transport MCPs, the launcher includes a token-refresh check. If the access token is expired but a refresh token exists, it exchanges the refresh token for a new access token before starting the MCP.
- **Manual refresh**: `crux mcp auth <name>` detects expired tokens and re-runs the appropriate flow.
- **Token metadata** stored in `~/.crux/tokens.json`:

```json
{
  "slack-mcp": {
    "auth_type": "oauth",
    "access_token_key": "access_token",
    "refresh_token_key": "refresh_token",
    "expires_at": "2026-03-19T14:30:00Z",
    "scopes": ["read", "write"],
    "token_url": "https://slack.com/api/oauth.v2.access",
    "client_id": "crux-cli"
  }
}
```

Token values stay in the OS keychain — `tokens.json` only stores metadata (expiry, scopes, URLs for refresh).

### 2.5 HTTP Transport Support

For MCPs that use HTTP Streamable transport (not stdio), crux needs to:

1. **Store the MCP endpoint URL** in registry metadata (`"url": "https://example.com/mcp"`)
2. **Inject auth headers** when generating `.mcp.json` — Claude Code's `.mcp.json` supports `"type": "streamable-http"` entries with `"url"` and `"headers"` fields
3. **Token refresh** before sync — ensure access tokens are fresh when generating config

New `.mcp.json` entry format for HTTP MCPs:

```json
{
  "mcpServers": {
    "slack-mcp": {
      "type": "streamable-http",
      "url": "https://slack.com/mcp",
      "headers": {
        "Authorization": "Bearer sk-..."
      }
    }
  }
}
```

For HTTP MCPs with OAuth, `crux project sync` will:
1. Check `tokens.json` for token expiry
2. If expired, attempt refresh using stored refresh token
3. Read access token from keychain
4. Embed in `.mcp.json` headers

This means `.mcp.json` contains live tokens for HTTP MCPs. Since `.mcp.json` is already gitignored and only generated locally, this is acceptable. The alternative (a launcher-style proxy) adds complexity with no security benefit since the token ends up in the MCP process either way.

---

## 3. Doctor Scope Reduction

### Current Doctor Checks (health.py `run_doctor_checks`)

| Check | Keep in Doctor? |
|---|---|
| Python version | Yes |
| `uv` installed | Yes |
| `git` installed | Yes |
| `node` installed | Yes |
| `npm` installed | Yes |
| `claude` installed | Yes |
| Directory structure | Yes |
| Registry JSON valid | Yes |
| MCP sources present | Yes |
| Build artifacts present | Yes |
| **Secrets consistency** | **No — move to `crux mcp auth`** |
| crux in PATH | Yes |

The `check_secrets_consistency` function in `health.py` and its invocation in `run_doctor_checks` will be removed. Auth state is shown by `crux mcp auth` (no args) and `crux project status`.

---

## 4. Project Status Enhancement

`crux project status` will show both MCPs and skills with auth state:

```
Project: my-app (3 MCPs, 2 skills)

  MCP Servers:
  Name          Status       Tools  Auth           Detail
  github-mcp    connected    15     Authenticated  GitHub MCP Server 1.2
  slack-mcp     connected    8      Expires 2h     Slack MCP v3.1
  wikijs-mcp    auth_required -     Missing key    WIKIJS_API_KEY not set

  Skills:
  Name          Source       Installed
  code-review   github       Yes
  refactor      local        Yes
```

The auth column pulls from the same logic as `crux mcp auth` (no args) — secrets index check, token expiry check, external-cli check.

---

## 5. File-Level Change Plan

### 5.1 CLI Entry Point

**File: `src/crux_cli/cli/main.py`**

Complete rewrite. Replace flat subparsers with nested subparser groups:

```python
parser = argparse.ArgumentParser(description="Crux — Agentic AI control plane")
subparsers = parser.add_subparsers(dest="command", required=True)

# Top-level
subparsers.add_parser("init", ...)      # crux init
subparsers.add_parser("doctor", ...)    # crux doctor
subparsers.add_parser("version", ...)   # crux version

# crux mcp ...
mcp_parser = subparsers.add_parser("mcp", ...)
mcp_sub = mcp_parser.add_subparsers(dest="mcp_command", required=True)
mcp_sub.add_parser("add", ...)
mcp_sub.add_parser("remove", ...)
mcp_sub.add_parser("list", ...)
mcp_sub.add_parser("search", ...)
mcp_sub.add_parser("upgrade", ...)
mcp_sub.add_parser("auth", ...)
mcp_sub.add_parser("status", ...)

# crux skill ...
skill_parser = subparsers.add_parser("skill", ...)
skill_sub = skill_parser.add_subparsers(dest="skill_command", required=True)
skill_sub.add_parser("add", ...)
skill_sub.add_parser("remove", ...)
skill_sub.add_parser("list", ...)

# crux project ...
project_parser = subparsers.add_parser("project", ...)
project_sub = project_parser.add_subparsers(dest="project_command", required=True)
project_sub.add_parser("create", ...)
project_sub.add_parser("install", ...)
project_sub.add_parser("uninstall", ...)
project_sub.add_parser("sync", ...)
project_sub.add_parser("status", ...)

# crux task ...
task_parser = subparsers.add_parser("task", ...)
task_sub = task_parser.add_subparsers(dest="task_command", required=True)
task_sub.add_parser("run", ...)
task_sub.add_parser("init", ...)
task_sub.add_parser("list", ...)
task_sub.add_parser("clean", ...)
```

### 5.2 Command Handler Files

**Split and rename command files to match namespaces:**

| Old File | New File(s) | Contents |
|---|---|---|
| `commands/registry.py` | `commands/mcp.py` | `cmd_mcp_add`, `cmd_mcp_remove`, `cmd_mcp_list`, `cmd_mcp_search`, `cmd_mcp_upgrade`, `cmd_mcp_status` |
| `commands/secrets.py` | `commands/mcp.py` (merged) | `cmd_mcp_auth` absorbs secret set/get/list/delete |
| `commands/project.py` | `commands/project.py` | `cmd_project_create`, `cmd_project_install`, `cmd_project_uninstall`, `cmd_project_sync`, `cmd_project_status` |
| `commands/sandbox.py` | `commands/task.py` | `cmd_task_run`, `cmd_task_init`, `cmd_task_list`, `cmd_task_clean` |
| `commands/doctor.py` | `commands/doctor.py` | `cmd_doctor` (reduced), `cmd_init` (crux init) |
| `commands/version.py` | `commands/version.py` | Unchanged |
| — | `commands/skill.py` (new) | `cmd_skill_add`, `cmd_skill_remove`, `cmd_skill_list` |

**New file: `commands/mcp.py`**

This is the largest new file. It combines:
- MCP registry operations (from old `registry.py`): add, remove, list, search, upgrade
- MCP status (from old `project.py` `cmd_status` global view)
- Unified auth (new): replaces all of `secrets.py` CLI + `setup <mcp>` from `doctor.py`

The `cmd_mcp_auth` function:
```python
def cmd_mcp_auth(args):
    name = getattr(args, 'name', None)
    if name:
        _auth_single(name)
    elif getattr(args, 'all', False):
        _auth_all()
    else:
        _auth_status()  # show table
```

**New file: `commands/skill.py`**

Extract skill-specific logic from old `registry.py`:
- `cmd_skill_add` — skill registration (was the `elif entry_type == "skill"` branch of `cmd_add`)
- `cmd_skill_remove` — skill removal (was handled in `cmd_remove`)
- `cmd_skill_list` — skill listing (was part of `cmd_list`)

### 5.3 Core Module Changes

**`secrets.py`** — No changes to the backend system. `SecretsBackend`, `MacOSKeychainBackend`, `LinuxSecretServiceBackend`, `AgeEncryptedBackend`, and the factory function all stay as-is. The secrets module is a storage layer — only the CLI surface on top changes.

**`health.py`** — Changes:
- Remove `check_secrets_consistency` function
- Remove secrets-related logic from `run_doctor_checks`
- Keep all other checks (python version, tools, directories, registry, sources, build artifacts)

**`preflight.py`** — Update fix hint messages:
- `"Fix: crux secret set {name} {var} <value>"` → `"Fix: crux mcp auth {name}"`
- `"Fix: crux add mcp {name} --npx <package>"` → `"Fix: crux mcp add {name} --npx <package>"`
- `"Fix: crux add skill {name} --github <repo>"` → `"Fix: crux skill add {name} --github <repo>"`

**`sync.py`** — Add HTTP transport support:
- New function `_build_http_server_entry` for HTTP MCPs — generates `type: streamable-http` entries with URL and auth headers
- Modify `_build_server_entry` to dispatch to HTTP or stdio path based on MCP type
- Token refresh logic before embedding tokens in `.mcp.json`

**New module: `auth.py`** — Unified auth orchestration:
- `auth_single(mcp_name, registry)` — dispatches to the right auth flow based on `auth.type`
- `auth_status(registry)` — returns list of auth status dicts for display
- `auth_all(registry)` — iterates MCPs needing auth
- `run_oauth_flow(auth_config)` — OAuth 2.1 Authorization Code + PKCE
- `run_client_credentials_flow(auth_config)` — OAuth 2.1 Client Credentials
- `refresh_token(mcp_name)` — refresh expired OAuth tokens
- `load_token_metadata()` / `save_token_metadata()` — manage `~/.crux/tokens.json`

**New module: `oauth.py`** — OAuth 2.1 implementation:
- PKCE code verifier/challenge generation (S256)
- Local redirect HTTP server (ephemeral port)
- Browser launch for authorization
- Token exchange
- Token refresh
- Authorization server discovery (RFC 9728, RFC 8414, OIDC Discovery)

**`paths.py`** — Add new path:
- `tokens_path()` → `~/.crux/tokens.json`

### 5.4 New Files Summary

| File | Purpose |
|---|---|
| `src/crux_cli/auth.py` | Unified auth orchestration (dispatches by auth type) |
| `src/crux_cli/oauth.py` | OAuth 2.1 implementation (PKCE, token exchange, refresh, discovery) |
| `src/crux_cli/cli/commands/mcp.py` | All `crux mcp *` command handlers |
| `src/crux_cli/cli/commands/skill.py` | All `crux skill *` command handlers |
| `src/crux_cli/cli/commands/task.py` | All `crux task *` command handlers (renamed from sandbox.py) |

### 5.5 Deleted Files

| File | Reason |
|---|---|
| `src/crux_cli/cli/commands/secrets.py` | Absorbed into `commands/mcp.py` via `cmd_mcp_auth` |
| `src/crux_cli/cli/commands/sandbox.py` | Renamed to `commands/task.py` |

### 5.6 Files With Edits Only

| File | Changes |
|---|---|
| `src/crux_cli/cli/main.py` | Complete rewrite of argument parser |
| `src/crux_cli/cli/commands/doctor.py` | Remove `cmd_setup` MCP branch; add `cmd_init`; reduce `cmd_doctor` scope |
| `src/crux_cli/cli/commands/project.py` | Rename functions (`cmd_init` → `cmd_project_create`, etc.); add `--mcp`/`--skill` to create; enhance status with auth + skills |
| `src/crux_cli/health.py` | Remove `check_secrets_consistency` and its call from `run_doctor_checks` |
| `src/crux_cli/preflight.py` | Update fix hint messages to new command names |
| `src/crux_cli/sync.py` | Add HTTP transport support (`_build_http_server_entry`, token refresh before sync) |
| `src/crux_cli/paths.py` | Add `tokens_path()` |
| `pyproject.toml` | Entry point unchanged (`crux = crux_cli.cli.main:main`); may need new dependency for OAuth (`authlib` or pure implementation) |

---

## 6. Test Changes

### 6.1 Integration Tests (tests/integration/)

Integration tests invoke the CLI as subprocesses with actual command strings. Every test file needs updating:

| Old Test File | New Test File | Changes |
|---|---|---|
| `test_cli_init.py` | `test_cli_project_create.py` | `crux init` → `crux project create`; add tests for `--mcp`/`--skill` flags |
| `test_cli_add_remove.py` | `test_cli_mcp_add_remove.py` + `test_cli_skill_add_remove.py` | Split MCP and skill tests; `crux add mcp` → `crux mcp add`; `crux remove` → `crux mcp remove` / `crux skill remove` |
| `test_cli_list.py` | `test_cli_mcp_list.py` + `test_cli_skill_list.py` | Split; `crux list` → `crux mcp list` / `crux skill list` |
| `test_cli_secret.py` | `test_cli_mcp_auth.py` | `crux secret set/get/list/delete` → `crux mcp auth` flows; add tests for auth status display, `--all` flag |
| `test_cli_doctor.py` | `test_cli_doctor.py` | Remove auth/secrets assertions from doctor output; add `crux init` tests (was `crux setup`) |
| `test_cli_sync.py` | `test_cli_project_sync.py` | `crux sync` → `crux project sync` |
| `test_cli_run.py` | `test_cli_task.py` | `crux run init` → `crux task init`; `crux run list` → `crux task list`; etc. |

**New integration tests:**
| File | Tests |
|---|---|
| `test_cli_mcp_auth.py` | Keychain auth flow, external-cli auth flow, setup-cmd flow, bearer token flow, auth status display, `--all` flag |
| `test_cli_mcp_status.py` | Global MCP health probing via `crux mcp status` |
| `test_cli_project_status.py` | Project status with auth indicators and skills |

### 6.2 Unit Tests (tests/unit/)

| Test File | Changes |
|---|---|
| `test_health.py` | Remove `test_check_secrets_consistency*` tests; keep all other health check tests |
| `test_health_extended.py` | Remove secrets-related assertions |
| `test_preflight.py` | Update expected fix hint messages to new command names |
| `test_sync.py` | Add tests for HTTP transport entry generation (`_build_http_server_entry`) |
| `test_setup.py` | Unchanged (tests `run_setup` core logic, not CLI command name) |
| `test_sandbox.py` | Unchanged (tests core sandbox logic, not CLI) |
| `test_sandbox_extended.py` | Unchanged |

**New unit tests:**
| File | Tests |
|---|---|
| `test_auth.py` | `auth_single` dispatch logic, `auth_status` computation, token metadata load/save |
| `test_oauth.py` | PKCE generation, token exchange request building, token refresh, discovery URL resolution |
| `test_tokens.py` | Token metadata file I/O, expiry checks, refresh token presence detection |

---

## 7. Documentation Changes

### 7.1 CLI Reference Docs (docs/cli/)

Complete restructure to match new command tree:

**Delete:**
- `docs/cli/setup.md` (→ merged into `init.md`)
- `docs/cli/add.md` (→ `mcp-add.md` + `skill-add.md`)
- `docs/cli/remove.md` (→ `mcp-remove.md` + `skill-remove.md`)
- `docs/cli/list.md` (→ `mcp-list.md` + `skill-list.md`)
- `docs/cli/search.md` (→ `mcp-search.md`)
- `docs/cli/upgrade.md` (→ `mcp-upgrade.md`)
- `docs/cli/init.md` (→ `project-create.md`)
- `docs/cli/install.md` (→ `project-install.md`)
- `docs/cli/uninstall.md` (→ `project-uninstall.md`)
- `docs/cli/sync.md` (→ `project-sync.md`)
- `docs/cli/status.md` (→ `project-status.md`)
- `docs/cli/secret.md` (→ `mcp-auth.md`)
- `docs/cli/run.md` (→ `task-run.md`)

**Create:**

| File | Content |
|---|---|
| `docs/cli/index.md` | Rewritten with new command tree grouped by namespace |
| `docs/cli/init.md` | `crux init` (first-time setup) |
| `docs/cli/doctor.md` | Updated — remove auth checks from scope |
| `docs/cli/mcp-add.md` | `crux mcp add` |
| `docs/cli/mcp-remove.md` | `crux mcp remove` |
| `docs/cli/mcp-list.md` | `crux mcp list` |
| `docs/cli/mcp-search.md` | `crux mcp search` |
| `docs/cli/mcp-upgrade.md` | `crux mcp upgrade` |
| `docs/cli/mcp-auth.md` | `crux mcp auth` — full auth reference with all auth types |
| `docs/cli/mcp-status.md` | `crux mcp status` |
| `docs/cli/skill-add.md` | `crux skill add` |
| `docs/cli/skill-remove.md` | `crux skill remove` |
| `docs/cli/skill-list.md` | `crux skill list` |
| `docs/cli/project-create.md` | `crux project create` |
| `docs/cli/project-install.md` | `crux project install` |
| `docs/cli/project-uninstall.md` | `crux project uninstall` |
| `docs/cli/project-sync.md` | `crux project sync` |
| `docs/cli/project-status.md` | `crux project status` |
| `docs/cli/task-run.md` | `crux task run` |
| `docs/cli/task-init.md` | `crux task init` |
| `docs/cli/task-list.md` | `crux task list` |
| `docs/cli/task-clean.md` | `crux task clean` |

### 7.2 Guide Docs (docs/guides/)

| File | Changes |
|---|---|
| `docs/guides/registry.md` | Update all command references: `crux add` → `crux mcp add`, etc. |
| `docs/guides/projects.md` | Update: `crux init` → `crux project create`, `crux install` → `crux project install`, `crux secret set` → `crux mcp auth`, etc. |
| `docs/guides/sandbox.md` | Update: `crux run` → `crux task run`, `crux secret` → `crux mcp auth` |
| `docs/guides/health.md` | Update: `crux doctor` scope reduction, `crux status` → `crux project status` |
| `docs/guides/secrets.md` | Major rewrite → rename to `docs/guides/authentication.md`. Cover all auth types, unified `crux mcp auth` flow, token refresh, OAuth setup. |

### 7.3 Getting Started Docs (docs/getting-started/)

Update any command references to use new names.

---

## 8. Skill File Changes

**File: `src/crux_cli/data/skills/crux/SKILL.md`**

Complete rewrite to reflect new command tree:

```markdown
# Crux — AI Agent Control Plane

Crux is a CLI tool for managing MCP servers, skills, and agent tasks.

## Available Commands

### MCP Servers
- `crux mcp search <query>` — Search the MCP Registry
- `crux mcp add <name> --npx <pkg>` — Register an MCP server
- `crux mcp remove <name>` — Unregister an MCP server
- `crux mcp list` — List registered MCP servers
- `crux mcp upgrade` — Update cloned MCP repos
- `crux mcp auth <name>` — Authenticate an MCP server
- `crux mcp auth` — Show authentication status for all MCPs
- `crux mcp status` — Probe all registered MCP servers

### Skills
- `crux skill add <name> --github <repo>` — Register a skill
- `crux skill remove <name>` — Unregister a skill
- `crux skill list` — List registered skills

### Projects
- `crux project create [name]` — Create a new project with crux.json
- `crux project install <name>` — Add MCPs/skills to current project
- `crux project uninstall <name>` — Remove MCPs/skills from project
- `crux project sync` — Generate .mcp.json from crux.json
- `crux project status` — Show project health (MCPs, skills, auth)

### Tasks
- `crux task run <prompt>` — Execute a task in an isolated sandbox
- `crux task init` — Scaffold a run.json template
- `crux task list` — Show past/active runs
- `crux task clean` — Remove completed sandboxes

### System
- `crux init` — Initialize the crux environment
- `crux doctor` — Check crux environment health
- `crux version` — Show version and check for updates

## Usage Notes

- Run `crux init` first to set up the `~/.crux/` directory.
- Use `crux mcp search` to discover MCPs, then `crux mcp add` to register them.
- Use `crux mcp auth <name>` to authenticate any MCP that needs credentials.
- Use `crux project create` to start a project, then `crux project install` to add MCPs.
- Secrets are stored in the system keychain (macOS) or secret-service (Linux).
```

---

## 9. CI/CD Changes

**File: `.github/workflows/ci.yml`**

No structural changes needed — CI runs `pytest tests/unit/` and `pytest tests/integration/`. As long as tests are in the same directories with the same markers, CI picks them up automatically.

If new dependencies are added (e.g., `authlib` for OAuth), update `pyproject.toml` dependencies and the CI install step will pick them up.

---

## 10. Dependencies

### New Dependencies (Evaluate)

| Package | Purpose | Alternative |
|---|---|---|
| Pure Python implementation | OAuth 2.1 PKCE + token exchange | No external dep; use `urllib`, `hashlib`, `secrets`, `http.server` |

**Recommendation:** Implement OAuth 2.1 with pure Python stdlib. The OAuth flows needed (authorization code + PKCE, client credentials, token refresh) are straightforward HTTP requests. PKCE is just `secrets.token_urlsafe(32)` + SHA256. The redirect server is a minimal `http.server` handler. This avoids adding a dependency and keeps crux lightweight.

---

## 11. Migration Checklist

Since there are no existing users, there is no data migration needed. The registry.json schema gains new `auth.type` values but existing entries with `auth.type: "keychain"` or `auth.check_cmd` remain valid. The `tokens.json` file is new and created on first OAuth auth.

Summary of schema additions:
- `registry.json` auth block: new `type` values (`bearer`, `oauth`, `oauth-client-credentials`), new fields (`header_name`, `header_prefix`, `authorization_url`, `token_url`, `client_id`, `scopes`, `discovery_url`, `resource_url`, `keychain_key`)
- New file `~/.crux/tokens.json`: OAuth token metadata
- `.mcp.json` gains `type: "streamable-http"` entries with `url` and `headers`

---

## 12. Execution Order

The implementation should proceed in this order:

1. **CLI restructuring** — rewrite `main.py`, split command files, rename functions. All existing functionality works with new command names.
2. **Doctor scope reduction** — remove auth checks from doctor, update health.py.
3. **Unified auth command** — implement `crux mcp auth` for existing auth types (keychain, external-cli, setup-cmd).
4. **Bearer token auth** — add bearer type support to auth and sync.
5. **HTTP transport support** — add streamable-http entries to sync.
6. **OAuth 2.1 implementation** — oauth.py, auth.py OAuth flows, token storage.
7. **Project status enhancement** — add auth state + skills to project status.
8. **Tests** — update all integration and unit tests for new commands; add new test files.
9. **Documentation** — rewrite CLI reference, guides, skill file.
10. **CI verification** — ensure all tests pass in CI.
