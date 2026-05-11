"""``crux registry add/remove/list``."""

from __future__ import annotations

import argparse
from pathlib import Path

from crux_cli import store
from crux_cli.registry_ops import (
    add_mcp,
    add_plugin_local,
    add_skill_github,
    add_skill_local,
    remove,
)


def _resolve_mcp_kind(args: argparse.Namespace) -> str:
    flags = [
        ("npm", args.npm),
        ("uvx", args.uvx),
        ("github", args.github),
        ("local", args.local),
        ("http", args.http),
    ]
    chosen = [name for name, on in flags if on]
    if len(chosen) > 1:
        raise SystemExit("crux: registry add: pick at most one of --npm/--uvx/--github/--local/--http")
    return chosen[0] if chosen else "npm"


def cmd_registry_add(args: argparse.Namespace) -> None:
    extra_args = args.args.split() if getattr(args, "args", None) else []
    keychain = [v.strip() for v in args.keychain.split(",") if v.strip()] if getattr(args, "keychain", None) else None
    if args.kind == "mcp":
        add_mcp(
            args.name,
            source_kind=_resolve_mcp_kind(args),
            source=args.source,
            args=extra_args,
            keychain=keychain,
            skip_install=args.skip_install,
        )
        print(f"registry: added mcp {args.name}")
    elif args.kind == "skill":
        if args.github:
            add_skill_github(args.name, args.source)
        else:
            add_skill_local(args.name, Path(args.source))
        print(f"registry: added skill {args.name}")
    elif args.kind == "plugin":
        add_plugin_local(args.name, Path(args.source), version=args.version)
        print(f"registry: added plugin {args.name}@{args.version}")


def cmd_registry_remove(args: argparse.Namespace) -> None:
    remove(args.name, force=args.force)
    print(f"registry: removed {args.name}")


def cmd_registry_list(_args: argparse.Namespace) -> None:
    print("# mcps:")
    for n in store.list_mcps():
        print(f"  {n}")
    print("# skills:")
    for n in store.list_skills():
        print(f"  {n}")
    print("# plugins:")
    for n in store.list_plugins():
        for v in store.plugin_versions(n):
            print(f"  {n}@{v}")
