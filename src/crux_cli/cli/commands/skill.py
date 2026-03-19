"""CLI commands: crux skill add/remove/list."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from crux_cli.manifest import load_registry, save_registry
from crux_cli.paths import skills_dir as v1_skills_dir
from crux_cli.validation import validate_name


def cmd_skill_add(args: argparse.Namespace) -> None:
    """crux skill add <name> — register a new skill."""
    reg = load_registry()
    name = args.name

    ok, reason = validate_name(name)
    if not ok:
        print(f"✖ Invalid name '{name}': {reason}")
        sys.exit(1)

    registry_key = "skill_definitions"
    if reg[registry_key].get(name):
        print(f"✖ Skill '{name}' already exists. Use 'crux skill remove {name}' first.")
        sys.exit(1)

    entry = {"tags": args.tags.split(",") if args.tags else []}

    if args.github:
        dest = v1_skills_dir() / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"  Cloning: {args.github} -> {dest}")
        subprocess.run(  # noqa: S603
            ["git", "clone", f"https://github.com/{args.github}", str(dest)],  # noqa: S607
            check=True,
        )
        entry.update({"type": "github", "source": args.github, "source_dir": str(dest)})
        if not (dest / "SKILL.md").exists():
            print(f"  Warning: No SKILL.md found in {dest}. Consider adding one for discoverability.")
    elif args.local:
        source = Path(args.local).resolve()
        dest = v1_skills_dir() / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        entry.update({"type": "local", "source_dir": str(dest)})
        if not (dest / "SKILL.md").exists():
            print(f"  Warning: No SKILL.md found in {dest}. Consider adding one for discoverability.")
    else:
        print("✖ Specify a source: --github <user/repo> or --local <path>")
        sys.exit(1)

    reg[registry_key][name] = entry
    save_registry(reg)
    print(f"✅ Registered skill '{name}'")


def cmd_skill_remove(args: argparse.Namespace) -> None:
    """crux skill remove <name> — unregister a skill."""
    reg = load_registry()
    name = args.name
    section = "skill_definitions"

    if name not in reg.get(section, {}):
        print(f"✖ Skill '{name}' not found in registry")
        sys.exit(1)

    data = reg[section][name]
    source_dir = data.get("source_dir")
    if source_dir and Path(source_dir).exists() and data.get("type") in ("github", "local"):
        from crux_cli.paths import crux_home

        resolved = Path(source_dir).resolve()
        if str(resolved).startswith(str(crux_home().resolve())):
            shutil.rmtree(source_dir)
            print(f"  Deleted cloned source: {source_dir}")
        else:
            print(f"  Skipped deletion: {source_dir} is outside ~/.crux/")

    del reg[section][name]
    save_registry(reg)
    print(f"✅ Removed skill '{name}' from registry")
    print("   Note: run 'crux project sync' to regenerate project configurations")


def cmd_skill_list(args: argparse.Namespace) -> None:
    """crux skill list — show registered skills."""
    reg = load_registry()
    all_skills = dict(reg.get("skill_definitions", {}))

    if getattr(args, "json_output", False):
        print(json.dumps({"skill_definitions": all_skills}, indent=2))
        return

    from rich import box
    from rich.console import Console
    from rich.table import Table

    console = Console()

    if not all_skills:
        print("No skills registered. Run 'crux skill add <name> --github <repo>' to get started.")
        print()
        return

    table = Table(title="Skills", box=box.SIMPLE_HEAVY, show_lines=False, expand=True)
    table.add_column("Name", style="bold cyan", min_width=15, no_wrap=True)
    table.add_column("Type", style="dim", min_width=12, no_wrap=True)
    table.add_column("Description", max_width=40)
    table.add_column("Source", style="blue", max_width=35)

    for name, data in sorted(all_skills.items()):
        skill_type = data.get("type", "unknown")
        desc = ", ".join(data.get("tags", [])) or ""
        source = data.get("source", "") or data.get("source_dir", "")
        table.add_row(name, skill_type, desc, str(source))

    console.print(table)
    print()
