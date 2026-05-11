"""registry_ops.py — add and remove registry primitives.

Adds:
- MCPs from npm, uvx, github, or local sources (installs the package if applicable).
- Skills from local paths or GitHub repos.
- Plugins from local paths (versioned).

Removes:
- MCPs/skills/plugins by name, refusing to delete primitives still
  referenced by any harness bundle unless ``force=True``.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from crux_cli import paths, store
from crux_cli.bundle import load_bundle
from crux_cli.install import install_npm_package, install_uv_package


def _referencing_harnesses(name: str, kind: str) -> list[str]:
    """Return ``["<harness>@<version>", ...]`` for harnesses including this name in *kind*."""
    refs: list[str] = []
    for harness in store.list_harnesses():
        for version in store.harness_versions(harness):
            try:
                bundle = load_bundle(store.harness_dir(harness, version))
            except (FileNotFoundError, OSError):
                continue
            included = bundle.get(kind, {}).get("include", []) or []
            base_names = [str(r).split("@", 1)[0] for r in included]
            if name in base_names:
                refs.append(f"{harness}@{version}")
    return refs


def add_mcp(
    name: str,
    *,
    source_kind: str,
    source: str,
    args: list[str] | None = None,
    keychain: list[str] | None = None,
    skip_install: bool = False,
) -> None:
    """Register an MCP. ``source_kind`` is ``npm | uvx | github | local | http``."""
    if store.mcp_dir(name).exists():
        raise FileExistsError(f"mcp '{name}' already exists")

    entry: dict[str, Any] = {"type": source_kind, "source": source}
    extra = list(args or [])

    if source_kind == "npm":
        if not skip_install:
            ok, err = install_npm_package(source)
            if not ok:
                raise RuntimeError(err)
        entry.update({"command": "npx", "args": ["-y", source, *extra]})
    elif source_kind == "uvx":
        if not skip_install:
            ok, err = install_uv_package(source)
            if not ok:
                raise RuntimeError(err)
        entry.update({"command": "uvx", "args": [source, *extra]})
    elif source_kind == "github":
        dest = store.mcp_dir(name) / "source"
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(  # noqa: S603
            ["git", "clone", f"https://github.com/{source}", str(dest)],  # noqa: S607
            check=True,
        )
        entry.update({"command": "", "args": extra, "source_dir": str(dest)})
    elif source_kind == "local":
        entry.update({"source_dir": source, "args": extra})
    elif source_kind == "http":
        entry.update({"url": source})
    else:
        raise ValueError(f"unknown source_kind: {source_kind}")

    if keychain:
        entry["auth"] = {"type": "keychain", "env_vars": list(keychain)}

    store.save_mcp_entry(name, entry)


def add_skill_local(name: str, src: Path) -> None:
    if not src.exists() or not src.is_dir():
        raise FileNotFoundError(src)
    dst = store.skill_dir(name)
    if dst.exists():
        raise FileExistsError(f"skill '{name}' already exists")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)


def add_skill_github(name: str, repo: str) -> None:
    dst = store.skill_dir(name)
    if dst.exists():
        raise FileExistsError(f"skill '{name}' already exists")
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(  # noqa: S603
        ["git", "clone", f"https://github.com/{repo}", str(dst)],  # noqa: S607
        check=True,
    )


def add_plugin_local(name: str, src: Path, *, version: str = "v1") -> None:
    if not src.exists() or not src.is_dir():
        raise FileNotFoundError(src)
    dst = store.plugin_dir(name, version)
    if dst.exists():
        raise FileExistsError(f"plugin '{name}@{version}' already exists")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)


def remove(name: str, *, force: bool) -> None:
    """Remove every primitive matching *name*. Refuses if referenced."""
    targets: list[tuple[str, Path]] = []
    if store.mcp_dir(name).exists():
        targets.append(("mcps", store.mcp_dir(name)))
    if store.skill_dir(name).exists():
        targets.append(("skills", store.skill_dir(name)))
    plugin_root = paths.plugins_root() / name
    if plugin_root.exists():
        targets.append(("plugins", plugin_root))
    if not targets:
        raise FileNotFoundError(name)

    if not force:
        all_refs: list[str] = []
        for kind, _ in targets:
            all_refs.extend(_referencing_harnesses(name, kind))
        if all_refs:
            raise RuntimeError(f"'{name}' referenced by: {', '.join(all_refs)} — pass force=True")

    for _kind, path in targets:
        shutil.rmtree(path)
