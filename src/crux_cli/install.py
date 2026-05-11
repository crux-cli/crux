"""Package installation helpers for MCP registration."""

from __future__ import annotations

import subprocess


def install_npm_package(package: str) -> tuple[bool, str]:
    """Install an npm package globally. Returns (ok, error_message).

    Returns ``(True, "")`` if npm is missing or times out (we don't want to
    block registration on transient infra issues — the user can always
    re-run with ``--skip-install`` if a real install is needed).
    """
    try:
        result = subprocess.run(  # noqa: S603
            ["npm", "install", "-g", package],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "E404" in stderr or "404" in stderr:
                return False, f"package '{package}' not found in npm registry"
            return False, f"npm install failed: {stderr[:300]}"
        return True, ""
    except FileNotFoundError:
        return True, ""
    except subprocess.TimeoutExpired:
        return True, ""


def install_uv_package(package: str) -> tuple[bool, str]:
    """Install a Python package permanently via ``uv tool install``."""
    try:
        result = subprocess.run(  # noqa: S603
            ["uv", "tool", "install", package],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "not found" in stderr.lower() or "no such" in stderr.lower():
                return False, f"package '{package}' not found on PyPI"
            if "No solution found" in stderr or "yanked" in stderr.lower():
                return False, f"package '{package}' not installable (no available versions)"
            return False, f"uv tool install failed: {stderr[:300]}"
        return True, ""
    except FileNotFoundError:
        return True, ""
    except subprocess.TimeoutExpired:
        return True, ""
