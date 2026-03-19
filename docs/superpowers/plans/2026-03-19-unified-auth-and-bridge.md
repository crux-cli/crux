# Unified Auth, Bridge & OAuth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `crux mcp auth` as the single command for all MCP authentication, including keychain, external-cli, setup-cmd, bearer, OAuth 2.1, and the stdio-to-HTTP bridge for remote MCPs.

**Architecture:** New `auth.py` orchestrates auth flows by dispatching on `auth.type`. New `oauth.py` handles OAuth 2.1 (PKCE, token exchange, refresh). New `bridge.py` proxies stdio↔HTTP for remote MCPs. `tokens.json` stores OAuth metadata (never token values). All secrets stay in OS keychain — never on disk.

**Tech Stack:** Python 3.11+ stdlib only (urllib, hashlib, secrets, http.server, webbrowser)

**Spec:** `docs/superpowers/specs/2026-03-19-cli-reorg-and-unified-auth-design.md` (Sections 2, 2.5)

---

## File Map

### New Files
| File | Responsibility |
|---|---|
| `src/crux_cli/auth.py` | Auth orchestration: dispatch by type, status checking, auth_single/auth_all/auth_status |
| `src/crux_cli/oauth.py` | OAuth 2.1: PKCE, local redirect server, token exchange, refresh, discovery |
| `src/crux_cli/bridge.py` | Stdio-to-HTTP proxy for remote MCP servers (runnable via `python3 -m crux_cli.bridge`) |
| `tests/unit/test_auth.py` | Auth dispatch, status computation, token metadata |
| `tests/unit/test_oauth.py` | PKCE generation, token exchange, refresh, discovery |
| `tests/unit/test_bridge.py` | Stdio-to-HTTP proxy, header injection, error handling |
| `tests/unit/test_no_secret_leaks.py` | Security invariant tests (sentinel value checks) |

### Modified Files
| File | Changes |
|---|---|
| `src/crux_cli/cli/commands/mcp.py` | Replace `cmd_mcp_auth` placeholder with real implementation |
| `src/crux_cli/paths.py` | Add `tokens_path()` |
| `src/crux_cli/sync.py` | Add HTTP bridge launcher generation |

---

## Phase 1: Auth Core (keychain, external-cli, setup-cmd, bearer)

### Task 1: Add `tokens_path()` to paths.py

**Files:**
- Modify: `src/crux_cli/paths.py`

- [ ] **Step 1: Read `src/crux_cli/paths.py`**
- [ ] **Step 2: Add `tokens_path()` function** returning `crux_home() / "tokens.json"`
- [ ] **Step 3: Commit**

### Task 2: Create `src/crux_cli/auth.py` — Auth orchestration

**Files:**
- Create: `src/crux_cli/auth.py`
- Test: `tests/unit/test_auth.py`

- [ ] **Step 1: Write failing tests in `tests/unit/test_auth.py`**

Test `auth_status()`:
- Given a registry with MCPs having different auth types, returns correct status for each
- `keychain` type: checks secrets index for missing env_vars
- `external-cli` type: reports status based on check_cmd exit code (mock subprocess)
- `bearer` type: checks keychain for stored token
- MCP with no auth block: excluded from results

Test `auth_single()` dispatch:
- `keychain` type: calls `SecretsBackend.set()` for each env_var (mock getpass + backend)
- `external-cli` type: runs check_cmd, then fix_cmd if needed (mock subprocess)
- `setup-cmd` type: runs setup_cmd (mock subprocess)
- `bearer` type: calls `SecretsBackend.set()` with keychain_key (mock getpass + backend)
- Unknown type: raises ValueError

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement `src/crux_cli/auth.py`**

```python
"""Unified auth orchestration — dispatches by auth.type."""

from __future__ import annotations

import getpass
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

from crux_cli.config import load_config
from crux_cli.manifest import load_registry
from crux_cli.paths import tokens_path
from crux_cli.secrets import get_backend, load_secrets_index


def auth_single(mcp_name: str, registry: dict[str, Any] | None = None) -> None:
    """Authenticate a single MCP by dispatching to the appropriate auth handler."""
    if registry is None:
        registry = load_registry()

    mcp_defs = registry.get("mcp_definitions", {})
    if mcp_name not in mcp_defs:
        print(f"\u274c MCP '{mcp_name}' not found in registry")
        sys.exit(1)

    auth = mcp_defs[mcp_name].get("auth", {})
    auth_type = auth.get("type", "")

    if not auth_type and not auth.get("env_vars") and not auth.get("check_cmd") and not auth.get("setup_cmd"):
        print(f"\u2139\ufe0f  MCP '{mcp_name}' has no authentication configured")
        return

    # Infer type from legacy fields if not explicit
    if not auth_type:
        if auth.get("env_vars"):
            auth_type = "keychain"
        elif auth.get("check_cmd"):
            auth_type = "external-cli"
        elif auth.get("setup_cmd"):
            auth_type = "setup-cmd"

    if auth_type == "keychain":
        _auth_keychain(mcp_name, auth)
    elif auth_type == "external-cli":
        _auth_external_cli(mcp_name, auth)
    elif auth_type == "setup-cmd":
        _auth_setup_cmd(mcp_name, auth)
    elif auth_type == "bearer":
        _auth_bearer(mcp_name, auth)
    elif auth_type in ("oauth", "oauth-client-credentials"):
        # Defer to oauth module (Plan phase 3)
        from crux_cli.oauth import run_oauth_flow, run_client_credentials_flow

        if auth_type == "oauth":
            run_oauth_flow(mcp_name, auth)
        else:
            run_client_credentials_flow(mcp_name, auth)
    else:
        msg = f"Unknown auth type '{auth_type}' for MCP '{mcp_name}'"
        raise ValueError(msg)


def auth_status(registry: dict[str, Any] | None = None) -> list[dict[str, str]]:
    """Return auth status for all MCPs that have auth requirements."""
    if registry is None:
        registry = load_registry()

    mcp_defs = registry.get("mcp_definitions", {})
    secrets_index = load_secrets_index()
    results = []

    for name, data in sorted(mcp_defs.items()):
        auth = data.get("auth", {})
        if not auth:
            continue

        auth_type = auth.get("type", "")
        if not auth_type:
            if auth.get("env_vars"):
                auth_type = "keychain"
            elif auth.get("check_cmd"):
                auth_type = "external-cli"
            elif auth.get("setup_cmd"):
                auth_type = "setup-cmd"

        status = _check_auth_status(name, auth, auth_type, secrets_index)
        results.append({"name": name, "auth_type": auth_type, "status": status})

    return results


def auth_all(registry: dict[str, Any] | None = None) -> None:
    """Authenticate all MCPs that need auth."""
    statuses = auth_status(registry)
    needing_auth = [s for s in statuses if "Authenticated" not in s["status"]]

    if not needing_auth:
        print("\u2705 All MCPs are authenticated")
        return

    for s in needing_auth:
        print(f"\n\u2500\u2500 Authenticating: {s['name']} ({s['auth_type']}) \u2500\u2500")
        try:
            auth_single(s["name"], registry)
        except Exception as e:  # noqa: BLE001
            print(f"\u26a0\ufe0f  Failed: {e}")


def _auth_keychain(mcp_name: str, auth: dict[str, Any]) -> None:
    """Authenticate via OS keychain — prompt for each env var."""
    env_vars = auth.get("env_vars", [])
    if not env_vars:
        print(f"\u2139\ufe0f  No env vars configured for '{mcp_name}'")
        return

    backend = get_backend()
    secrets_index = load_secrets_index()
    stored = secrets_index.get(mcp_name, [])

    for var in env_vars:
        if var in stored:
            existing = backend.get(mcp_name, var)
            if existing:
                print(f"  {var}: already set (use crux mcp auth {mcp_name} to reset)")
                continue

        value = getpass.getpass(f"  Enter {var}: ")
        if not value:
            print(f"  Skipped {var}")
            continue
        backend.set(mcp_name, var, value)
        print(f"  \u2705 Stored {var}")

    print(f"\u2705 Authenticated '{mcp_name}' — run 'crux project sync' to update launchers")


def _auth_external_cli(mcp_name: str, auth: dict[str, Any]) -> None:
    """Authenticate via external CLI tool."""
    check_cmd = auth.get("check_cmd", [])
    if not check_cmd:
        print(f"\u2139\ufe0f  No check_cmd configured for '{mcp_name}'")
        return

    try:
        result = subprocess.run(check_cmd, capture_output=True, timeout=10)  # noqa: S603
        if result.returncode == 0:
            print(f"\u2705 '{mcp_name}' is already authenticated")
            return
    except FileNotFoundError:
        print(f"\u274c Command not found: {check_cmd[0]}")
        fix = auth.get("fix_description", "")
        if fix:
            print(f"  Fix: {fix}")
        return
    except subprocess.TimeoutExpired:
        print(f"\u26a0\ufe0f  Auth check timed out for '{mcp_name}'")
        return

    fix_cmd = auth.get("fix_cmd", [])
    fix_desc = auth.get("fix_description", "")

    if fix_cmd:
        print(f"  Running: {' '.join(fix_cmd)}")
        subprocess.run(fix_cmd)  # noqa: S603
        # Re-check
        result = subprocess.run(check_cmd, capture_output=True, timeout=10)  # noqa: S603
        if result.returncode == 0:
            print(f"\u2705 '{mcp_name}' authenticated successfully")
        else:
            print(f"\u26a0\ufe0f  Authentication may have failed — check manually")
    elif fix_desc:
        print(f"  {fix_desc}")
    else:
        print(f"\u274c '{mcp_name}' auth check failed (exit {result.returncode})")


def _auth_setup_cmd(mcp_name: str, auth: dict[str, Any]) -> None:
    """Authenticate via one-time setup command."""
    setup_cmd = auth.get("setup_cmd", [])
    if not setup_cmd:
        print(f"\u2139\ufe0f  No setup_cmd configured for '{mcp_name}'")
        return

    print(f"  Running: {' '.join(setup_cmd)}")
    result = subprocess.run(setup_cmd)  # noqa: S603
    if result.returncode == 0:
        print(f"\u2705 Setup complete for '{mcp_name}'")
    else:
        print(f"\u26a0\ufe0f  Setup failed (exit {result.returncode})")
        sys.exit(result.returncode)


def _auth_bearer(mcp_name: str, auth: dict[str, Any]) -> None:
    """Authenticate via static Bearer token."""
    keychain_key = auth.get("keychain_key", "API_TOKEN")
    backend = get_backend()

    existing = backend.get(mcp_name, keychain_key)
    if existing:
        replace = input(f"  Token already stored for '{mcp_name}'. Replace? [y/N] ").strip().lower()
        if replace != "y":
            print("  Kept existing token")
            return

    value = getpass.getpass(f"  Enter token for '{mcp_name}': ")
    if not value:
        print("  Skipped — no token entered")
        return

    backend.set(mcp_name, keychain_key, value)
    print(f"\u2705 Token stored for '{mcp_name}'")


def _check_auth_status(
    name: str, auth: dict[str, Any], auth_type: str, secrets_index: dict[str, list[str]]
) -> str:
    """Check auth status for a single MCP. Returns a human-readable status string."""
    if auth_type == "keychain":
        env_vars = auth.get("env_vars", [])
        stored = secrets_index.get(name, [])
        missing = [v for v in env_vars if v not in stored]
        if missing:
            return f"Missing: {', '.join(missing)}"
        return "Authenticated"

    if auth_type == "external-cli":
        check_cmd = auth.get("check_cmd", [])
        if not check_cmd:
            return "No check command"
        try:
            result = subprocess.run(check_cmd, capture_output=True, timeout=5)  # noqa: S603
            return "Authenticated" if result.returncode == 0 else "Not authenticated"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return "Check failed"

    if auth_type == "setup-cmd":
        return "Run setup to configure"

    if auth_type == "bearer":
        keychain_key = auth.get("keychain_key", "API_TOKEN")
        backend = get_backend()
        existing = backend.get(name, keychain_key)
        return "Authenticated" if existing else "Token not set"

    if auth_type in ("oauth", "oauth-client-credentials"):
        return _check_oauth_status(name)

    return "Unknown auth type"


def _check_oauth_status(name: str) -> str:
    """Check OAuth token status from tokens.json metadata."""
    import json

    tp = tokens_path()
    if not tp.exists():
        return "Not authenticated"

    try:
        with open(tp) as f:
            tokens = json.load(f)
    except (json.JSONDecodeError, OSError):
        return "Token metadata corrupt"

    meta = tokens.get(name)
    if not meta:
        return "Not authenticated"

    expires_at = meta.get("expires_at")
    if expires_at:
        try:
            exp = datetime.fromisoformat(expires_at)
            now = datetime.now(timezone.utc)
            if exp <= now:
                refresh_key = meta.get("keychain_account_refresh")
                if refresh_key:
                    return "Refresh needed"
                return "Expired"
            remaining = exp - now
            hours = remaining.total_seconds() / 3600
            if hours < 1:
                return f"Expires in {int(remaining.total_seconds() / 60)}m"
            return f"Expires in {int(hours)}h"
        except ValueError:
            pass

    return "Authenticated"
```

- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

### Task 3: Wire `cmd_mcp_auth` in `commands/mcp.py`

**Files:**
- Modify: `src/crux_cli/cli/commands/mcp.py`

- [ ] **Step 1: Replace the `cmd_mcp_auth` placeholder** with:

```python
def cmd_mcp_auth(args: argparse.Namespace) -> None:
    """crux mcp auth — authenticate MCP servers."""
    from crux_cli.auth import auth_all, auth_single, auth_status

    name = getattr(args, "name", None)
    do_all = getattr(args, "all", False)

    if name:
        auth_single(name)
    elif do_all:
        auth_all()
    else:
        # Show auth status table
        from rich import box
        from rich.console import Console
        from rich.table import Table

        statuses = auth_status()
        if not statuses:
            print("No MCPs have authentication configured.")
            return

        console = Console()
        table = Table(title="MCP Authentication Status", box=box.SIMPLE_HEAVY, show_lines=False)
        table.add_column("Name", style="bold cyan", no_wrap=True)
        table.add_column("Auth Type", style="dim")
        table.add_column("Status")

        status_styles = {
            "Authenticated": "[green]Authenticated[/]",
            "Not authenticated": "[bold red]Not authenticated[/]",
            "Token not set": "[bold red]Token not set[/]",
            "Expired": "[bold red]Expired[/]",
            "Refresh needed": "[yellow]Refresh needed[/]",
            "Check failed": "[red]Check failed[/]",
        }

        for s in statuses:
            styled = status_styles.get(s["status"], s["status"])
            if s["status"].startswith("Missing:"):
                styled = f"[red]{s['status']}[/]"
            elif s["status"].startswith("Expires in"):
                styled = f"[yellow]{s['status']}[/]"
            table.add_row(s["name"], s["auth_type"], styled)

        console.print(table)
        print("\nRun: crux mcp auth <name>  to authenticate")
        print("     crux mcp auth --all   to authenticate all")
```

- [ ] **Step 2: Run integration test to verify** `crux mcp auth` no longer prints "not yet implemented"
- [ ] **Step 3: Commit**

### Task 4: Create security test suite `test_no_secret_leaks.py`

**Files:**
- Create: `tests/unit/test_no_secret_leaks.py`

- [ ] **Step 1: Write the security invariant tests**

These tests use a sentinel secret value and verify it never appears in any generated file. Cover:
- Launcher scripts never contain literal secrets
- `.mcp.json` never contains secrets
- `registry.json` never contains secret values
- `secrets.json` contains only key names, never values
- Full sync cycle with keychain auth: sentinel value absent from all files

- [ ] **Step 2: Run tests**
- [ ] **Step 3: Commit**

---

## Phase 2: HTTP Bridge

### Task 5: Create `src/crux_cli/bridge.py` — Stdio-to-HTTP proxy

**Files:**
- Create: `src/crux_cli/bridge.py`
- Test: `tests/unit/test_bridge.py`

The bridge:
- Reads ALL config from environment variables (CRUX_BRIDGE_URL, CRUX_BRIDGE_AUTH_HEADER, CRUX_BRIDGE_AUTH_PREFIX, CRUX_BRIDGE_AUTH_ENV)
- Takes ZERO CLI arguments (security: prevents token leakage in process listings)
- Reads newline-delimited JSON-RPC from stdin
- Forwards as HTTP POST with auth headers
- Writes responses to stdout
- Handles SSE streaming responses

- [ ] **Step 1: Write tests in `tests/unit/test_bridge.py`**
- [ ] **Step 2: Implement bridge**
- [ ] **Step 3: Commit**

### Task 6: Update `sync.py` for HTTP bridge launcher generation

**Files:**
- Modify: `src/crux_cli/sync.py`

- [ ] **Step 1: Add `_build_http_bridge_entry` function**

For MCPs with `type: "streamable-http"` and a `url` field, generate a launcher script that:
- Exports `CRUX_BRIDGE_URL`, `CRUX_BRIDGE_AUTH_*` env vars
- Fetches token from keychain at runtime
- Runs `exec python3 -m crux_cli.bridge` with zero arguments

- [ ] **Step 2: Modify `_build_server_entry` to dispatch**
- [ ] **Step 3: Add tests to `tests/unit/test_sync.py`**
- [ ] **Step 4: Commit**

---

## Phase 3: OAuth 2.1

### Task 7: Create `src/crux_cli/oauth.py`

**Files:**
- Create: `src/crux_cli/oauth.py`
- Test: `tests/unit/test_oauth.py`

Implements:
- `generate_pkce()` → (code_verifier, code_challenge)
- `discover_auth_server(auth_config)` → (authorization_url, token_url)
- `run_oauth_flow(mcp_name, auth_config)` — full Authorization Code + PKCE flow
- `run_client_credentials_flow(mcp_name, auth_config)`
- `refresh_access_token(mcp_name)` — exchange refresh token for new access token
- `load_token_metadata()` / `save_token_metadata()`
- Local redirect HTTP server with state validation and 120s timeout

- [ ] **Step 1: Write tests for PKCE, token exchange, refresh**
- [ ] **Step 2: Implement oauth.py**
- [ ] **Step 3: Commit**

### Task 8: Full integration test & verification

- [ ] **Step 1: Run full test suite**
- [ ] **Step 2: Verify all `crux mcp auth` subcommands work**
- [ ] **Step 3: Lint and format**
- [ ] **Step 4: Final commit**
