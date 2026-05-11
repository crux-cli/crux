"""``crux use`` (activate, rollback, deactivate) and ``crux active`` (show)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from crux_cli import history, paths, store
from crux_cli.activation import activate, remove_managed_symlinks
from crux_cli.pointer import parse_ref, read_pointer, resolve_active, write_pointer


def _pointer_path(scope: str, cwd: Path) -> Path:
    return paths.active_pointer_path() if scope == "user" else cwd / "crux.toml"


def _history_path(scope: str, cwd: Path) -> Path:
    return paths.history_path() if scope == "user" else cwd / ".crux" / "history"


def _scope_target(scope: str, cwd: Path) -> Path:
    return paths.claude_user_dir() if scope == "user" else paths.claude_dir_for(cwd)


def _previous_ref_string(pointer: Path) -> str:
    parsed = read_pointer(pointer)
    if parsed is None:
        return ""
    name, version = parsed
    if version is None:
        version = store.latest_version(name) or "v?"
    return f"{name}@{version}"


def cmd_use(args: argparse.Namespace) -> None:
    cwd = Path.cwd()
    scope = "user" if args.user else "directory"
    pointer = _pointer_path(scope, cwd)

    if args.none:
        if pointer.exists():
            pointer.unlink()
        remove_managed_symlinks(_scope_target(scope, cwd))
        print(f"use: deactivated ({scope})")
        return

    ref = args.ref
    if ref == "-":
        prev = history.pop_previous(_history_path(scope, cwd))
        if not prev:
            print("crux: use: no previous harness in history", file=sys.stderr)
            sys.exit(3)
        ref = prev

    if not ref:
        print("crux: use: missing harness reference", file=sys.stderr)
        sys.exit(1)

    name, version = parse_ref(ref)
    if version is None:
        version = store.latest_version(name)
        if version is None:
            raise FileNotFoundError(f"harness '{name}'")

    prev_ref = _previous_ref_string(pointer)

    activate(name, version, scope=scope, cwd=cwd)
    write_pointer(pointer, f"{name}@{version}")
    history.append(_history_path(scope, cwd), prev=prev_ref or None, new=f"{name}@{version}")
    print(f"use: {name}@{version} ({scope})")


def cmd_active(_args: argparse.Namespace) -> None:
    res = resolve_active(Path.cwd())
    if res is None:
        print("active: (none)")
        return
    scope, name, version, pointer_path = res
    print(f"active: {name}@{version or 'latest'} ({scope}, {pointer_path})")
