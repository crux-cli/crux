#!/usr/bin/env sh
# Shared helper — sourced by other hooks.
# Ensures uv is available, installing it via the official installer if needed.

_ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return 0
  fi

  echo "  uv not found — installing via astral.sh..."

  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://astral.sh/uv/install.sh | sh
  else
    echo "  Error: curl or wget required to install uv." >&2
    exit 1
  fi

  # Pick up uv in the current shell session
  UV_ENV="${HOME}/.local/bin/env"
  if [ -f "${UV_ENV}" ]; then
    # shellcheck disable=SC1090
    . "${UV_ENV}"
  else
    export PATH="${HOME}/.local/bin:${PATH}"
  fi

  if ! command -v uv >/dev/null 2>&1; then
    echo "  Error: uv installed but not on PATH. Add ~/.local/bin to PATH." >&2
    exit 1
  fi

  echo "  uv installed."
}
