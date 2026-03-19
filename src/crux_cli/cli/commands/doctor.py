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
