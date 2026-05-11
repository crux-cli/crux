"""``crux doctor`` — sanity-check the environment."""

from __future__ import annotations

import argparse
import shutil
import sys

from crux_cli import paths

_REQUIRED_TOOLS = ("git", "uv", "npm", "claude")


def cmd_doctor(_args: argparse.Namespace) -> None:
    issues = 0
    for d in (
        paths.crux_home(),
        paths.registry_root(),
        paths.mcps_root(),
        paths.skills_root(),
        paths.plugins_root(),
        paths.harnesses_root(),
    ):
        if not d.exists():
            print(f"missing: {d} — run `crux setup`")
            issues += 1
    for tool in _REQUIRED_TOOLS:
        if shutil.which(tool) is None:
            print(f"missing tool: {tool}")
            issues += 1
    if issues:
        sys.exit(4)
    print("doctor: ok")
