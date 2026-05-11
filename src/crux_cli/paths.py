"""Canonical paths under Crux's ``~/.crux/`` home directory.

Paths respect two environment variables:

- ``CRUX_HOME``       — Override the default ``~/.crux/`` root.
- ``CRUX_TEST_ROOT``  — If set, every path is rooted under this directory
  instead. Used for test isolation.
"""

from __future__ import annotations

import os
from pathlib import Path


def _resolve_crux_home() -> Path:
    test_root = os.environ.get("CRUX_TEST_ROOT")
    if test_root:
        return Path(test_root)
    env_home = os.environ.get("CRUX_HOME")
    if env_home:
        return Path(env_home)
    return Path.home() / ".crux"


def crux_home() -> Path:
    """Resolved Crux home directory."""
    return _resolve_crux_home()


def secrets_path() -> Path:
    """Path to the secrets index file."""
    return crux_home() / "secrets.json"


def config_path() -> Path:
    """Path to the user configuration file."""
    return crux_home() / "config.toml"


def tokens_path() -> Path:
    """Path to the OAuth token metadata file (used by HTTP bridges)."""
    return crux_home() / "tokens.json"


# ---------------------------------------------------------------------------
# v2: harness manager layout
# ---------------------------------------------------------------------------


def registry_root() -> Path:
    """Root of the v2 registry tree containing mcps, skills, plugins, harnesses."""
    return crux_home() / "registry"


def mcps_root() -> Path:
    """v2 MCP registry directory: ``~/.crux/registry/mcps/``."""
    return registry_root() / "mcps"


def skills_root() -> Path:
    """v2 skills registry directory: ``~/.crux/registry/skills/``."""
    return registry_root() / "skills"


def plugins_root() -> Path:
    """v2 plugins registry directory: ``~/.crux/registry/plugins/``."""
    return registry_root() / "plugins"


def harnesses_root() -> Path:
    """v2 harnesses registry directory: ``~/.crux/registry/harnesses/``."""
    return registry_root() / "harnesses"


def active_pointer_path() -> Path:
    """User-level active harness pointer: ``~/.crux/active.toml``."""
    return crux_home() / "active.toml"


def history_path() -> Path:
    """User-level activation history log: ``~/.crux/history``."""
    return crux_home() / "history"


def claude_user_dir() -> Path:
    """User-level Claude Code directory: ``~/.claude/``."""
    return Path.home() / ".claude"


def claude_dir_for(project_dir: Path) -> Path:
    """Directory-level Claude Code directory: ``<project>/.claude/``."""
    return project_dir / ".claude"
