"""Canonical path constants for Crux's ~/.crux/ home directory.

All paths respect two environment variables:
  - CRUX_HOME      Override the default ~/.crux/ root
  - CRUX_TEST_ROOT If set, ALL paths are rooted under this directory
                   instead of ~/.crux/ (used for test isolation)
"""

from __future__ import annotations

import os
from pathlib import Path


def _resolve_crux_home() -> Path:
    """Determine the Crux home directory, respecting env overrides."""
    test_root = os.environ.get("CRUX_TEST_ROOT")
    if test_root:
        return Path(test_root)

    env_home = os.environ.get("CRUX_HOME")
    if env_home:
        return Path(env_home)

    return Path.home() / ".crux"


def crux_home() -> Path:
    """Return the resolved Crux home directory."""
    return _resolve_crux_home()


def registry_path() -> Path:
    """Path to the local plugin/MCP registry."""
    return crux_home() / "registry.json"


def mcps_dir() -> Path:
    """Directory containing installed MCP server configurations."""
    return crux_home() / "mcps"


def launchers_dir() -> Path:
    """Directory containing generated MCP launcher scripts (legacy)."""
    return crux_home() / "mcps" / "launchers"


def shared_launchers_dir() -> Path:
    """Directory containing shared (non-generated) launcher scripts."""
    return crux_home() / "launchers"


def skills_dir() -> Path:
    """Directory containing installed skills."""
    return crux_home() / "skills"


def sandbox_dir() -> Path:
    """Directory containing run sandboxes."""
    return crux_home() / "sandbox"


def projects_path() -> Path:
    """Path to the projects index file."""
    return crux_home() / "projects.json"


def secrets_path() -> Path:
    """Path to the secrets index file."""
    return crux_home() / "secrets.json"


def config_path() -> Path:
    """Path to the user configuration file."""
    return crux_home() / "config.toml"


def tokens_path() -> Path:
    """Path to the OAuth token metadata file."""
    return crux_home() / "tokens.json"


# ---------------------------------------------------------------------------
# v2: harness manager layout
# ---------------------------------------------------------------------------


def registry_root() -> Path:
    """Root of the v2 registry tree containing mcps, skills, plugins, harnesses."""
    return crux_home() / "registry"


def mcps_root() -> Path:
    """v2 MCP registry directory: ~/.crux/registry/mcps/."""
    return registry_root() / "mcps"


def skills_root() -> Path:
    """v2 skills registry directory: ~/.crux/registry/skills/."""
    return registry_root() / "skills"


def plugins_root() -> Path:
    """v2 plugins registry directory: ~/.crux/registry/plugins/."""
    return registry_root() / "plugins"


def harnesses_root() -> Path:
    """v2 harnesses registry directory: ~/.crux/registry/harnesses/."""
    return registry_root() / "harnesses"


def active_pointer_path() -> Path:
    """User-level active harness pointer: ~/.crux/active.toml."""
    return crux_home() / "active.toml"


def history_path() -> Path:
    """User-level activation history log: ~/.crux/history."""
    return crux_home() / "history"


def claude_user_dir() -> Path:
    """User-level Claude Code directory: ~/.claude/."""
    return Path.home() / ".claude"


def claude_dir_for(project_dir: Path) -> Path:
    """Directory-level Claude Code directory: <project>/.claude/."""
    return project_dir / ".claude"
