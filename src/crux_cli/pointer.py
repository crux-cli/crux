"""Pointer-file resolution.

A pointer file is a TOML file with a single key naming the active harness::

    harness = "coding-default@v7"

Resolution order:
1. Walk up from cwd looking for ``crux.toml``. If found, that's the directory pointer.
2. Else read ``~/.crux/active.toml`` for a user-level pointer.
3. Else: no active harness.
"""

from __future__ import annotations

from pathlib import Path

from crux_cli.paths import active_pointer_path
from crux_cli.tomlio import dump_toml, load_toml


def parse_ref(ref: str) -> tuple[str, str | None]:
    """Parse ``name`` or ``name@version`` into a tuple. Raises ValueError on garbage."""
    if not ref or ref.startswith("@") or ref.endswith("@"):
        raise ValueError(f"Invalid harness ref: {ref!r}")
    if "@" in ref:
        if ref.count("@") != 1:
            raise ValueError(f"Invalid harness ref: {ref!r}")
        name, version = ref.split("@", 1)
        if not name or not version:
            raise ValueError(f"Invalid harness ref: {ref!r}")
        return name, version
    return ref, None


def write_pointer(path: Path, harness_ref: str) -> None:
    """Validate and write a pointer file."""
    parse_ref(harness_ref)
    dump_toml(path, {"harness": harness_ref})


def read_pointer(path: Path) -> tuple[str, str | None] | None:
    """Read a pointer file; return (name, version) or None if absent/invalid."""
    if not path.exists():
        return None
    data = load_toml(path)
    ref = data.get("harness")
    if not isinstance(ref, str):
        return None
    try:
        return parse_ref(ref)
    except ValueError:
        return None


def _walk_up_for_pointer(start: Path) -> Path | None:
    cur = start.resolve()
    while True:
        candidate = cur / "crux.toml"
        if candidate.exists():
            return candidate
        if cur.parent == cur:
            return None
        cur = cur.parent


def resolve_active(cwd: Path) -> tuple[str, str, str | None, Path] | None:
    """Return ``(scope, name, version, pointer_path)`` or ``None``.

    ``scope`` is ``"directory"`` or ``"user"``.
    """
    found = _walk_up_for_pointer(cwd)
    if found is not None:
        parsed = read_pointer(found)
        if parsed is not None:
            return ("directory", parsed[0], parsed[1], found)
    user_pointer = active_pointer_path()
    parsed = read_pointer(user_pointer)
    if parsed is not None:
        return ("user", parsed[0], parsed[1], user_pointer)
    return None
