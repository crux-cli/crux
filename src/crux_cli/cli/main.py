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
    p.add_argument("--value", action="append", metavar="KEY=VALUE", help="Set secret non-interactively (repeatable)")
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
