"""Package validation for npm and PyPI packages."""

from __future__ import annotations

import subprocess


def validate_npm_package(package: str) -> tuple[bool, str]:
    """Check that an npm package exists and can be cached.

    Returns (ok, error_message).
    """
    # Strip version specifier if present (e.g., "@scope/pkg@1.0.0" -> "@scope/pkg")
    pkg_name = package.rsplit("@", 1)[0] if not package.startswith("@") else package
    if package.startswith("@") and "@" in package[1:]:
        # Scoped package with version: @scope/pkg@1.0.0
        parts = package[1:].split("@", 1)
        pkg_name = "@" + parts[0]

    try:
        # First check if the package exists in the registry
        result = subprocess.run(  # noqa: S603
            ["npm", "view", pkg_name, "name"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "E404" in stderr or "404" in stderr:
                return False, f"package '{pkg_name}' not found in npm registry"
            return False, f"npm lookup failed: {stderr[:200]}"

        # Pre-cache the package so it's ready for use
        cache_result = subprocess.run(  # noqa: S603
            ["npm", "cache", "add", package],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=60,
        )
        if cache_result.returncode != 0:
            stderr = cache_result.stderr.strip()
            return False, f"package '{package}' failed to download: {stderr[:200]}"

        return True, ""
    except FileNotFoundError:
        return True, ""  # npm not installed, skip validation
    except subprocess.TimeoutExpired:
        return True, ""  # timeout, skip validation


def validate_pypi_package(package: str) -> tuple[bool, str]:
    """Check that a PyPI package exists and has installable versions.

    Returns (ok, error_message).
    """
    # Strip extras/version specifiers (e.g., "pkg[extra]>=1.0" -> "pkg")
    pkg_name = package.split("[")[0].split(">")[0].split("<")[0].split("=")[0].split("!")[0]

    try:
        result = subprocess.run(  # noqa: S603
            ["uv", "pip", "install", "--dry-run", pkg_name],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "No solution found" in stderr or "no versions" in stderr.lower() or "yanked" in stderr.lower():
                return False, f"package '{pkg_name}' not installable (no available versions)"
            if "not found" in stderr.lower() or "no such" in stderr.lower():
                return False, f"package '{pkg_name}' not found on PyPI"
            return False, f"uv lookup failed: {stderr[:200]}"
        return True, ""
    except FileNotFoundError:
        return True, ""  # uv not installed, skip validation
    except subprocess.TimeoutExpired:
        return True, ""  # timeout, skip validation
