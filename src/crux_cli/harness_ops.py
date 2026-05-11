"""Harness lifecycle operations: new and bump.

``new_harness`` creates ``<name>/v1`` with a fresh bundle, an empty
``CLAUDE.md``, and a ``hooks/`` directory.

``bump`` copies the latest version directory into the next ``vN+1`` slot
and rewrites ``bundle.toml`` with the new version string.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from crux_cli import paths, store
from crux_cli.bundle import default_bundle, save_bundle
from crux_cli.tomlio import dump_toml, load_toml


def new_harness(name: str, description: str = "") -> Path:
    target = paths.harnesses_root() / name
    if target.exists():
        raise FileExistsError(f"harness '{name}' already exists")
    v1 = target / "v1"
    save_bundle(v1, default_bundle(name, "v1", description))
    (v1 / "CLAUDE.md").write_text(f"# {name} v1\n\n")
    (v1 / "hooks").mkdir(exist_ok=True)
    return v1


def bump(name: str) -> Path:
    latest = store.latest_version(name)
    if latest is None:
        raise FileNotFoundError(f"harness '{name}' not found")
    nxt_version = store.next_version(name)
    src = paths.harnesses_root() / name / latest
    dst = paths.harnesses_root() / name / nxt_version
    shutil.copytree(src, dst)
    bundle_path = dst / "bundle.toml"
    data = load_toml(bundle_path)
    data.setdefault("harness", {})["version"] = nxt_version
    dump_toml(bundle_path, data)
    return dst
