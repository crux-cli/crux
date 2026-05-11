"""Activation: turn a harness bundle into a symlink plan and deploy it.

A symlink plan is a list of ``(symlink_path, real_source_path)`` pairs. The
plan is derived purely from the bundle's references; ``apply_plan`` then
deploys it, refusing to clobber any non-Crux file or symlink.
"""

from __future__ import annotations

from pathlib import Path

from crux_cli import paths, store
from crux_cli.bundle import load_bundle
from crux_cli.mcp_emit import emit_mcp_json


class ConflictError(RuntimeError):
    """A non-Crux file/symlink blocks a target path."""


def plan_symlinks(name: str, version: str, scope_target: Path) -> list[tuple[Path, Path]]:
    """Return ``[(symlink_path, real_source_path), ...]`` for a bundle.

    ``scope_target`` is the directory that holds Claude Code's view
    (``~/.claude`` for user scope or ``<cwd>/.claude`` for directory scope).
    """
    hdir = store.harness_dir(name, version)
    bundle = load_bundle(hdir)
    plan: list[tuple[Path, Path]] = []

    claude_md = hdir / "CLAUDE.md"
    if claude_md.exists():
        plan.append((scope_target / "CLAUDE.md", claude_md))

    for skill in bundle.get("skills", {}).get("include", []):
        plan.append((scope_target / "skills" / skill, store.skill_dir(skill)))

    for plugin_ref in bundle.get("plugins", {}).get("include", []):
        if "@" in plugin_ref:
            pname, pver = plugin_ref.split("@", 1)
        else:
            pname, pver = plugin_ref, None
        plan.append((scope_target / "plugins" / pname, store.plugin_dir(pname, pver)))

    hooks = bundle.get("hooks", {}) or {}
    for _key, rel in hooks.items():
        if not isinstance(rel, str) or not rel:
            continue
        src = hdir / rel
        plan.append((scope_target / "hooks" / Path(rel).name, src))

    return plan


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def apply_plan(plan: list[tuple[Path, Path]], known_registry_root: Path | None = None) -> None:
    """Create the symlinks listed in *plan*.

    Refuses to overwrite regular files or symlinks whose resolved target
    is not under *known_registry_root* (defaults to ``paths.registry_root()``).
    """
    if known_registry_root is None:
        known_registry_root = paths.registry_root()

    for target, src in plan:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            try:
                resolved = target.resolve(strict=False)
            except OSError:
                resolved = None
            if resolved and _is_under(resolved, known_registry_root):
                target.unlink()
            else:
                raise ConflictError(f"refusing to overwrite foreign symlink: {target}")
        elif target.exists():
            raise ConflictError(f"refusing to overwrite existing file: {target}")
        target.symlink_to(src)


def _scope_target(scope: str, cwd: Path) -> Path:
    return paths.claude_user_dir() if scope == "user" else paths.claude_dir_for(cwd)


def remove_managed_symlinks(scope_target: Path) -> None:
    """Delete any symlink under *scope_target* that points into the registry.

    Walks ``CLAUDE.md``, ``skills/*``, ``plugins/*``, ``hooks/*``. Leaves
    non-managed files alone.
    """
    if not scope_target.exists():
        return
    known = paths.registry_root().resolve()
    candidates: list[Path] = []
    claude_md = scope_target / "CLAUDE.md"
    if claude_md.is_symlink():
        candidates.append(claude_md)
    for sub in ("skills", "plugins", "hooks"):
        d = scope_target / sub
        if d.exists():
            candidates.extend(p for p in d.iterdir() if p.is_symlink())

    for c in candidates:
        try:
            resolved = c.resolve(strict=False)
        except OSError:
            continue
        if _is_under(resolved, known):
            c.unlink()


def activate(name: str, version: str, scope: str, cwd: Path) -> None:
    """Deploy *name@version* to *scope* (``"user"`` or ``"directory"``).

    Clears previously-managed symlinks under the scope's ``.claude/``
    directory, then writes the new plan and emits ``.mcp.json``.
    """
    target = _scope_target(scope, cwd)
    target.mkdir(parents=True, exist_ok=True)
    remove_managed_symlinks(target)
    plan = plan_symlinks(name, version, scope_target=target)
    apply_plan(plan)
    emit_mcp_json(name, version, out_path=target / ".mcp.json")
