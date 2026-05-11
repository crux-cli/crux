"""bundle.toml reader and writer for harnesses.

A bundle declares the harness identity plus its references to skills, MCPs,
plugins, and hooks. ``load_bundle`` always returns the four sections so
callers don't need to guard against missing keys.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from crux_cli.tomlio import dump_toml, load_toml


def default_bundle(name: str, version: str, description: str = "") -> dict[str, Any]:
    """Return a fresh bundle dict with empty include lists."""
    return {
        "harness": {"name": name, "version": version, "description": description},
        "skills": {"include": []},
        "mcps": {"include": []},
        "plugins": {"include": []},
        "hooks": {},
    }


def load_bundle(harness_dir: Path) -> dict[str, Any]:
    """Load bundle.toml, filling in default sections."""
    data = load_toml(harness_dir / "bundle.toml")
    data.setdefault("harness", {})
    data.setdefault("skills", {})
    data.setdefault("mcps", {})
    data.setdefault("plugins", {})
    data.setdefault("hooks", {})
    data["skills"].setdefault("include", [])
    data["mcps"].setdefault("include", [])
    data["plugins"].setdefault("include", [])
    return data


def save_bundle(harness_dir: Path, data: dict[str, Any]) -> None:
    """Write bundle.toml atomically."""
    harness_dir.mkdir(parents=True, exist_ok=True)
    dump_toml(harness_dir / "bundle.toml", data)
