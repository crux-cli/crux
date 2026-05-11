"""Generate ``.mcp.json`` from the MCPs included in a harness bundle.

Keychain-protected MCPs are emitted with the shared ``keychain-auth.sh``
launcher and env vars that drive the secret lookup at runtime. HTTP
transports go through ``http-bridge-auth.sh``. Plain MCPs are emitted as
``{command, args, env}`` with no wrapper.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from crux_cli import paths, store
from crux_cli.bundle import load_bundle


def _launchers_dir() -> Path:
    return paths.crux_home() / "launchers"


def _build_entry(name: str, data: dict[str, Any]) -> dict[str, Any]:
    auth = data.get("auth", {}) or {}
    auth_type = auth.get("type", "")
    command = data.get("command", "")
    args = list(data.get("args", []))

    if data.get("type") == "http" or data.get("url"):
        launcher = str(_launchers_dir() / "http-bridge-auth.sh")
        env: dict[str, str] = {
            "CRUX_MCP_NAME": name,
            "CRUX_BRIDGE_URL": data.get("url", ""),
        }
        if auth_type == "bearer":
            env["CRUX_BRIDGE_AUTH_HEADER"] = auth.get("header_name", "Authorization")
            env["CRUX_BRIDGE_AUTH_PREFIX"] = auth.get("header_prefix", "Bearer")
            env["CRUX_BRIDGE_AUTH_ENV"] = "CRUX_AUTH_TOKEN"
            env["CRUX_AUTH_KEYCHAIN_KEY"] = auth.get("keychain_key", "API_TOKEN")
        return {"command": launcher, "args": [], "env": env}

    if auth_type == "keychain":
        launcher = str(_launchers_dir() / "keychain-auth.sh")
        return {
            "command": launcher,
            "args": [command, *args],
            "env": {
                "CRUX_MCP_NAME": name,
                "CRUX_AUTH_ENV_VARS": ",".join(auth.get("env_vars", [])),
            },
        }

    entry: dict[str, Any] = {"command": command, "args": args}
    if data.get("env"):
        entry["env"] = data["env"]
    return entry


def emit_mcp_json(harness_name: str, version: str, out_path: Path) -> None:
    """Write ``.mcp.json`` for the MCPs included in *harness_name@version*."""
    hdir = store.harness_dir(harness_name, version)
    bundle = load_bundle(hdir)
    servers: dict[str, Any] = {}
    for name in bundle.get("mcps", {}).get("include", []):
        servers[name] = _build_entry(name, store.load_mcp_entry(name))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=out_path.parent, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump({"mcpServers": servers}, f, indent=2)
        Path(tmp).replace(out_path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
