#!/usr/bin/env python3
"""Minimal MCP server fixture for integration testing.

Validates AUTH_TOKEN env var and responds to JSON-RPC handshake.

Modes:
  Default (stdio MCP): reads JSON-RPC from stdin, validates auth, responds
  AUTH_CHECK_MODE=check: exits 0 if AUTH_TOKEN set, 1 if not (for external-cli testing)
"""

import json
import os
import sys


def _respond(obj: dict) -> None:
    """Write a JSON-RPC response to stdout."""
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _error_response(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _check_mode() -> None:
    """AUTH_CHECK_MODE=check: exit 0 if authenticated, 1 if not."""
    token = os.environ.get("AUTH_TOKEN", "")
    sys.exit(0 if token else 1)


def _serve() -> None:
    """Main MCP server loop."""
    token = os.environ.get("AUTH_TOKEN", "")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = msg.get("id")
        method = msg.get("method", "")

        if method == "initialize":
            if not token:
                _respond(_error_response(req_id, -32001, "authentication required: AUTH_TOKEN not set"))
                continue
            _respond(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "serverInfo": {"name": "test-mcp-server", "version": "1.0.0"},
                    },
                }
            )

        elif method == "tools/list":
            if not token:
                _respond(_error_response(req_id, -32001, "authentication required: AUTH_TOKEN not set"))
                continue
            _respond(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "test_tool",
                                "description": "A test tool for integration testing",
                                "inputSchema": {"type": "object", "properties": {}},
                            }
                        ]
                    },
                }
            )

        elif method == "notifications/initialized":
            pass  # Notification, no response needed

        else:
            _respond(_error_response(req_id, -32601, f"Method not found: {method}"))


def main() -> None:
    mode = os.environ.get("AUTH_CHECK_MODE", "")
    if mode == "check":
        _check_mode()
    else:
        _serve()


if __name__ == "__main__":
    main()
