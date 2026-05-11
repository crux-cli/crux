"""Crux v2 CLI entry point."""

from __future__ import annotations

import argparse
import sys

from crux_cli.activation import ConflictError


def _build_parser() -> argparse.ArgumentParser:
    from crux_cli.cli.commands.doctor_cmd import cmd_doctor
    from crux_cli.cli.commands.harness_cmd import (
        cmd_bump,
        cmd_edit,
        cmd_list,
        cmd_new,
        cmd_show,
    )
    from crux_cli.cli.commands.migrate_cmd import cmd_migrate
    from crux_cli.cli.commands.registry_cmd import (
        cmd_registry_add,
        cmd_registry_list,
        cmd_registry_remove,
    )
    from crux_cli.cli.commands.secret_cmd import (
        cmd_secret_list,
        cmd_secret_remove,
        cmd_secret_set,
    )
    from crux_cli.cli.commands.setup_cmd import cmd_setup
    from crux_cli.cli.commands.use_cmd import cmd_active, cmd_use

    p = argparse.ArgumentParser(prog="crux", description="Crux — Harness manager for Claude Code")
    sub = p.add_subparsers(dest="command", required=True)

    # ── Setup / doctor / migrate ────────────────────────────────────────
    sub.add_parser("setup", help="Initialize ~/.crux").set_defaults(func=cmd_setup)
    sub.add_parser("doctor", help="Diagnose the environment").set_defaults(func=cmd_doctor)
    m = sub.add_parser("migrate", help="Migrate the cwd's crux.json into a v2 harness")
    m.add_argument("--name", help="Override harness name")
    m.set_defaults(func=cmd_migrate)

    # ── Registry ────────────────────────────────────────────────────────
    rp = sub.add_parser("registry", help="Manage MCPs, skills, plugins")
    rs = rp.add_subparsers(dest="reg_cmd", required=True)
    ra = rs.add_parser("add", help="Register an MCP, skill, or plugin")
    ra.add_argument("kind", choices=["mcp", "skill", "plugin"])
    ra.add_argument("name")
    ra.add_argument("source")
    ra.add_argument("--npm", action="store_true")
    ra.add_argument("--uvx", action="store_true")
    ra.add_argument("--github", action="store_true")
    ra.add_argument("--local", action="store_true")
    ra.add_argument("--http", action="store_true")
    ra.add_argument("--keychain", help="Comma-separated env vars for keychain auth")
    ra.add_argument("--args", help="Extra args, space-separated")
    ra.add_argument("--skip-install", action="store_true")
    ra.add_argument("--version", default="v1", help="Plugin version (default v1)")
    ra.set_defaults(func=cmd_registry_add)

    rr = rs.add_parser("remove", help="Unregister a primitive")
    rr.add_argument("name")
    rr.add_argument("--force", action="store_true")
    rr.set_defaults(func=cmd_registry_remove)

    rl = rs.add_parser("list", help="List registered primitives")
    rl.set_defaults(func=cmd_registry_list)

    # ── Secret ──────────────────────────────────────────────────────────
    sp = sub.add_parser("secret", help="Manage credentials")
    ss = sp.add_subparsers(dest="secret_cmd", required=True)
    sset = ss.add_parser("set")
    sset.add_argument("mcp")
    sset.add_argument("key")
    sset.add_argument("--value", help="Value (otherwise prompted)")
    sset.set_defaults(func=cmd_secret_set)
    sl = ss.add_parser("list")
    sl.add_argument("mcp", nargs="?")
    sl.set_defaults(func=cmd_secret_list)
    srm = ss.add_parser("remove")
    srm.add_argument("mcp")
    srm.add_argument("key")
    srm.set_defaults(func=cmd_secret_remove)

    # ── Harness lifecycle ───────────────────────────────────────────────
    n = sub.add_parser("new", help="Create a new harness at v1")
    n.add_argument("name")
    n.set_defaults(func=cmd_new)

    b = sub.add_parser("bump", help="Create the next version from the latest")
    b.add_argument("name")
    b.set_defaults(func=cmd_bump)

    li = sub.add_parser("list", help="List harnesses or versions of a harness")
    li.add_argument("name", nargs="?")
    li.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="Display the bundle for a harness")
    sh.add_argument("ref")
    sh.set_defaults(func=cmd_show)

    # ── Edit ────────────────────────────────────────────────────────────
    ep = sub.add_parser("edit", help="Edit parts of a harness")
    es = ep.add_subparsers(dest="edit_what", required=True)
    for what in ("claude", "skills", "mcps", "plugins", "hooks"):
        sub_e = es.add_parser(what)
        sub_e.add_argument("ref", nargs="?")
        sub_e.add_argument("--add", action="append", default=[])
        sub_e.add_argument("--remove", action="append", default=[])
        sub_e.set_defaults(func=cmd_edit, edit_what=what)

    # ── Activation ──────────────────────────────────────────────────────
    u = sub.add_parser("use", help="Activate a harness (or '-' for previous)")
    u.add_argument("ref", nargs="?")
    u.add_argument("--user", action="store_true")
    u.add_argument("--none", action="store_true")
    u.set_defaults(func=cmd_use)
    sub.add_parser("active", help="Show the active harness").set_defaults(func=cmd_active)

    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except FileNotFoundError as e:
        print(f"crux: not found: {e}", file=sys.stderr)
        sys.exit(2)
    except FileExistsError as e:
        print(f"crux: exists: {e}", file=sys.stderr)
        sys.exit(3)
    except ConflictError as e:
        print(f"crux: conflict: {e}", file=sys.stderr)
        sys.exit(3)
    except RuntimeError as e:
        print(f"crux: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
