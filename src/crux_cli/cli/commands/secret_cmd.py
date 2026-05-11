"""``crux secret set/list/remove`` — manage credentials referenced by MCPs."""

from __future__ import annotations

import argparse
import getpass

from crux_cli.secrets import get_backend


def cmd_secret_set(args: argparse.Namespace) -> None:
    val = args.value or getpass.getpass(f"value for {args.mcp}/{args.key}: ")
    get_backend().set(args.mcp, args.key, val)
    print(f"secret: set {args.mcp}/{args.key}")


def cmd_secret_list(args: argparse.Namespace) -> None:
    keys = get_backend().list_keys(getattr(args, "mcp", None))
    for mcp, names in keys.items():
        print(f"{mcp}: {', '.join(names)}")


def cmd_secret_remove(args: argparse.Namespace) -> None:
    get_backend().delete(args.mcp, args.key)
    print(f"secret: removed {args.mcp}/{args.key}")
