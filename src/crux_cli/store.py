"""Read-only and read/write access to the registry tree.

The registry tree lives under ``~/.crux/registry/`` with four primitive types:

- ``mcps/<name>/mcp.toml``                (plus optional ``source/`` clone)
- ``skills/<name>/``                      (directory; the skill IS the dir)
- ``plugins/<name>/<version>/``           (directory; versioned)
- ``harnesses/<name>/<version>/``         (``bundle.toml`` + ``CLAUDE.md`` + ``hooks/``)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from crux_cli import paths
from crux_cli.tomlio import dump_toml, load_toml

_VERSION_RE = re.compile(r"^v(\d+)$")


def _version_sort_key(v: str) -> tuple[int, str]:
    m = _VERSION_RE.match(v)
    return (int(m.group(1)), v) if m else (10**9, v)


def _list_subdirs(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])


# ---------------------------------------------------------------------------
# Primitive enumeration
# ---------------------------------------------------------------------------


def list_mcps() -> list[str]:
    return _list_subdirs(paths.mcps_root())


def list_skills() -> list[str]:
    return _list_subdirs(paths.skills_root())


def list_plugins() -> list[str]:
    return _list_subdirs(paths.plugins_root())


def list_harnesses() -> list[str]:
    return _list_subdirs(paths.harnesses_root())


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------


def harness_versions(name: str) -> list[str]:
    return sorted(_list_subdirs(paths.harnesses_root() / name), key=_version_sort_key)


def latest_version(name: str) -> str | None:
    vs = harness_versions(name)
    return vs[-1] if vs else None


def next_version(name: str) -> str:
    latest = latest_version(name)
    if not latest:
        return "v1"
    m = _VERSION_RE.match(latest)
    return f"v{int(m.group(1)) + 1}" if m else "v1"


def plugin_versions(name: str) -> list[str]:
    return sorted(_list_subdirs(paths.plugins_root() / name), key=_version_sort_key)


# ---------------------------------------------------------------------------
# Directory accessors
# ---------------------------------------------------------------------------


def harness_dir(name: str, version: str | None = None) -> Path:
    if version is None:
        version = latest_version(name) or ""
    return paths.harnesses_root() / name / version


def plugin_dir(name: str, version: str | None = None) -> Path:
    if version is None:
        vs = plugin_versions(name)
        version = vs[-1] if vs else ""
    return paths.plugins_root() / name / version


def skill_dir(name: str) -> Path:
    return paths.skills_root() / name


def mcp_dir(name: str) -> Path:
    return paths.mcps_root() / name


def mcp_toml_path(name: str) -> Path:
    return mcp_dir(name) / "mcp.toml"


# ---------------------------------------------------------------------------
# MCP entry I/O
# ---------------------------------------------------------------------------


def load_mcp_entry(name: str) -> dict[str, Any]:
    return load_toml(mcp_toml_path(name))


def save_mcp_entry(name: str, data: dict[str, Any]) -> None:
    mcp_dir(name).mkdir(parents=True, exist_ok=True)
    dump_toml(mcp_toml_path(name), data)
