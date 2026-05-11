"""Sync engine — read crux.json + registry, generate .mcp.json.

Launcher scripts are no longer generated per-MCP.  Instead, shared
launcher scripts installed by ``crux setup`` handle keychain lookups
at runtime, driven by env vars in the ``.mcp.json`` entries.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

from crux_cli.paths import crux_home, registry_path, shared_launchers_dir, skills_dir

_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
_SAFE_ENV_VAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------


def _load_registry_for_sync(reg_path: Path | None = None) -> dict[str, Any]:
    """Load the v1 registry for sync operations."""
    path = reg_path or registry_path()
    if not path.exists():
        return {"version": "1.0.0", "mcp_definitions": {}, "skill_definitions": {}}
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_mcp_name(mcp_name: str) -> None:
    if not _SAFE_NAME_RE.match(mcp_name):
        msg = f"Unsafe MCP name: {mcp_name!r}"
        raise ValueError(msg)


def _validate_env_var(var: str) -> None:
    if not _SAFE_ENV_VAR_RE.match(var):
        msg = f"Unsafe env var name: {var!r}"
        raise ValueError(msg)


# ---------------------------------------------------------------------------
# Resolve source_dir to absolute path
# ---------------------------------------------------------------------------


def _resolve_source_dir(source_dir: str) -> str:
    """Turn a potentially relative source_dir into an absolute path."""
    p = Path(source_dir)
    if p.is_absolute():
        return source_dir
    return str(crux_home().parent / source_dir)


# ---------------------------------------------------------------------------
# .mcp.json entry builders
# ---------------------------------------------------------------------------


def _build_keychain_auth_entry(
    mcp_name: str,
    mcp_data: dict[str, Any],
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    """Build a .mcp.json entry for a stdio MCP with keychain auth.

    Uses the shared ``keychain-auth.sh`` launcher; env vars in the
    returned dict tell the script which secrets to fetch.
    """
    env_vars = mcp_data.get("auth", {}).get("env_vars", [])
    _validate_mcp_name(mcp_name)
    for var in env_vars:
        _validate_env_var(var)

    command = mcp_data.get("command", "")
    args = list(mcp_data.get("args", []))

    if mcp_data.get("source_dir"):
        abs_source = _resolve_source_dir(mcp_data["source_dir"])
        args = [abs_source if a == "{source_dir}" else a for a in args]

    launcher = str(shared_launchers_dir() / "keychain-auth.sh")
    entry: dict[str, Any] = {
        "command": launcher,
        "args": [command] + args + (extra_args or []),
        "env": {
            "CRUX_MCP_NAME": mcp_name,
            "CRUX_AUTH_ENV_VARS": ",".join(env_vars),
        },
    }
    return entry


def _build_http_bridge_entry(
    mcp_name: str,
    mcp_data: dict[str, Any],
) -> dict[str, Any]:
    """Build a .mcp.json entry for an HTTP-transport MCP using the bridge.

    Uses the shared ``http-bridge-auth.sh`` launcher; env vars drive
    the keychain lookup and bridge configuration.
    """
    _validate_mcp_name(mcp_name)

    url = mcp_data.get("url", "")
    auth = mcp_data.get("auth", {})
    auth_type = auth.get("type", "")

    env: dict[str, str] = {
        "CRUX_MCP_NAME": mcp_name,
        "CRUX_BRIDGE_URL": url,
    }

    if auth_type == "bearer":
        keychain_key = auth.get("keychain_key", "API_TOKEN")
        _validate_env_var(keychain_key)
        env["CRUX_BRIDGE_AUTH_HEADER"] = auth.get("header_name", "Authorization")
        env["CRUX_BRIDGE_AUTH_PREFIX"] = auth.get("header_prefix", "Bearer")
        env["CRUX_BRIDGE_AUTH_ENV"] = "CRUX_AUTH_TOKEN"
        env["CRUX_AUTH_KEYCHAIN_KEY"] = keychain_key
    elif auth_type in ("oauth", "oauth-client-credentials"):
        env["CRUX_BRIDGE_AUTH_HEADER"] = auth.get("header_name", "Authorization")
        env["CRUX_BRIDGE_AUTH_PREFIX"] = auth.get("header_prefix", "Bearer")
        env["CRUX_BRIDGE_AUTH_ENV"] = "CRUX_AUTH_TOKEN"
        env["CRUX_AUTH_KEYCHAIN_KEY"] = "access_token"

    launcher = str(shared_launchers_dir() / "http-bridge-auth.sh")
    return {"command": launcher, "args": [], "env": env}


def _build_server_entry(
    mcp_name: str,
    mcp_data: dict[str, Any],
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    """Build a single mcpServers entry for .mcp.json."""
    # HTTP-transport MCPs use the bridge
    if mcp_data.get("type") == "streamable-http" or mcp_data.get("url"):
        return _build_http_bridge_entry(mcp_name, mcp_data)

    env_vars = mcp_data.get("auth", {}).get("env_vars", [])

    if env_vars:
        return _build_keychain_auth_entry(mcp_name, mcp_data, extra_args)

    # No auth — pass through command/args/env directly
    server: dict[str, Any] = {k: v for k, v in mcp_data.items() if k in ("command", "args", "env")}
    if extra_args:
        server["args"] = server.get("args", []) + extra_args

    if mcp_data.get("source_dir"):
        abs_source = _resolve_source_dir(mcp_data["source_dir"])
        server["args"] = [abs_source if a == "{source_dir}" else a for a in server.get("args", [])]

    return server


def sync_project(
    project_dir: Path,
    registry: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Sync a single project: generate .mcp.json, copy skills."""
    crux_json_path = project_dir / "crux.json"
    if not crux_json_path.exists():
        return False, ["No crux.json found"]

    with open(crux_json_path) as f:
        crux_json = json.load(f)

    if registry is None:
        registry = _load_registry_for_sync()

    mcp_defs = registry.get("mcp_definitions", {})
    skill_defs = registry.get("skill_definitions", {})
    issues: list[str] = []

    # Build .mcp.json
    declared_mcps = crux_json.get("mcps", [])
    mcp_servers: dict[str, Any] = {}
    for mcp_entry in declared_mcps:
        if isinstance(mcp_entry, str):
            mcp_name, extra_args = mcp_entry, []
        else:
            mcp_name = mcp_entry.get("name", "")
            extra_args = mcp_entry.get("args", [])
        if mcp_name not in mcp_defs:
            issues.append(f"MCP '{mcp_name}' not found in registry")
            continue
        mcp_servers[mcp_name] = _build_server_entry(mcp_name, mcp_defs[mcp_name], extra_args or None)

    mcp_file = project_dir / ".mcp.json"
    new_config = {"mcpServers": mcp_servers}
    _atomic_json_write(mcp_file, new_config)

    # Copy skills
    declared_skills = crux_json.get("skills", [])
    for skill_name in declared_skills:
        if skill_name not in skill_defs:
            issues.append(f"Skill '{skill_name}' not found in registry")
            continue
        skill_data = skill_defs[skill_name]
        source_dir_str = skill_data.get("source_dir", "")
        source_path = Path(source_dir_str)
        if not source_path.is_absolute():
            candidate = skills_dir() / skill_name
            if candidate.exists():
                source_path = candidate
            elif source_dir_str:
                source_path = crux_home().parent / source_dir_str
            else:
                source_path = skills_dir() / skill_name

        safe_skill = Path(skill_name).name
        skills_parent = project_dir / ".claude" / "skills"
        dest_path = skills_parent / safe_skill
        if source_path.exists():
            import shutil

            if not dest_path.resolve().is_relative_to(skills_parent.resolve()):
                issues.append(f"Skill '{skill_name}' resolves outside skills directory")
                continue
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.copytree(source_path, dest_path)
        else:
            issues.append(f"Skill '{skill_name}' source missing at {source_path}")

    return True, issues


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _atomic_json_write(path: Path, data: dict[str, Any]) -> None:
    """Write JSON atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump(data, f, indent=2)
        Path(tmp).replace(path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
