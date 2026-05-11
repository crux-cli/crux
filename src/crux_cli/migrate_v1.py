"""Migrate a v1 ``crux.json`` project into a v2 harness + pointer.

Operates on a single project directory: reads ``crux.json``, creates a
harness named after the project (or ``--name``), seeds the bundle with
the project's declared MCPs/skills, writes ``crux.toml`` pointing at the
new harness, and deletes the old ``crux.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

from crux_cli.bundle import load_bundle, save_bundle
from crux_cli.harness_ops import new_harness
from crux_cli.pointer import write_pointer


def migrate_cwd(project_dir: Path, *, name: str | None = None) -> str:
    """Migrate ``project_dir/crux.json`` to a harness. Returns the harness name."""
    crux_json = project_dir / "crux.json"
    if not crux_json.exists():
        raise FileNotFoundError(crux_json)
    data = json.loads(crux_json.read_text())

    harness_name = name or data.get("name") or project_dir.name
    hdir = new_harness(harness_name)
    bundle = load_bundle(hdir)
    bundle["mcps"]["include"] = list(data.get("mcps", []))
    bundle["skills"]["include"] = list(data.get("skills", []))
    save_bundle(hdir, bundle)

    write_pointer(project_dir / "crux.toml", f"{harness_name}@v1")
    crux_json.unlink()
    return harness_name
