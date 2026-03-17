"""Version checking for Crux — local version and PyPI update checks."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from packaging.version import InvalidVersion, Version

from crux_cli import __version__

_VERSION_RE = re.compile(r"^\d+[\d.]*\d+$")

PYPI_URL = "https://pypi.org/pypi/crux-cli/json"


def current_version() -> str:
    """Return the currently installed version string."""
    return __version__


def check_pypi_version(*, timeout: float = 5.0) -> str | None:
    """Query PyPI for the latest crux-cli version."""
    try:
        req = urllib.request.Request(PYPI_URL, headers={"Accept": "application/json"})  # noqa: S310
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
        ver = data["info"]["version"]
        if not isinstance(ver, str) or not _VERSION_RE.match(ver):
            return None
        return ver
    except (urllib.error.URLError, OSError, KeyError, json.JSONDecodeError, ValueError):
        return None


def format_version_output(*, check: bool = False) -> str:
    """Build the human-readable version string."""
    local = current_version()

    if not check:
        return f"crux-cli v{local}"

    latest = check_pypi_version()

    if latest is None:
        return f"crux-cli v{local} (could not check for updates)"

    try:
        local_ver = Version(local)
        latest_ver = Version(latest)
    except InvalidVersion:
        if latest != local:
            return f"Update available: v{local} → v{latest}. Run: uv tool upgrade crux-cli"
        return f"crux-cli v{local} (up to date)"

    if latest_ver > local_ver:
        return f"Update available: v{local} → v{latest}. Run: uv tool upgrade crux-cli"
    if local_ver > latest_ver:
        return f"crux-cli v{local} (ahead of PyPI v{latest})"

    return f"crux-cli v{local} (up to date)"
