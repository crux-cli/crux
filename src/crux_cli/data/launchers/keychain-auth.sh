#!/bin/bash
# Shared keychain-auth launcher for stdio MCP servers.
# Auto-installed by crux setup — do not edit.
#
# Expected env vars (set via .mcp.json "env" field):
#   CRUX_MCP_NAME       — MCP name used as keychain service (e.g. "wikijs-mcp")
#   CRUX_AUTH_ENV_VARS   — Comma-separated env var names to fetch (e.g. "API_KEY,SECRET")
#
# Remaining positional args ($@) are the MCP command + arguments to exec.

set -euo pipefail

if [ -z "${CRUX_MCP_NAME:-}" ]; then
  echo "keychain-auth.sh: CRUX_MCP_NAME is not set" >&2
  exit 1
fi
if [ -z "${CRUX_AUTH_ENV_VARS:-}" ]; then
  echo "keychain-auth.sh: CRUX_AUTH_ENV_VARS is not set" >&2
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

# Export each requested env var from keychain
IFS=',' read -ra _vars <<< "$CRUX_AUTH_ENV_VARS"
for _var in "${_vars[@]}"; do
  export "$_var=$(_lookup_secret "$CRUX_MCP_NAME" "$_var")"
done

exec "$@"
