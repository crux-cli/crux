"""CLI commands: crux mcp add/remove/list/search/upgrade/status/auth."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from crux_cli.manifest import load_registry, save_registry
from crux_cli.paths import mcps_dir as v1_mcps_dir
from crux_cli.registry import (
    best_package,
    display_name,
    github_slug,
    remote_url,
    search_servers,
    suggest_crux_add,
)
from crux_cli.validation import validate_name


def detect_and_run_build(dest: Path, entry: dict) -> None:
    """Auto-detect build requirements and run the build."""
    pkg_json = dest / "package.json"
    if pkg_json.exists():
        with open(pkg_json) as f:
            pkg = json.load(f)
        if "build" in pkg.get("scripts", {}):
            build_cmd = "npm install && npm run build"
            entry["build_cmd"] = build_cmd
            print("  \U0001f528 Building (npm)...")
            result = subprocess.run(build_cmd, shell=True, cwd=dest, capture_output=True, text=True)  # noqa: S602
            if result.returncode == 0:
                print("  \u2705 Build complete")
            else:
                print(f"  \u26a0\ufe0f  Build failed:\n{result.stderr[-500:].strip()}")


def cmd_mcp_add(args: argparse.Namespace) -> None:
    """crux mcp add <name> — register a new MCP server to the registry."""
    reg = load_registry()
    name = args.name

    ok, reason = validate_name(name)
    if not ok:
        print(f"\u274c Invalid name '{name}': {reason}")
        sys.exit(1)

    registry_key = "mcp_definitions"
    if reg[registry_key].get(name):
        print(f"\u274c MCP '{name}' already exists. Use 'crux mcp remove {name}' first.")
        sys.exit(1)

    entry: dict[str, Any] = {"tags": args.tags.split(",") if args.tags else []}

    keychain_vars = getattr(args, "keychain", None)
    if keychain_vars:
        entry["auth"] = {
            "type": "keychain",
            "env_vars": [v.strip() for v in keychain_vars.split(",")],
            "fix_description": f"Run: crux secret set {name} <VAR> <value>",
        }

    build_cmd = getattr(args, "build_cmd", None)
    if build_cmd:
        entry["build_cmd"] = build_cmd

    if args.uvx:
        base_args = [args.uvx]
        if args.args:
            base_args += args.args.split()
        entry.update({"type": "uvx-package", "command": "uvx", "args": base_args})
    elif args.npx:
        base_args = ["-y", args.npx]
        if args.args:
            base_args += args.args.split()
        entry.update({"type": "npm-package", "command": "npx", "args": base_args})
    elif args.github:
        dest = v1_mcps_dir() / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"  Cloning: {args.github} -> {dest}")
        subprocess.run(  # noqa: S603
            ["git", "clone", f"https://github.com/{args.github}", str(dest)],  # noqa: S607
            check=True,
        )
        entry.update({"type": "github", "source": args.github, "source_dir": str(dest)})
        if args.command:
            run_args = args.args.split() if args.args else []
            entry.update({"command": args.command, "args": run_args})
        detect_and_run_build(dest, entry)
    elif args.local:
        source = Path(args.local).resolve()
        dest = v1_mcps_dir() / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        entry.update({"type": "local", "source_dir": str(dest)})
        if args.command:
            entry.update({"command": args.command, "args": args.args.split() if args.args else []})
    else:
        print("\u274c Specify a source: --uvx <package>, --npx <package>, --github <user/repo>, or --local <path>")
        sys.exit(1)

    reg[registry_key][name] = entry
    save_registry(reg)
    print(f"\u2705 Registered MCP '{name}'")

    # Inline keychain auth: prompt for secrets immediately (interactive terminals only)
    auth_block = entry.get("auth", {})
    if auth_block.get("type") == "keychain" and sys.stdin.isatty():
        try:
            from crux_cli.auth import _auth_keychain

            _auth_keychain(name, auth_block)
        except Exception as e:  # noqa: BLE001
            print(f"  \u26a0\ufe0f  Auth failed: {e} \u2014 run 'crux mcp auth {name}' to retry")


def cmd_mcp_remove(args: argparse.Namespace) -> None:
    """crux mcp remove <name> — unregister an MCP from the registry."""
    reg = load_registry()
    name = args.name
    section = "mcp_definitions"

    if name not in reg.get(section, {}):
        print(f"\u274c '{name}' not found in MCP registry")
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
    print(f"\u2705 Removed MCP '{name}' from registry")
    print("   Note: run 'crux project sync' to regenerate project configurations")


def cmd_mcp_list(args: argparse.Namespace) -> None:
    """crux mcp list — show registered MCP servers."""
    reg = load_registry()
    all_mcps: dict[str, Any] = dict(reg.get("mcp_definitions", {}))

    if getattr(args, "json_output", False):
        print(json.dumps({"mcp_definitions": all_mcps}, indent=2))
        return

    from rich import box
    from rich.console import Console
    from rich.table import Table

    console = Console()

    if not all_mcps:
        print("No MCPs registered. Run 'crux mcp add <name> --npx <package>' to get started.")
        print()
        return

    table = Table(title="MCP Servers", box=box.SIMPLE_HEAVY, show_lines=False, expand=True)
    table.add_column("Name", style="bold cyan", min_width=15, no_wrap=True)
    table.add_column("Type", style="dim", min_width=12, no_wrap=True)
    table.add_column("Description", max_width=40)
    table.add_column("Source", style="blue", max_width=35)
    table.add_column("Auth", style="yellow", no_wrap=True)

    for name, data in sorted(all_mcps.items()):
        mcp_type = data.get("type", "unknown")
        desc = ", ".join(data.get("tags", [])) or ""
        source = data.get("source", "") or data.get("source_dir", "")
        if mcp_type == "npm-package":
            pkg_args = data.get("args", [])
            source = next((a for a in pkg_args if not a.startswith("-")), source)
        elif mcp_type == "uvx-package":
            pkg_args = data.get("args", [])
            source = pkg_args[0] if pkg_args else source
        auth_required = "Yes" if data.get("auth") else "No"
        table.add_row(name, mcp_type, desc, str(source), auth_required)

    console.print(table)
    print()


def cmd_mcp_search(args: argparse.Namespace) -> None:
    """crux mcp search <query> — discover MCP servers from the official registry."""
    from rich import box
    from rich.console import Console
    from rich.table import Table

    console = Console()
    query = args.query

    console.print(f"\n[bold]Searching MCP Registry[/bold] for [cyan]{query!r}[/cyan]...\n")

    try:
        servers = search_servers(query=query, limit=args.limit)
    except RuntimeError as e:
        console.print(f"[red]\u274c {e}[/red]")
        sys.exit(1)

    if not servers:
        console.print("[yellow]No results found.[/yellow]")
        sys.exit(0)

    table = Table(box=box.SIMPLE_HEAVY, show_lines=False, expand=True)
    table.add_column("#", style="dim", width=3, no_wrap=True)
    table.add_column("Name", style="bold cyan", min_width=18, no_wrap=True)
    table.add_column("Description", max_width=55, no_wrap=True)
    table.add_column("Package", style="dim", max_width=35, no_wrap=True)
    table.add_column("GitHub", style="blue", max_width=35, no_wrap=True)

    for i, srv in enumerate(servers, 1):
        name = display_name(srv)
        desc = (srv.get("description") or "").strip()
        if len(desc) > 55:
            desc = desc[:52] + "..."
        reg, pkg = best_package(srv)
        if pkg:
            pkg_str = f"[{reg}] {pkg}"
        else:
            ru = remote_url(srv)
            pkg_str = "[remote]" if ru else "\u2014"
        slug = github_slug(srv)
        gh_str = slug or "\u2014"
        table.add_row(str(i), name, desc, pkg_str, gh_str)

    console.print(table)

    console.print("[bold]To add one to your marketplace:[/bold]")
    for srv in servers[:5]:
        safe_name = display_name(srv).replace(" ", "-").replace("/", "-").lower()
        cmd = suggest_crux_add(safe_name, srv)
        if cmd:
            console.print(f"  [dim]$[/dim] [green]{cmd}[/green]")
    console.print()

    if args.add:
        _search_add(console, servers)


def _search_add(console: object, servers: list[dict]) -> None:
    """Prompt user to pick a server from search results and add it."""
    try:
        choice = input("Enter number to add (or Enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if not choice:
        return
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(servers):
            raise ValueError
    except ValueError:
        console.print("[red]Invalid selection.[/red]")
        return

    srv = servers[idx]
    name = display_name(srv)
    safe_name = name.replace(" ", "-").replace("/", "-").lower()

    reg, pkg = best_package(srv)
    slug = github_slug(srv)

    try:
        custom = input(f"Name in marketplace [{safe_name}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if custom:
        safe_name = custom

    if reg == "npm" and pkg:
        console.print(f"\n[dim]Running:[/dim] crux mcp add {safe_name} --npx {pkg}\n")
        os.execvp("crux", ["crux", "mcp", "add", safe_name, "--npx", pkg])  # noqa: S606, S607
    elif slug:
        console.print(f"\n[dim]Running:[/dim] crux mcp add {safe_name} --github {slug}\n")
        os.execvp("crux", ["crux", "mcp", "add", safe_name, "--github", slug])  # noqa: S606, S607
    else:
        console.print("[yellow]Cannot auto-add \u2014 no npm package or GitHub repo found.[/yellow]")
        console.print(f"Try: crux mcp add {safe_name} --github <user/repo>")


def cmd_mcp_upgrade(args: argparse.Namespace) -> None:
    """crux mcp upgrade — update all/named cloned repos."""
    reg = load_registry()
    dry_run = getattr(args, "dry_run", False)
    target_names = getattr(args, "names", None) or []

    print("\n  CRUX UPGRADE" + (" (dry run)" if dry_run else "") + "\n")

    updated = 0

    all_mcps = dict(reg.get("mcp_definitions", {}))

    cloned_items = {}
    for name, data in all_mcps.items():
        if data.get("type") in ("github", "git-submodule") and data.get("source_dir"):
            if target_names and name not in target_names:
                continue
            cloned_items[name] = data

    for name, data in cloned_items.items():
        source_dir = Path(data["source_dir"])
        if not source_dir.exists():
            continue
        git_dir = source_dir / ".git"
        if not git_dir.exists():
            continue

        status_result = subprocess.run(
            ["git", "status", "--porcelain"],  # noqa: S607
            cwd=source_dir,
            capture_output=True,
            text=True,
        )
        if status_result.stdout.strip():
            print(f"  Warning: {name} has local modifications \u2014 skipping")
            continue

        old_sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            cwd=source_dir,
            capture_output=True,
            text=True,
        )
        old_sha = old_sha_result.stdout.strip()[:8] if old_sha_result.returncode == 0 else "unknown"

        if dry_run:
            subprocess.run(["git", "fetch"], cwd=source_dir, capture_output=True, text=True)  # noqa: S607
            behind = subprocess.run(
                ["git", "rev-list", "HEAD..@{u}", "--count"],  # noqa: S607
                cwd=source_dir,
                capture_output=True,
                text=True,
            )
            count = behind.stdout.strip() if behind.returncode == 0 else "?"
            if count != "0":
                print(f"  {name}: {count} commit(s) behind ({old_sha})")
                updated += 1
            else:
                print(f"  {name}: up to date ({old_sha})")
            continue

        pull_result = subprocess.run(
            ["git", "pull", "--ff-only"],  # noqa: S607
            cwd=source_dir,
            capture_output=True,
            text=True,
        )
        if pull_result.returncode != 0:
            print(f"  Warning: {name} pull failed \u2014 {pull_result.stderr.strip()}")
            continue

        new_sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            cwd=source_dir,
            capture_output=True,
            text=True,
        )
        new_sha = new_sha_result.stdout.strip()[:8] if new_sha_result.returncode == 0 else "unknown"

        if old_sha != new_sha:
            print(f"  {name}: {old_sha} -> {new_sha}")
            updated += 1

            build_cmd = data.get("build_cmd")
            if build_cmd:
                print(f"    Rebuilding ({build_cmd})...")
                build_result = subprocess.run(  # noqa: S602
                    build_cmd,
                    shell=True,
                    cwd=source_dir,
                    capture_output=True,
                    text=True,
                )
                if build_result.returncode == 0:
                    print("    Build complete")
                else:
                    print(f"    Warning: build failed \u2014 {build_result.stderr[-300:].strip()}")
        else:
            print(f"  {name}: up to date ({old_sha})")

    if dry_run:
        if updated:
            print(f"\n  {updated} item(s) have updates available\n")
        else:
            print("\n  Everything is up to date\n")
    else:
        print(f"\n  Upgrade complete ({updated} updated)\n")


_STATUS_STYLE = {
    "connected": "[bold green]connected[/]",
    "running": "[yellow]running[/]",
    "auth_required": "[bold red]auth_required[/]",
    "timeout": "[red]timeout[/]",
    "error": "[red]error[/]",
    "failed": "[bold red]failed[/]",
}


def cmd_mcp_status(args: argparse.Namespace) -> None:
    """crux mcp status — probe every MCP in the global registry."""
    from rich.console import Console
    from rich.table import Table

    from crux_cli.health import probe_mcp_server_detailed
    from crux_cli.mcp_config import enrich_with_marketplace

    print("\nChecking MCP server health...\n")

    reg = load_registry()
    mcp_definitions = dict(reg.get("mcp_definitions", {}))

    if not mcp_definitions:
        print("No MCPs registered. Run 'crux mcp add <name> --npx <package>' to get started.")
        print()
        return

    # Build a config dict for each MCP from its registry definition
    servers: dict[str, Any] = {}
    for name, data in mcp_definitions.items():
        config: dict[str, Any] = {}
        mcp_type = data.get("type", "")
        if mcp_type in ("npm-package", "uvx-package") or mcp_type in ("github", "local"):
            config["command"] = data.get("command", "")
            config["args"] = data.get("args", [])
        else:
            config["command"] = data.get("command", "")
            config["args"] = data.get("args", [])
        if data.get("env"):
            config["env"] = data["env"]
        servers[name] = config

    enriched = enrich_with_marketplace(servers, mcp_definitions)

    rows = []
    for name, config in enriched.items():
        result = probe_mcp_server_detailed(config)
        rows.append(
            {
                "name": name,
                "status": result["status"],
                "tools_count": result["tools_count"],
                "detail": result["detail"],
            }
        )

    console = Console()
    table = Table(title="MCP Server Status (Global Registry)", show_lines=False)
    table.add_column("MCP Name", style="cyan", no_wrap=True)
    table.add_column("Status")
    table.add_column("Tools", justify="right")
    table.add_column("Detail")

    for r in rows:
        styled = _STATUS_STYLE.get(r["status"], r["status"])
        tools_str = str(r["tools_count"]) if r["tools_count"] is not None else "-"
        table.add_row(r["name"], styled, tools_str, r.get("detail", ""))

    console.print(table)
    print()


def cmd_mcp_auth(args: argparse.Namespace) -> None:
    """crux mcp auth — authenticate MCP servers."""
    from crux_cli.auth import auth_all, auth_single, auth_status

    name = getattr(args, "name", None)
    do_all = getattr(args, "all", False)

    values = getattr(args, "value", None)

    if name:
        # Parse --value KEY=VALUE pairs into a dict
        inline_values: dict[str, str] | None = None
        if values:
            inline_values = {}
            for pair in values:
                if "=" not in pair:
                    print(f"\u274c Invalid --value format: '{pair}' (expected KEY=VALUE)")
                    sys.exit(1)
                k, v = pair.split("=", 1)
                inline_values[k] = v
        auth_single(name, inline_values=inline_values)
    elif do_all:
        auth_all()
    else:
        # Show auth status table
        from rich import box
        from rich.console import Console
        from rich.table import Table

        statuses = auth_status()
        if not statuses:
            print("No MCPs have authentication configured.")
            return

        console = Console()
        table = Table(title="MCP Authentication Status", box=box.SIMPLE_HEAVY, show_lines=False)
        table.add_column("Name", style="bold cyan", no_wrap=True)
        table.add_column("Auth Type", style="dim")
        table.add_column("Status")

        status_styles = {
            "Authenticated": "[green]Authenticated[/]",
            "Not authenticated": "[bold red]Not authenticated[/]",
            "Token not set": "[bold red]Token not set[/]",
            "Expired": "[bold red]Expired[/]",
            "Refresh needed": "[yellow]Refresh needed[/]",
            "Check failed": "[red]Check failed[/]",
        }

        for s in statuses:
            styled = status_styles.get(s["status"], s["status"])
            if s["status"].startswith("Missing:"):
                styled = f"[red]{s['status']}[/]"
            elif s["status"].startswith("Expires in"):
                styled = f"[yellow]{s['status']}[/]"
            table.add_row(s["name"], s["auth_type"], styled)

        console.print(table)
        print("\nRun: crux mcp auth <name>  to authenticate")
        print("     crux mcp auth --all   to authenticate all")
