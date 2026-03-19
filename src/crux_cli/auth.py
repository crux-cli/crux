"""Unified auth orchestration — dispatches by auth.type."""

from __future__ import annotations

import getpass
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any

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
        from crux_cli.oauth import run_client_credentials_flow, run_oauth_flow

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
            print("\u26a0\ufe0f  Authentication may have failed — check manually")
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


def _check_auth_status(name: str, auth: dict[str, Any], auth_type: str, secrets_index: dict[str, list[str]]) -> str:
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
            now = datetime.now(UTC)
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
