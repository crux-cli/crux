"""Stdio-to-HTTP bridge for remote MCP servers.

Reads JSON-RPC from stdin, forwards via HTTP with auth headers from
environment variables, writes responses to stdout. All configuration
via env vars — zero CLI arguments for security.

Usage: python3 -m crux_cli.bridge
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _build_auth_header() -> dict[str, str]:
    """Build auth header from environment variables."""
    header_name = os.environ.get("CRUX_BRIDGE_AUTH_HEADER", "")
    prefix = os.environ.get("CRUX_BRIDGE_AUTH_PREFIX", "")
    token_env = os.environ.get("CRUX_BRIDGE_AUTH_ENV", "")

    if not header_name or not token_env:
        return {}

    token = os.environ.get(token_env, "")
    if not token:
        return {}

    value = f"{prefix} {token}".strip() if prefix else token
    return {header_name: value}


def _forward_request(url: str, data: bytes, headers: dict[str, str]) -> bytes:
    """Forward a JSON-RPC request via HTTP POST."""
    req = urllib.request.Request(  # noqa: S310
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            **headers,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return resp.read()


def _make_error_response(req_id: int | str | None, code: int, message: str) -> str:
    """Create a JSON-RPC error response."""
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }
    )


def run() -> None:
    """Main bridge loop: read stdin, forward via HTTP, write to stdout."""
    url = os.environ.get("CRUX_BRIDGE_URL", "")
    if not url:
        print("CRUX_BRIDGE_URL not set", file=sys.stderr)
        sys.exit(1)

    auth_headers = _build_auth_header()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = msg.get("id")

        try:
            response_data = _forward_request(url, line.encode(), auth_headers)
            sys.stdout.write(response_data.decode() + "\n")
            sys.stdout.flush()
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            # Try to pass through JSON-RPC error from server
            try:
                parsed = json.loads(body)
                if "error" in parsed:
                    sys.stdout.write(body + "\n")
                    sys.stdout.flush()
                    continue
            except (json.JSONDecodeError, ValueError):
                pass
            error_resp = _make_error_response(req_id, -32000, f"HTTP {e.code}: {e.reason}")
            sys.stdout.write(error_resp + "\n")
            sys.stdout.flush()
        except urllib.error.URLError as e:
            error_resp = _make_error_response(req_id, -32001, f"Connection error: {e.reason}")
            sys.stdout.write(error_resp + "\n")
            sys.stdout.flush()
        except Exception as e:  # noqa: BLE001
            error_resp = _make_error_response(req_id, -32603, f"Bridge error: {e}")
            sys.stdout.write(error_resp + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run()
