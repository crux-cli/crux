# CLI Restructuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the crux CLI from flat top-level commands to resource-first namespaces (`mcp`, `skill`, `project`, `task`), rename `setup` to `init`, and remove auth checks from `doctor`.

**Architecture:** Rewrite `main.py` with nested argparse subparsers. Split `commands/registry.py` into `commands/mcp.py` and `commands/skill.py`. Rename `commands/sandbox.py` to `commands/task.py`. Rename project commands. Delete `commands/secrets.py` (placeholder — unified auth comes in a later plan). All core modules (`secrets.py`, `sync.py`, `health.py`, etc.) remain unchanged except for fix-hint string updates.

**Tech Stack:** Python 3.11+, argparse, pytest, ruff

**Spec:** `docs/superpowers/specs/2026-03-19-cli-reorg-and-unified-auth-design.md`

**Scope:** This plan covers ONLY the CLI restructuring (Spec Sections 1, 3, parts of 5-6). Auth system, bridge, OAuth, and docs are separate plans.

---

## File Map

### New Files
| File | Responsibility |
|---|---|
| `src/crux_cli/cli/commands/mcp.py` | All `crux mcp *` handlers: add, remove, list, search, upgrade, status. Auth placeholder. |
| `src/crux_cli/cli/commands/skill.py` | All `crux skill *` handlers: add, remove, list |
| `src/crux_cli/cli/commands/task.py` | All `crux task *` handlers: run, init, list, clean (moved from sandbox.py) |
| `tests/integration/test_cli_project_create.py` | Integration tests for `crux project create` |
| `tests/integration/test_cli_mcp.py` | Integration tests for `crux mcp add/remove/list/search/upgrade` |
| `tests/integration/test_cli_skill.py` | Integration tests for `crux skill add/remove/list` |
| `tests/integration/test_cli_project_sync.py` | Integration tests for `crux project sync` |
| `tests/integration/test_cli_task.py` | Integration tests for `crux task init/list/clean` |

### Modified Files
| File | Changes |
|---|---|
| `src/crux_cli/cli/main.py` | Complete rewrite: nested subparsers |
| `src/crux_cli/cli/commands/doctor.py` | `cmd_setup` → `cmd_init`; remove MCP-specific setup branch; remove secrets from doctor |
| `src/crux_cli/cli/commands/project.py` | Rename: `cmd_init` → `cmd_project_create` (add `--mcp`/`--skill` flags), `cmd_install` → `cmd_project_install`, etc. |
| `src/crux_cli/health.py` | Remove `check_secrets_consistency`; update fix hints to new command names |
| `src/crux_cli/preflight.py` | Update fix hint strings to new command names |
| `src/crux_cli/registry.py` (core) | Update `suggest_crux_add` output: `"crux add mcp"` → `"crux mcp add"` |
| `src/crux_cli/data/skills/crux/SKILL.md` | Rewrite with new command names |
| `tests/unit/test_health.py` | Remove `test_check_secrets_consistency*` tests |
| `tests/unit/test_preflight.py` | Update expected fix hint strings |
| `tests/unit/test_registry.py` | Update expected `suggest_crux_add` output |

### Deleted Files
| File | Reason |
|---|---|
| `src/crux_cli/cli/commands/secrets.py` | Absorbed by `crux mcp auth` (later plan) — replaced with stub in `mcp.py` |
| `src/crux_cli/cli/commands/sandbox.py` | Renamed to `task.py` |
| `tests/integration/test_cli_init.py` | Replaced by `test_cli_project_create.py` |
| `tests/integration/test_cli_add_remove.py` | Replaced by `test_cli_mcp.py` + `test_cli_skill.py` |
| `tests/integration/test_cli_list.py` | Merged into `test_cli_mcp.py` + `test_cli_skill.py` |
| `tests/integration/test_cli_secret.py` | Replaced in later plan (`test_cli_mcp_auth.py`) |
| `tests/integration/test_cli_sync.py` | Replaced by `test_cli_project_sync.py` |
| `tests/integration/test_cli_run.py` | Replaced by `test_cli_task.py` |
| `tests/integration/test_cli_doctor.py` | Rewritten in place |

---

## Task 1: Rewrite `main.py` — Argument Parser

**Files:**
- Modify: `src/crux_cli/cli/main.py` (complete rewrite)

- [ ] **Step 1: Read the current `main.py`**

Read `src/crux_cli/cli/main.py` to understand current structure. Note all 15 commands and their arguments.

- [ ] **Step 2: Write the new `main.py`**

Replace the entire file. The new parser has 4 namespace subparsers (`mcp`, `skill`, `project`, `task`) plus 3 top-level commands (`init`, `doctor`, `version`).

```python
"""Entry point for the crux CLI."""

from __future__ import annotations

import argparse


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate command handler."""
    from crux_cli.cli.commands.doctor import cmd_doctor, cmd_init
    from crux_cli.cli.commands.mcp import (
        cmd_mcp_add,
        cmd_mcp_auth,
        cmd_mcp_list,
        cmd_mcp_remove,
        cmd_mcp_search,
        cmd_mcp_status,
        cmd_mcp_upgrade,
    )
    from crux_cli.cli.commands.project import (
        cmd_project_create,
        cmd_project_install,
        cmd_project_status,
        cmd_project_sync,
        cmd_project_uninstall,
    )
    from crux_cli.cli.commands.skill import cmd_skill_add, cmd_skill_list, cmd_skill_remove
    from crux_cli.cli.commands.task import cmd_task
    from crux_cli.cli.commands.version import cmd_version

    parser = argparse.ArgumentParser(description="Crux — Agentic Tool Manager for Claude Code")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── crux init ──────────────────────────────────────────────────────
    subparsers.add_parser("init", help="Initialise ~/.crux/").set_defaults(func=cmd_init)

    # ── crux doctor ────────────────────────────────────────────────────
    subparsers.add_parser("doctor", help="Check Crux environment health").set_defaults(func=cmd_doctor)

    # ── crux version ───────────────────────────────────────────────────
    p = subparsers.add_parser("version", help="Show crux-cli version")
    p.add_argument("--check", action="store_true", help="Check for updates")
    p.set_defaults(func=cmd_version)

    # ── crux mcp ───────────────────────────────────────────────────────
    mcp_parser = subparsers.add_parser("mcp", help="Manage MCP servers")
    mcp_sub = mcp_parser.add_subparsers(dest="mcp_command", required=True)

    p = mcp_sub.add_parser("add", help="Register a new MCP server")
    p.add_argument("name", help="Name for the MCP")
    p.add_argument("--uvx", help="PyPI package to run via uvx")
    p.add_argument("--npx", help="npm package")
    p.add_argument("--github", help="GitHub repo (e.g. user/repo)")
    p.add_argument("--local", help="Local directory path")
    p.add_argument("--command", help="Command to run the MCP")
    p.add_argument("--args", help="Args for the command, space-separated")
    p.add_argument("--tags", help="Comma-separated tags")
    p.add_argument("--keychain", help="Comma-separated env var names for keychain auth")
    p.add_argument("--build-cmd", dest="build_cmd", help="Build command after clone")
    p.add_argument("--setup-cmd", dest="setup_cmd", help="Setup command after registration")
    p.set_defaults(func=cmd_mcp_add)

    p = mcp_sub.add_parser("remove", help="Unregister an MCP server")
    p.add_argument("name", help="Name to remove")
    p.set_defaults(func=cmd_mcp_remove)

    p = mcp_sub.add_parser("list", help="List registered MCP servers")
    p.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_mcp_list)

    p = mcp_sub.add_parser("search", help="Search the official MCP Registry")
    p.add_argument("query", help="Search query")
    p.add_argument("--limit", type=int, default=20, metavar="N", help="Max results (default: 20)")
    p.add_argument("--add", action="store_true", help="Interactively add a result")
    p.set_defaults(func=cmd_mcp_search)

    p = mcp_sub.add_parser("upgrade", help="Update cloned repos")
    p.add_argument("names", nargs="*", help="Specific names to upgrade (default: all)")
    p.add_argument("--dry-run", action="store_true", help="Show what would be updated")
    p.set_defaults(func=cmd_mcp_upgrade)

    p = mcp_sub.add_parser("auth", help="Authenticate MCP servers")
    p.add_argument("name", nargs="?", help="MCP name (omit to show auth status)")
    p.add_argument("--all", action="store_true", help="Authenticate all MCPs needing auth")
    p.add_argument("--refresh", action="store_true", help="Refresh OAuth token only")
    p.set_defaults(func=cmd_mcp_auth)

    p = mcp_sub.add_parser("status", help="Probe all registered MCP servers")
    p.set_defaults(func=cmd_mcp_status)

    # ── crux skill ─────────────────────────────────────────────────────
    skill_parser = subparsers.add_parser("skill", help="Manage skills")
    skill_sub = skill_parser.add_subparsers(dest="skill_command", required=True)

    p = skill_sub.add_parser("add", help="Register a new skill")
    p.add_argument("name", help="Name for the skill")
    p.add_argument("--github", help="GitHub repo (e.g. user/repo)")
    p.add_argument("--local", help="Local directory path")
    p.add_argument("--tags", help="Comma-separated tags")
    p.add_argument("--build-cmd", dest="build_cmd", help="Build command after clone")
    p.set_defaults(func=cmd_skill_add)

    p = skill_sub.add_parser("remove", help="Unregister a skill")
    p.add_argument("name", help="Name to remove")
    p.set_defaults(func=cmd_skill_remove)

    p = skill_sub.add_parser("list", help="List registered skills")
    p.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_skill_list)

    # ── crux project ───────────────────────────────────────────────────
    proj_parser = subparsers.add_parser("project", help="Manage projects")
    proj_sub = proj_parser.add_subparsers(dest="project_command", required=True)

    p = proj_sub.add_parser("create", help="Scaffold a new project")
    p.add_argument("name", nargs="?", default=None, help="Project name")
    p.add_argument("--mcp", dest="mcps", help="Comma-separated MCP names to install")
    p.add_argument("--skill", dest="skills", help="Comma-separated skill names to install")
    p.set_defaults(func=cmd_project_create)

    p = proj_sub.add_parser("install", help="Add MCPs/skills to current project and sync")
    p.add_argument("names", nargs="+", help="Names of MCPs or skills to install")
    p.set_defaults(func=cmd_project_install)

    p = proj_sub.add_parser("uninstall", help="Remove MCPs/skills from current project and sync")
    p.add_argument("names", nargs="+", help="Names of MCPs or skills to uninstall")
    p.set_defaults(func=cmd_project_uninstall)

    p = proj_sub.add_parser("sync", help="Sync projects: read crux.json, generate .mcp.json")
    p.add_argument("--all", action="store_true", help="Sync all tracked projects")
    p.set_defaults(func=cmd_project_sync)

    p = proj_sub.add_parser("status", help="Show project health (MCPs, skills, auth)")
    p.add_argument("--all", action="store_true", help="All tracked projects")
    p.set_defaults(func=cmd_project_status)

    # ── crux task ──────────────────────────────────────────────────────
    task_parser = subparsers.add_parser("task", help="Run agent tasks in sandboxes")
    task_sub = task_parser.add_subparsers(dest="task_command", required=True)

    p = task_sub.add_parser("run", help="Run an agent in an isolated sandbox")
    p.add_argument("task", help="Task string")
    p.add_argument("--mcp", nargs="*", default=[], dest="mcps", metavar="mcp", help="MCPs to enable")
    p.add_argument("--keep", action="store_true", help="Keep sandbox after run")
    p.add_argument("--no-stream", dest="no_stream", action="store_true", help="Collect output instead of streaming")
    p.add_argument("--file", "-f", metavar="run.json", help="Load from manifest file")
    p.set_defaults(func=cmd_task)

    p = task_sub.add_parser("init", help="Scaffold a run.json template")
    p.add_argument("name", nargs="?", default=None, metavar="name", help="Name for the run")
    p.set_defaults(func=cmd_task)

    p = task_sub.add_parser("list", help="Show past/active runs")
    p.set_defaults(func=cmd_task)

    p = task_sub.add_parser("clean", help="Remove completed sandboxes")
    p.add_argument("--force", action="store_true", help="Skip confirmation")
    p.set_defaults(func=cmd_task)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify syntax**

Run: `python -c "import ast; ast.parse(open('src/crux_cli/cli/main.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/crux_cli/cli/main.py
git commit -m "refactor: rewrite CLI parser with resource-first namespaces"
```

---

## Task 2: Create `commands/mcp.py`

**Files:**
- Create: `src/crux_cli/cli/commands/mcp.py`

This file absorbs all MCP-related handlers from `commands/registry.py` (add, remove, list, search, upgrade) plus a new `cmd_mcp_status` (global MCP probing) and a placeholder `cmd_mcp_auth`.

- [ ] **Step 1: Read `commands/registry.py`**

Read the entire file to understand `cmd_add`, `cmd_remove`, `cmd_list`, `cmd_search`, `cmd_upgrade`, `_search_add`, and `detect_and_run_build`. Note that `cmd_add` handles both MCPs and skills — we only take the MCP branch.

- [ ] **Step 2: Read `commands/project.py` for status logic**

Read `cmd_status` and `_probe_project_servers` — the `--all` path probes across projects. `cmd_mcp_status` (new) will probe ALL registered MCPs globally, regardless of project.

- [ ] **Step 3: Create `commands/mcp.py`**

Extract MCP-specific code from `registry.py`. Key changes:
- `cmd_add` MCP branch → `cmd_mcp_add` (standalone function, no `entry_type` argument)
- `cmd_remove` → `cmd_mcp_remove` (only searches `mcp_definitions`)
- `cmd_list` → `cmd_mcp_list` (only shows MCPs, no `--type` filter needed)
- `cmd_search` → `cmd_mcp_search` (unchanged logic)
- `cmd_upgrade` → `cmd_mcp_upgrade` (unchanged logic)
- `_search_add` → update `os.execvp` calls: `["crux", "add", "mcp", ...]` → `["crux", "mcp", "add", ...]`
- `cmd_mcp_status` → NEW: probes every MCP in registry, not project-scoped
- `cmd_mcp_auth` → PLACEHOLDER: prints "crux mcp auth not yet implemented"

The file should import from the same modules as the old `registry.py`: `crux_cli.manifest`, `crux_cli.registry`, `crux_cli.validation`, `crux_cli.paths`, `crux_cli.health`.

- [ ] **Step 4: Verify syntax**

Run: `python -c "import ast; ast.parse(open('src/crux_cli/cli/commands/mcp.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/crux_cli/cli/commands/mcp.py
git commit -m "refactor: create commands/mcp.py with MCP-specific handlers"
```

---

## Task 3: Create `commands/skill.py`

**Files:**
- Create: `src/crux_cli/cli/commands/skill.py`

- [ ] **Step 1: Read `commands/registry.py` skill branches**

Note the `elif entry_type == "skill"` branch in `cmd_add`, the skill handling in `cmd_remove`, and the skill table in `cmd_list`.

- [ ] **Step 2: Create `commands/skill.py`**

Extract skill-specific code:
- `cmd_skill_add` — skill registration from `cmd_add`'s skill branch (GitHub/local only, no --npx/--uvx/--keychain)
- `cmd_skill_remove` — only searches `skill_definitions`
- `cmd_skill_list` — only shows skills table

```python
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
        print(f"\u274c Invalid name '{name}': {reason}")
        sys.exit(1)

    registry_key = "skill_definitions"
    if reg[registry_key].get(name):
        print(f"\u274c Skill '{name}' already exists. Use 'crux skill remove {name}' first.")
        sys.exit(1)

    entry = {"tags": args.tags.split(",") if args.tags else []}

    if args.github:
        dest = v1_skills_dir() / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"  Cloning: {args.github} -> {dest}")
        subprocess.run(
            ["git", "clone", f"https://github.com/{args.github}", str(dest)],
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
        print("\u274c Specify a source: --github <user/repo> or --local <path>")
        sys.exit(1)

    reg[registry_key][name] = entry
    save_registry(reg)
    print(f"\u2705 Registered skill '{name}'")


def cmd_skill_remove(args: argparse.Namespace) -> None:
    """crux skill remove <name> — unregister a skill."""
    reg = load_registry()
    name = args.name
    section = "skill_definitions"

    if name not in reg.get(section, {}):
        print(f"\u274c Skill '{name}' not found in registry")
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
    print(f"\u2705 Removed skill '{name}' from registry")
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
```

- [ ] **Step 3: Verify syntax**

Run: `python -c "import ast; ast.parse(open('src/crux_cli/cli/commands/skill.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/crux_cli/cli/commands/skill.py
git commit -m "refactor: create commands/skill.py with skill-specific handlers"
```

---

## Task 4: Create `commands/task.py` (rename from `sandbox.py`)

**Files:**
- Create: `src/crux_cli/cli/commands/task.py`
- Delete: `src/crux_cli/cli/commands/sandbox.py`

- [ ] **Step 1: Read `commands/sandbox.py`**

Read the entire file. Note the dispatch logic in `cmd_run` that routes `init`/`list`/`clean`/task.

- [ ] **Step 2: Create `commands/task.py`**

Copy `sandbox.py` to `task.py`. The key change: `cmd_run` becomes `cmd_task` with simplified dispatch since argparse now handles subcommand routing via `task_command`.

```python
"""CLI commands: crux task run/init/list/clean."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from crux_cli.manifest import load_registry
from crux_cli.sandbox import (
    clean_runs,
    create_sandbox,
    generate_run_id,
    list_runs,
    load_run_manifest,
    run_agent,
    write_run_meta,
)


def cmd_task(args: argparse.Namespace) -> None:
    """Dispatch crux task subcommands."""
    sub = getattr(args, "task_command", None)

    if sub == "run":
        _cmd_task_run(args)
    elif sub == "init":
        _cmd_task_init(getattr(args, "name", None))
    elif sub == "list":
        _cmd_task_list()
    elif sub == "clean":
        _cmd_task_clean(force=getattr(args, "force", False))
    else:
        print("crux task: specify a subcommand (run/init/list/clean)")
        sys.exit(1)


def _cmd_task_run(args: argparse.Namespace) -> None:
    """Execute a task — from inline string or run.json manifest."""
    reg = load_registry()

    run_file = getattr(args, "file", None)
    task_str = getattr(args, "task", None)

    if run_file:
        run_manifest = load_run_manifest(run_file)
        task = run_manifest.get("task", "")
        mcps = run_manifest.get("mcps", [])
        name = run_manifest.get("name")
        timeout = run_manifest.get("timeout", 300)
    else:
        task = task_str
        mcps = getattr(args, "mcps", []) or []
        name = None
        timeout = None

    if not task:
        print("\u274c No task specified. Provide a task string or a run.json with a 'task' field.")
        sys.exit(1)

    run_id = generate_run_id()
    sandbox_path = create_sandbox(
        run_id,
        mcps,
        registry=reg,
        skip_preflight=False,
    )
    write_run_meta(sandbox_path, run_id, task, mcps, name=name)

    exit_code = run_agent(
        sandbox_path,
        task,
        timeout=timeout,
        run_id=run_id,
    )
    sys.exit(exit_code)


def _cmd_task_init(name: str | None = None) -> None:
    """Scaffold a run.json template in the current directory."""
    name = name or "my-run"
    output_path = Path.cwd() / "run.json"

    if output_path.exists():
        print(f"\u274c run.json already exists at {output_path}")
        sys.exit(1)

    reg = load_registry()
    available_mcps = sorted(reg.get("mcp_definitions", {}).keys())

    template = {
        "name": name,
        "task": "Describe your task here",
        "mcps": [],
        "skills": [],
        "workspace": "scratch",
        "output": "output.md",
        "timeout": 300,
    }
    output_path.write_text(json.dumps(template, indent=2) + "\n")

    print(f"\u2705 Created run.json for '{name}'")
    print("   Edit the 'task' field, then run: crux task run --file run.json")
    if available_mcps:
        print(f"   Available MCPs: {', '.join(available_mcps)}")


def _cmd_task_list() -> None:
    """Show all past/active runs from sandbox/."""
    from rich.console import Console
    from rich.table import Table

    runs = list_runs()
    console = Console()

    if not runs:
        console.print("[dim]No runs found in sandbox/[/dim]")
        return

    table = Table(title="crux task history", show_lines=False)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Status", no_wrap=True)
    table.add_column("MCPs", style="dim")
    table.add_column("Task", max_width=50, overflow="ellipsis")

    status_colors = {
        "done": "[green]done[/green]",
        "failed": "[red]failed[/red]",
        "running": "[yellow]running[/yellow]",
    }

    for run in runs:
        status = run.get("status", "?")
        status_str = status_colors.get(status, status)
        mcps_str = ", ".join(run.get("mcps", [])) or "\u2014"
        task = run.get("task", "")
        run_name = run.get("name", run.get("id", ""))
        table.add_row(run.get("id", ""), run_name, status_str, mcps_str, task)

    console.print(table)


def _cmd_task_clean(force: bool = False) -> None:
    """Remove completed sandboxes."""
    count = clean_runs(force=force)
    if count == 0:
        print("sandbox/ is already empty.")
    else:
        print(f"\u2705 Removed {count} sandbox(es)")
```

- [ ] **Step 3: Delete `commands/sandbox.py`**

```bash
git rm src/crux_cli/cli/commands/sandbox.py
```

- [ ] **Step 4: Verify syntax**

Run: `python -c "import ast; ast.parse(open('src/crux_cli/cli/commands/task.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/crux_cli/cli/commands/task.py
git commit -m "refactor: rename sandbox.py to task.py, update dispatch"
```

---

## Task 5: Update `commands/project.py`

**Files:**
- Modify: `src/crux_cli/cli/commands/project.py`

- [ ] **Step 1: Read current `project.py`**

Note: `cmd_init`, `cmd_sync`, `cmd_install`, `cmd_uninstall`, `cmd_status`.

- [ ] **Step 2: Rename functions and update**

Changes:
- `cmd_init` → `cmd_project_create` — add `--mcp` and `--skill` flag support. After creating `crux.json`, if `--mcp` or `--skill` provided, add them to the manifest and call `sync_project`.
- `cmd_sync` → `cmd_project_sync` — update help text: `'crux init'` → `'crux project create'`
- `cmd_install` → `cmd_project_install` — no logic changes
- `cmd_uninstall` → `cmd_project_uninstall` — no logic changes
- `cmd_status` → `cmd_project_status` — no logic changes (project-scoped status stays here)

In `cmd_project_create`, add after writing `crux.json`:
```python
mcps_arg = getattr(args, "mcps", None)
skills_arg = getattr(args, "skills", None)
if mcps_arg:
    crux_json["mcps"] = [m.strip() for m in mcps_arg.split(",")]
if skills_arg:
    crux_json["skills"] = [s.strip() for s in skills_arg.split(",")]
```

Update all user-facing strings:
- `'crux init'` → `'crux project create'`
- `'crux sync'` → `'crux project sync'`
- `'crux install'` → `'crux project install'`

- [ ] **Step 3: Verify syntax**

Run: `python -c "import ast; ast.parse(open('src/crux_cli/cli/commands/project.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/crux_cli/cli/commands/project.py
git commit -m "refactor: rename project.py functions, add --mcp/--skill to create"
```

---

## Task 6: Update `commands/doctor.py`

**Files:**
- Modify: `src/crux_cli/cli/commands/doctor.py`

- [ ] **Step 1: Read current `doctor.py`**

Note: `cmd_setup` has two branches — no-name (full setup) and name (run MCP's setup_cmd). `cmd_doctor` shows all checks including secrets.

- [ ] **Step 2: Rewrite**

Changes:
- `cmd_setup` (no-name branch) → rename to `cmd_init` — keep the same logic from `run_setup()`
- `cmd_setup` (name branch) → DELETE — absorbed by `crux mcp auth` (later plan)
- `cmd_doctor` → remove `secrets_idx` loading and the `secrets_index=secrets_idx` parameter from `run_doctor_checks` call

```python
"""CLI commands: init, doctor."""

from __future__ import annotations

import argparse

from crux_cli.health import run_doctor_checks
from crux_cli.manifest import load_registry
from crux_cli.paths import crux_home


def cmd_doctor(args: argparse.Namespace) -> None:
    """crux doctor — check the Crux environment."""
    print("\n\U0001fa7a CRUX DOCTOR \u2014 Environment Health Check\n")

    reg = load_registry()
    mcp_defs = reg.get("mcp_definitions", {})

    fh = crux_home()
    reg_path = fh / "registry.json"

    checks = run_doctor_checks(
        crux_root=fh,
        registry_path=reg_path if reg_path.exists() else None,
        mcp_definitions=mcp_defs,
    )

    all_ok = True
    print("  \U0001f4e6 Environment & Dependencies")
    for c in checks:
        if c.passed:
            print(f"  \u2705 {c.label}")
        elif c.warning:
            all_ok = False
            print(f"  \u26a0\ufe0f  {c.label}")
            if c.fix_hint:
                print(f"     Fix: {c.fix_hint}")
        else:
            all_ok = False
            print(f"  \u274c {c.label}")
            if c.fix_hint:
                print(f"     Fix: {c.fix_hint}")

    print()
    if all_ok:
        print("\u2705 All checks passed \u2014 Crux environment is healthy!\n")
    else:
        print("\u26a0\ufe0f  Some issues were found.\n")


def cmd_init(args: argparse.Namespace) -> None:
    """crux init — initialise ~/.crux/."""
    from crux_cli.setup_crux import run_setup

    print("\n  CRUX SETUP\n")
    result = run_setup()

    if result.dirs_created:
        print(f"  Created directories: {len(result.dirs_created)}")
        for d in result.dirs_created:
            print(f"    {d}")

    if result.config_written:
        print("  Wrote config.toml with platform defaults")
    else:
        print("  config.toml already exists \u2014 skipped")

    if result.skill_installed:
        print("  Installed Crux skill to ~/.claude/skills/crux/SKILL.md")
    else:
        print("  Crux skill not installed (bundled data missing)")

    if result.missing_deps:
        print(f"\n  Missing dependencies: {', '.join(result.missing_deps)}")
    else:
        print("  All dependencies found")

    mig = result.migration
    if mig and mig.detected:
        print("\n  Migration from old layout:")
        print(f"    Registry entries: {mig.registry_entries}")
        if mig.mcps_copied:
            print(f"    MCPs copied: {', '.join(mig.mcps_copied)}")
        if mig.skills_copied:
            print(f"    Skills copied: {', '.join(mig.skills_copied)}")
    elif mig and not mig.detected:
        print("  No old marketplace layout detected \u2014 nothing to migrate")

    print("\n  Setup complete.\n")
```

- [ ] **Step 3: Delete `commands/secrets.py`**

This file is now dead — `crux secret` no longer exists. Auth will be implemented in a later plan via `cmd_mcp_auth` in `mcp.py`.

```bash
git rm src/crux_cli/cli/commands/secrets.py
```

- [ ] **Step 4: Verify syntax**

Run: `python -c "import ast; ast.parse(open('src/crux_cli/cli/commands/doctor.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/crux_cli/cli/commands/doctor.py
git commit -m "refactor: cmd_setup -> cmd_init, remove MCP setup branch, remove secrets from doctor"
```

---

## Task 7: Update Core Modules (health.py, preflight.py, registry.py)

**Files:**
- Modify: `src/crux_cli/health.py`
- Modify: `src/crux_cli/preflight.py`
- Modify: `src/crux_cli/registry.py` (core module)

- [ ] **Step 1: Update `health.py`**

1. Remove `check_secrets_consistency` function (lines 261-289)
2. Remove `secrets_index` parameter from `run_doctor_checks` function signature and body (lines 298-330)
3. Update fix hint in `check_mcp_sources_present`: `f"Run: crux add {mcp_name}"` → `f"Run: crux mcp add {mcp_name}"`

- [ ] **Step 2: Update `preflight.py`**

Update fix hint strings:
- Line 66-67: `f"Fix: crux add mcp {name} --npx <package>"` → `f"Fix: crux mcp add {name} --npx <package>"`
- Line 102-103: `f"Fix: crux secret set {name} {var} <value>"` → `f"Fix: crux mcp auth {name}"`
- Line 138: `f"Fix: crux add skill {name} --github <repo>"` → `f"Fix: crux skill add {name} --github <repo>"`

- [ ] **Step 3: Update `registry.py` (core)**

Read the file, find `suggest_crux_add` function. Update the command strings it generates:
- `f"crux add mcp {safe_name} --npx {pkg}"` → `f"crux mcp add {safe_name} --npx {pkg}"`
- Same for `--github` variant

- [ ] **Step 4: Verify syntax for all three files**

```bash
python -c "import ast; [ast.parse(open(f).read()) for f in ['src/crux_cli/health.py', 'src/crux_cli/preflight.py', 'src/crux_cli/registry.py']]; print('OK')"
```

- [ ] **Step 5: Commit**

```bash
git add src/crux_cli/health.py src/crux_cli/preflight.py src/crux_cli/registry.py
git commit -m "refactor: update fix hints to new command names, remove secrets from doctor"
```

---

## Task 8: Delete Old `commands/registry.py`

**Files:**
- Delete: `src/crux_cli/cli/commands/registry.py`

This file is now fully replaced by `commands/mcp.py` + `commands/skill.py`.

- [ ] **Step 1: Verify no imports remain**

Search for `from crux_cli.cli.commands.registry import` in the codebase. Should only appear in old test files (which we'll replace) and `main.py` (already rewritten).

Run: `grep -r "commands.registry" src/`
Expected: no matches

- [ ] **Step 2: Delete**

```bash
git rm src/crux_cli/cli/commands/registry.py
```

- [ ] **Step 3: Smoke test — verify imports resolve**

```bash
python -c "from crux_cli.cli.main import main; print('imports OK')"
```

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor: delete commands/registry.py (replaced by mcp.py + skill.py)"
```

---

## Task 9: Update SKILL.md

**Files:**
- Modify: `src/crux_cli/data/skills/crux/SKILL.md`

- [ ] **Step 1: Rewrite SKILL.md**

Replace entire contents with:

```markdown
# Crux — Agentic Tool Manager for Claude Code

Crux is a CLI tool for managing MCP servers, skills, and agent tasks.

## Available Commands

### MCP Servers
- `crux mcp search <query>` — Search the MCP Registry
- `crux mcp add <name> --npx <pkg>` — Register an MCP server
- `crux mcp remove <name>` — Unregister an MCP server
- `crux mcp list` — List registered MCP servers
- `crux mcp upgrade` — Update cloned MCP repos
- `crux mcp auth <name>` — Authenticate an MCP server
- `crux mcp auth` — Show authentication status for all MCPs
- `crux mcp status` — Probe all registered MCP servers

### Skills
- `crux skill add <name> --github <repo>` — Register a skill
- `crux skill remove <name>` — Unregister a skill
- `crux skill list` — List registered skills

### Projects
- `crux project create [name]` — Create a new project with crux.json
- `crux project install <name>` — Add MCPs/skills to current project
- `crux project uninstall <name>` — Remove MCPs/skills from project
- `crux project sync` — Generate .mcp.json from crux.json
- `crux project status` — Show project health (MCPs, skills, auth)

### Tasks
- `crux task run <prompt>` — Execute a task in an isolated sandbox
- `crux task init` — Scaffold a run.json template
- `crux task list` — Show past/active runs
- `crux task clean` — Remove completed sandboxes

### System
- `crux init` — Initialize the crux environment
- `crux doctor` — Check crux environment health
- `crux version` — Show version and check for updates

## Usage Notes

- Run `crux init` first to set up the `~/.crux/` directory.
- Use `crux mcp search` to discover MCPs, then `crux mcp add` to register them.
- Use `crux mcp auth <name>` to authenticate any MCP that needs credentials.
- Use `crux project create` to start a project, then `crux project install` to add MCPs.
- Secrets are stored in the system keychain (macOS) or secret-service (Linux).
```

- [ ] **Step 2: Commit**

```bash
git add src/crux_cli/data/skills/crux/SKILL.md
git commit -m "docs: update SKILL.md with new command names"
```

---

## Task 10: Update Unit Tests

**Files:**
- Modify: `tests/unit/test_health.py`
- Modify: `tests/unit/test_preflight.py`
- Modify: `tests/unit/test_registry.py`

- [ ] **Step 1: Update `test_health.py`**

1. Remove all tests that reference `check_secrets_consistency` — search for function name and delete those test functions.
2. Update any test calling `run_doctor_checks` that passes `secrets_index=` — remove that parameter.

- [ ] **Step 2: Update `test_preflight.py`**

Update expected strings in assertions:
- `"crux secret set"` → `"crux mcp auth"`
- `"crux add mcp"` → `"crux mcp add"`
- `"crux add skill"` → `"crux skill add"`

- [ ] **Step 3: Update `test_registry.py`**

Update expected strings from `suggest_crux_add` tests:
- `"crux add mcp"` → `"crux mcp add"`

- [ ] **Step 4: Run unit tests**

```bash
pytest tests/unit/ -v --tb=short
```
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_health.py tests/unit/test_preflight.py tests/unit/test_registry.py
git commit -m "test: update unit tests for new command names"
```

---

## Task 11: Rewrite Integration Tests

**Files:**
- Delete: all old `tests/integration/test_cli_*.py` files
- Create: `tests/integration/test_cli_project_create.py`
- Create: `tests/integration/test_cli_mcp.py`
- Create: `tests/integration/test_cli_skill.py`
- Create: `tests/integration/test_cli_project_sync.py`
- Create: `tests/integration/test_cli_task.py`
- Modify: `tests/integration/test_cli_doctor.py`

- [ ] **Step 1: Delete old integration test files**

```bash
git rm tests/integration/test_cli_init.py
git rm tests/integration/test_cli_add_remove.py
git rm tests/integration/test_cli_list.py
git rm tests/integration/test_cli_secret.py
git rm tests/integration/test_cli_sync.py
git rm tests/integration/test_cli_run.py
```

- [ ] **Step 2: Create `test_cli_project_create.py`**

Port tests from old `test_cli_init.py`, changing `run_crux("init", ...)` to `run_crux("project", "create", ...)`:

```python
"""Integration tests: crux project create"""
import json

import pytest

from .conftest import run_crux


@pytest.mark.integration
class TestProjectCreate:
    def test_creates_project_directory(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "myproject", env=env, cwd=str(root))
        assert (root / "myproject").is_dir()

    def test_creates_crux_json(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "myproject", env=env, cwd=str(root))
        crux_json_path = root / "myproject" / "crux.json"
        assert crux_json_path.exists()
        data = json.loads(crux_json_path.read_text())
        assert data["name"] == "myproject"
        assert "mcps" in data
        assert "skills" in data

    def test_creates_gitignore(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "myproject", env=env, cwd=str(root))
        gitignore = root / "myproject" / ".gitignore"
        assert gitignore.exists()
        assert ".mcp.json" in gitignore.read_text()

    def test_exits_nonzero_if_project_exists(self, crux_env):
        env, root = crux_env
        project = root / "existing"
        project.mkdir(parents=True)
        (project / "crux.json").write_text('{"name": "existing"}')
        result = run_crux("project", "create", "existing", env=env, cwd=str(root))
        assert result.returncode != 0
        assert "already exists" in result.stdout

    def test_success_message_shown(self, crux_env):
        env, root = crux_env
        result = run_crux("project", "create", "myproject", env=env, cwd=str(root))
        assert result.returncode == 0
        assert "myproject" in result.stdout

    def test_create_current_dir(self, crux_env):
        env, root = crux_env
        project = root / "my-app"
        project.mkdir()
        result = run_crux("project", "create", env=env, cwd=str(project))
        assert result.returncode == 0
        assert (project / "crux.json").exists()

    def test_create_with_mcp_flag(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "flagtest", "--mcp", "test-mcp", env=env, cwd=str(root))
        crux_json_path = root / "flagtest" / "crux.json"
        data = json.loads(crux_json_path.read_text())
        assert "test-mcp" in data["mcps"]

    def test_create_registers_project(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "tracked", env=env, cwd=str(root))
        projects_file = root / "projects.json"
        assert projects_file.exists()
```

- [ ] **Step 3: Create `test_cli_mcp.py`**

Port MCP tests from old `test_cli_add_remove.py` and `test_cli_list.py`:

```python
"""Integration tests: crux mcp add/remove/list"""
import json

import pytest

from .conftest import run_crux


def _load_registry(root):
    reg_path = root / "registry.json"
    with open(reg_path) as f:
        return json.load(f)


@pytest.mark.integration
class TestMcpAdd:
    def test_add_npx_mcp(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "add", "new-mcp", "--npx", "@test/new-mcp", "--tags", "test", env=env)
        assert result.returncode == 0
        assert "Registered MCP" in result.stdout
        reg = _load_registry(root)
        assert "new-mcp" in reg["mcp_definitions"]

    def test_add_duplicate_fails(self, crux_env):
        env, root = crux_env
        run_crux("mcp", "add", "dup", "--npx", "@test/dup", env=env)
        result = run_crux("mcp", "add", "dup", "--npx", "@test/dup", env=env)
        assert result.returncode != 0
        assert "already exists" in result.stdout

    def test_add_no_source_fails(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "add", "nosrc", env=env)
        assert result.returncode != 0


@pytest.mark.integration
class TestMcpRemove:
    def test_remove_existing(self, crux_env):
        env, root = crux_env
        run_crux("mcp", "add", "to-remove", "--npx", "@test/pkg", env=env)
        result = run_crux("mcp", "remove", "to-remove", env=env)
        assert result.returncode == 0
        assert "Removed" in result.stdout
        reg = _load_registry(root)
        assert "to-remove" not in reg["mcp_definitions"]

    def test_remove_nonexistent_fails(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "remove", "nope", env=env)
        assert result.returncode != 0


@pytest.mark.integration
class TestMcpList:
    def test_list_shows_mcps(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "list", env=env)
        assert result.returncode == 0

    def test_list_json(self, crux_env):
        env, root = crux_env
        result = run_crux("mcp", "list", "--json", env=env)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "mcp_definitions" in data
```

- [ ] **Step 4: Create `test_cli_skill.py`**

```python
"""Integration tests: crux skill add/remove/list"""
import json

import pytest

from .conftest import run_crux


def _load_registry(root):
    reg_path = root / "registry.json"
    with open(reg_path) as f:
        return json.load(f)


@pytest.mark.integration
class TestSkillList:
    def test_list_returns_zero(self, crux_env):
        env, root = crux_env
        result = run_crux("skill", "list", env=env)
        assert result.returncode == 0

    def test_list_json(self, crux_env):
        env, root = crux_env
        result = run_crux("skill", "list", "--json", env=env)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "skill_definitions" in data


@pytest.mark.integration
class TestSkillRemove:
    def test_remove_nonexistent_fails(self, crux_env):
        env, root = crux_env
        result = run_crux("skill", "remove", "nope", env=env)
        assert result.returncode != 0
```

- [ ] **Step 5: Create `test_cli_project_sync.py`**

```python
"""Integration tests: crux project sync"""
import pytest

from .conftest import run_crux


@pytest.mark.integration
class TestProjectSync:
    def test_sync_no_crux_json_fails(self, crux_env):
        env, root = crux_env
        result = run_crux("project", "sync", env=env, cwd=str(root))
        assert result.returncode != 0

    def test_sync_after_create(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "synctest", env=env, cwd=str(root))
        result = run_crux("project", "sync", env=env, cwd=str(root / "synctest"))
        assert result.returncode == 0

    def test_sync_all(self, crux_env):
        env, root = crux_env
        run_crux("project", "create", "p1", env=env, cwd=str(root))
        result = run_crux("project", "sync", "--all", env=env, cwd=str(root))
        assert result.returncode == 0
```

- [ ] **Step 6: Create `test_cli_task.py`**

```python
"""Integration tests: crux task init/list/clean"""
import pytest

from .conftest import run_crux


@pytest.mark.integration
class TestTaskInit:
    def test_init_creates_run_json(self, crux_env):
        env, root = crux_env
        workdir = root / "tasktest"
        workdir.mkdir()
        result = run_crux("task", "init", "my-task", env=env, cwd=str(workdir))
        assert result.returncode == 0
        assert (workdir / "run.json").exists()

    def test_init_fails_if_exists(self, crux_env):
        env, root = crux_env
        workdir = root / "tasktest2"
        workdir.mkdir()
        (workdir / "run.json").write_text("{}")
        result = run_crux("task", "init", env=env, cwd=str(workdir))
        assert result.returncode != 0


@pytest.mark.integration
class TestTaskList:
    def test_list_empty(self, crux_env):
        env, root = crux_env
        result = run_crux("task", "list", env=env)
        assert result.returncode == 0


@pytest.mark.integration
class TestTaskClean:
    def test_clean_empty(self, crux_env):
        env, root = crux_env
        result = run_crux("task", "clean", "--force", env=env)
        assert result.returncode == 0
```

- [ ] **Step 7: Update `test_cli_doctor.py`**

Update to test `crux init` (was `crux setup`) and `crux doctor` without secrets checks:

```python
"""Integration tests: crux init, crux doctor"""
import pytest

from .conftest import run_crux


@pytest.mark.integration
class TestCruxInit:
    def test_init_runs(self, crux_env):
        env, root = crux_env
        result = run_crux("init", env=env)
        assert result.returncode == 0
        assert "Setup complete" in result.stdout


@pytest.mark.integration
class TestCruxDoctor:
    def test_doctor_runs(self, crux_env):
        env, root = crux_env
        result = run_crux("doctor", env=env)
        assert result.returncode == 0
        assert "CRUX DOCTOR" in result.stdout

    def test_doctor_does_not_check_secrets(self, crux_env):
        env, root = crux_env
        result = run_crux("doctor", env=env)
        assert "secret" not in result.stdout.lower()
        assert "crux secret" not in result.stdout
```

- [ ] **Step 8: Run all integration tests**

```bash
pytest tests/integration/ -v --tb=short
```
Expected: all pass

- [ ] **Step 9: Commit**

```bash
git add tests/integration/
git commit -m "test: rewrite integration tests for new CLI command structure"
```

---

## Task 12: Full Test Suite Run & Final Verification

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v --tb=short
```
Expected: all pass

- [ ] **Step 2: Verify CLI commands work end-to-end**

```bash
python -m crux_cli.cli.main mcp list
python -m crux_cli.cli.main skill list
python -m crux_cli.cli.main doctor
python -m crux_cli.cli.main version
python -m crux_cli.cli.main --help
python -m crux_cli.cli.main mcp --help
python -m crux_cli.cli.main project --help
python -m crux_cli.cli.main task --help
```

- [ ] **Step 3: Verify old commands no longer work**

```bash
python -m crux_cli.cli.main add mcp test --npx test 2>&1 | grep -q "invalid choice"
python -m crux_cli.cli.main secret set test KEY 2>&1 | grep -q "invalid choice"
python -m crux_cli.cli.main run list 2>&1 | grep -q "invalid choice"
python -m crux_cli.cli.main init 2>&1 | grep -q "Setup complete"  # crux init = env setup, not project create
```

- [ ] **Step 4: Lint**

```bash
ruff check src/crux_cli/ tests/
ruff format --check src/crux_cli/ tests/
```

- [ ] **Step 5: Commit any lint fixes**

```bash
ruff format src/crux_cli/ tests/
git add -A
git commit -m "style: fix lint issues from CLI restructuring"
```
