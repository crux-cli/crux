#!/bin/bash
# Shared HTTP bridge auth launcher for remote MCP servers.
# Auto-installed by crux setup — do not edit.
#
# Expected env vars (set via .mcp.json "env" field):
#   CRUX_MCP_NAME              — MCP name used as keychain service
#   CRUX_AUTH_KEYCHAIN_KEY     — Keychain account name to look up (e.g. "API_TOKEN", "access_token")
#   CRUX_BRIDGE_URL            — Remote MCP endpoint URL
#   CRUX_BRIDGE_AUTH_HEADER    — HTTP header name (e.g. "Authorization")
#   CRUX_BRIDGE_AUTH_PREFIX    — Header value prefix (e.g. "Bearer")
#   CRUX_BRIDGE_AUTH_ENV       — Env var name the bridge reads the token from
#
# Execs python3 -m crux_cli.bridge with the token injected.

set -euo pipefail

if [ -z "${CRUX_MCP_NAME:-}" ]; then
  echo "http-bridge-auth.sh: CRUX_MCP_NAME is not set" >&2
  exit 1
fi

# Platform-specific secret lookup
_lookup_secret() {
  local mcp_name="$1" var_name="$2"
  case "$(uname -s)" in
    Darwin)
      security find-generic-password -s "crux.${mcp_name}" -a "${var_name}" -w 2>/dev/null || true
      ;;
    *)
      secret-tool lookup service "crux.${mcp_name}" username "${var_name}" 2>/dev/null || true
      ;;
  esac
}

# Fetch the token and export it
if [ -n "${CRUX_AUTH_KEYCHAIN_KEY:-}" ] && [ -n "${CRUX_BRIDGE_AUTH_ENV:-}" ]; then
  export "${CRUX_BRIDGE_AUTH_ENV}=$(_lookup_secret "$CRUX_MCP_NAME" "$CRUX_AUTH_KEYCHAIN_KEY")"
fi

exec python3 -m crux_cli.bridge
