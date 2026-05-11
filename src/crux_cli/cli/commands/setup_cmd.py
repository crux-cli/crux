"""``crux setup`` — initialise ~/.crux/."""

from __future__ import annotations

import argparse

from crux_cli.setup import run_setup


def cmd_setup(_args: argparse.Namespace) -> None:
    res = run_setup()
    print(
        f"setup: dirs={len(res.dirs_created)} "
        f"skill={'ok' if res.skill_installed else 'skip'} "
        f"launchers={len(res.launchers_installed)} "
        f"config={'written' if res.config_written else 'kept'}"
    )
