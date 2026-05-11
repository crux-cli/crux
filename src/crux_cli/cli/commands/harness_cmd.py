"""``crux new/bump/list/show/edit`` — harness lifecycle and bundle editing."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from crux_cli import store
from crux_cli.bundle import load_bundle, save_bundle
from crux_cli.harness_ops import bump, new_harness
from crux_cli.pointer import parse_ref, resolve_active


def cmd_new(args: argparse.Namespace) -> None:
    hdir = new_harness(args.name)
    print(f"new: created {args.name}@v1 at {hdir}")


def cmd_bump(args: argparse.Namespace) -> None:
    hdir = bump(args.name)
    print(f"bump: created {args.name}@{hdir.name}")


def cmd_list(args: argparse.Namespace) -> None:
    name = getattr(args, "name", None)
    if name:
        for v in store.harness_versions(name):
            print(v)
        return
    for h in store.list_harnesses():
        versions = store.harness_versions(h)
        print(f"{h}: {', '.join(versions)}")


def _resolve_ref(ref: str) -> tuple[str, str]:
    name, version = parse_ref(ref)
    if version is None:
        version = store.latest_version(name)
        if version is None:
            raise FileNotFoundError(f"harness '{name}'")
    return name, version


def cmd_show(args: argparse.Namespace) -> None:
    name, version = _resolve_ref(args.ref)
    hdir = store.harness_dir(name, version)
    bundle = load_bundle(hdir)
    print(f"# {name}@{version}")
    desc = bundle.get("harness", {}).get("description", "")
    if desc:
        print(f"description: {desc}")
    print(f"skills:  {', '.join(bundle['skills']['include'])}")
    print(f"mcps:    {', '.join(bundle['mcps']['include'])}")
    print(f"plugins: {', '.join(bundle['plugins']['include'])}")
    hooks = bundle.get("hooks", {}) or {}
    if hooks:
        print("hooks:")
        for k, v in hooks.items():
            print(f"  {k} = {v}")


def _active_ref_or_arg(args: argparse.Namespace) -> tuple[str, str]:
    ref = getattr(args, "ref", None)
    if ref:
        return _resolve_ref(ref)
    res = resolve_active(Path.cwd())
    if res is None:
        print("crux: edit: no active harness, pass a ref", file=sys.stderr)
        sys.exit(2)
    _scope, name, version, _ = res
    if version is None:
        version = store.latest_version(name)
        if version is None:
            raise FileNotFoundError(f"harness '{name}'")
    return name, version


def cmd_edit(args: argparse.Namespace) -> None:
    name, version = _active_ref_or_arg(args)
    hdir = store.harness_dir(name, version)
    what = args.edit_what

    if what == "claude":
        editor = os.environ.get("EDITOR", "vi")
        subprocess.run([editor, str(hdir / "CLAUDE.md")], check=False)  # noqa: S603
        return

    if what == "hooks":
        (hdir / "hooks").mkdir(exist_ok=True)
        editor = os.environ.get("EDITOR", "vi")
        subprocess.run([editor, str(hdir / "hooks")], check=False)  # noqa: S603
        return

    bundle = load_bundle(hdir)
    key = {"skills": "skills", "mcps": "mcps", "plugins": "plugins"}[what]
    include: list[str] = list(bundle[key]["include"])
    for item in args.add or []:
        if item not in include:
            include.append(item)
    for item in args.remove or []:
        if item in include:
            include.remove(item)
    bundle[key]["include"] = include
    save_bundle(hdir, bundle)
    print(f"edit {what}: {', '.join(include)}")
